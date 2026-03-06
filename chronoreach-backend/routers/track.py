"""
Synaptiq — Email Open Tracking
Serves a 1x1 transparent pixel and records email_opened events.
After 3+ opens for the same lead, triggers ClawBot WhatsApp alert.
"""
import os
import base64
from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database import get_db
from models import Event, Lead, CampaignLead, ClawbotPending
from engine.executor import event_bus

router = APIRouter(prefix="/api/track", tags=["tracking"])

# 1x1 transparent PNG (base64)
PIXEL = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAC0lEQVQI12NgAAIABQAB"
    "Nl7BcQAAAABJRU5ErkJggg=="
)

CLAWBOT_THRESHOLD = 2  # Alert after this many opens (lower for demo)


@router.get("/{campaign_id}/{lead_id}/open.png")
async def track_open(campaign_id: int, lead_id: int, db: AsyncSession = Depends(get_db)):
    """Record an email open event. Returns a 1x1 transparent pixel."""

    # Record the open event
    ev = Event(
        campaign_id=campaign_id, lead_id=lead_id,
        node_id="tracking_pixel", event_type="email_opened",
        payload={"source": "tracking_pixel"}
    )
    db.add(ev)
    await db.commit()
    await db.refresh(ev)

    # Publish to SSE bus
    lead = await db.get(Lead, lead_id)
    lead_name = f"{lead.first_name} {lead.last_name}" if lead else f"Lead #{lead_id}"
    company = lead.company if lead else ""

    event_bus.publish({
        "id": ev.id, "campaign_id": campaign_id, "lead_id": lead_id,
        "node_id": "tracking_pixel", "event_type": "email_opened",
        "payload": {"lead_name": lead_name, "company": company, "source": "tracking_pixel"},
        "created_at": ev.created_at.isoformat()
    })

    # Count total opens for this lead in this campaign
    open_count = await db.scalar(
        select(func.count(Event.id)).where(
            Event.campaign_id == campaign_id,
            Event.lead_id == lead_id,
            Event.event_type == "email_opened"
        )
    )

    print(f"[Track] 👁 Email opened by {lead_name} ({company}) — open #{open_count}")

    # WhatsApp notification on first open only
    if open_count == 1:
        from services.clawbot_service import send_whatsapp
        user_phone = os.getenv("USER_PHONE", "").replace("whatsapp:", "")
        if user_phone:
            msg = f"👁 {lead_name} ({company}) just opened your email!"
            success = send_whatsapp(user_phone, msg)
            print(f"[Track] 📱 Open alert {'✅ sent' if success else '❌ failed'} for {lead_name}")

    # Trigger ClawBot after threshold opens (hot lead detection)
    if open_count >= CLAWBOT_THRESHOLD:
        # Check if we already sent an alert for this lead
        existing = await db.scalar(
            select(func.count(ClawbotPending.id)).where(
                ClawbotPending.campaign_id == campaign_id,
                ClawbotPending.lead_id == lead_id,
                ClawbotPending.action_type == "high_intent"
            )
        )
        if existing == 0:
            await _trigger_clawbot_alert(campaign_id, lead_id, lead, open_count, db)

    return Response(content=PIXEL, media_type="image/png",
                    headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


async def _trigger_clawbot_alert(campaign_id: int, lead_id: int, lead, opens: int, db: AsyncSession):
    """Send a WhatsApp alert for a hot lead."""
    from services.clawbot_service import send_whatsapp, build_hot_lead_alert
    from services.llm_service import llm_service

    lead_dict = {
        "first_name": lead.first_name, "last_name": lead.last_name,
        "title": lead.title, "company": lead.company
    }

    # Generate a follow-up draft
    draft = f"Hi {lead.first_name}, noticed you've been thinking about our intro — would love to continue the conversation. Worth a quick 15-min chat this week?"

    try:
        msg = await llm_service.generate_message(lead_dict, 2, {"tone": "casual"})
        draft = msg.get("body", draft)
    except Exception:
        pass

    # Save to ClawbotPending
    cp = ClawbotPending(
        campaign_id=campaign_id, lead_id=lead_id,
        action_type="high_intent", draft_message=draft,
        user_phone=os.getenv("USER_PHONE", ""), status="pending"
    )
    db.add(cp)
    await db.commit()

    # Send WhatsApp
    alert_msg = build_hot_lead_alert(lead_dict, draft, opens)
    user_phone = os.getenv("USER_PHONE", "").replace("whatsapp:", "")
    if user_phone:
        success = send_whatsapp(user_phone, alert_msg)
        print(f"[ClawBot] 🦅 Hot lead alert {'✅ sent' if success else '❌ failed'} for {lead.first_name}")

    # Log event
    ev = Event(
        campaign_id=campaign_id, lead_id=lead_id,
        node_id="clawbot", event_type="clawbot_triggered",
        payload={"lead_name": f"{lead.first_name} {lead.last_name}", "opens": opens, "whatsapp_sent": True}
    )
    db.add(ev)
    await db.commit()
    await db.refresh(ev)

    event_bus.publish({
        "id": ev.id, "campaign_id": campaign_id, "lead_id": lead_id,
        "node_id": "clawbot", "event_type": "clawbot_triggered",
        "payload": {"lead_name": f"{lead.first_name} {lead.last_name}", "opens": opens},
        "created_at": ev.created_at.isoformat()
    })
