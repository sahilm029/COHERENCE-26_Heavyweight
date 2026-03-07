"""
Synaptiq — Cal.com Integration
Handles booking notifications from Cal.com.
Two methods:
1. Webhook (if Cal.com can reach us) — POST /api/cal/webhook
2. Email polling (via inbox monitor) — detects Cal.com confirmation emails
"""
import os
from fastapi import APIRouter, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models import Lead, Event, CampaignLead
from engine.executor import event_bus
from services.clawbot_service import send_whatsapp

router = APIRouter(prefix="/api/cal", tags=["cal"])

USER_PHONE = os.getenv("USER_PHONE", "").replace("whatsapp:", "")
CAL_URL = os.getenv("CAL_URL", "app.cal.com/synaptiq")


@router.post("/webhook")
async def cal_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Cal.com calls this when a booking is created/cancelled.
    Payload shape: { triggerEvent: "BOOKING_CREATED", payload: { attendees: [...], ... } }
    """
    try:
        payload = await request.json()
    except Exception:
        return {"status": "invalid_json"}

    trigger = payload.get("triggerEvent", "")
    booking = payload.get("payload", {})
    attendees = booking.get("attendees", [])
    title = booking.get("title", "Meeting")
    start_time = booking.get("startTime", "")

    # Format ISO timestamp into readable form for WhatsApp
    if start_time:
        try:
            from datetime import datetime as dt
            parsed = dt.fromisoformat(start_time.replace("Z", "+00:00"))
            start_time = parsed.strftime("%A, %B %d, %Y at %I:%M %p")
        except Exception:
            pass  # keep raw value if parsing fails

    print(f"[Cal] 📅 Webhook received: {trigger} — {title}")

    if trigger != "BOOKING_CREATED":
        return {"status": "ignored", "trigger": trigger}

    for attendee in attendees:
        email = attendee.get("email", "").lower()
        name = attendee.get("name", "")

        if not email:
            continue

        # Find matching lead by email
        lead = await _find_lead_by_email(email, db)
        if lead:
            lead_name = f"{lead.first_name} {lead.last_name}".strip()
            await _record_meeting_booked(lead, start_time, db)
            # WhatsApp notification
            if USER_PHONE:
                msg = f"🎉 Meeting Booked!\n─────────────────\n{lead_name} ({lead.company}) just booked a call!\n📅 {start_time}\n\nCheck your calendar for the invite."
                send_whatsapp(USER_PHONE, msg)
                print(f"[Cal] 📱 WhatsApp alert sent for {lead_name}")
        else:
            print(f"[Cal] ⚠️ No matching lead for {email}")

    return {"status": "ok"}


async def process_cal_booking_email(subject: str, body: str, db: AsyncSession):
    """
    Called from inbox_monitor when a Cal.com confirmation email is detected.
    Parses attendee email from the confirmation and logs the event.
    """
    import re

    print(f"[Cal] 📧 Processing booking email: {subject}")

    # Extract attendee email from Cal.com confirmation body
    # Cal.com emails contain patterns like "Priya Sharma (igotthis123421@gmail.com)"
    email_matches = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', body)

    for email in email_matches:
        email = email.lower()
        # Skip our own email
        if email in ["synaptiqmail@gmail.com", "noreply@cal.com", "notifications@cal.com"]:
            continue

        lead = await _find_lead_by_email(email, db)
        if lead:
            lead_name = f"{lead.first_name} {lead.last_name}".strip()

            # Check if we already processed this CONFIRMED booking (not just link-sent)
            existing = await db.scalar(
                select(Event.id).where(
                    Event.lead_id == lead.id,
                    Event.event_type == "meeting_confirmed"
                ).limit(1)
            )
            if existing:
                print(f"[Cal] ⏭️ Meeting confirmation already processed for {lead_name}")
                continue

            # Extract date/time from Cal.com email body
            # Cal.com uses various formats — try multiple patterns
            start_time = _extract_datetime_from_email(body)

            await _record_meeting_booked(lead, start_time, db)

            # WhatsApp notification with full details
            if USER_PHONE:
                msg = f"🎉 Meeting Booked!\n─────────────────\n📌 {lead_name} ({lead.company}) just booked a call!\n📅 {start_time}\n\n🔗 Check your Google Calendar for the invite."
                send_whatsapp(USER_PHONE, msg)
                print(f"[Cal] 📱 WhatsApp alert sent for {lead_name}: {start_time}")
            return True

    return False


def _extract_datetime_from_email(body: str) -> str:
    """
    Extract meeting date/time from Cal.com confirmation email body.
    Tries multiple regex patterns for different Cal.com email formats.
    """
    import re
    from datetime import datetime as dt

    # Pattern 1: ISO 8601 datetime (e.g., "2026-03-11T10:00:00+05:30" or "2026-03-11T10:00:00Z")
    iso_match = re.search(
        r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:[+-]\d{2}:\d{2}|Z)?)',
        body
    )
    if iso_match:
        try:
            raw = iso_match.group(1)
            parsed = dt.fromisoformat(raw.replace("Z", "+00:00"))
            return parsed.strftime("%A, %B %d, %Y at %I:%M %p")
        except Exception:
            pass

    # Pattern 2: "When: <date and time>" or "Date: <date>" / "Time: <time>" labels
    when_line = re.search(
        r'(?:When|Date & Time|Date and Time|Scheduled)\s*[:\-]\s*(.+)',
        body, re.IGNORECASE
    )
    if when_line:
        return when_line.group(1).strip()[:80]

    # Pattern 3: "Wednesday, March 11, 2026 | 10:00am - 10:15am" (pipe separator)
    pipe_match = re.search(
        r'(\w+day,?\s+\w+\s+\d{1,2},?\s+\d{4})\s*\|?\s*(\d{1,2}:\d{2}\s*[aApP][mM]\s*[-–]\s*\d{1,2}:\d{2}\s*[aApP][mM])',
        body
    )
    if pipe_match:
        return f"{pipe_match.group(1)} at {pipe_match.group(2).strip()}"

    # Pattern 4: "March 11, 2026 10:00 AM - 10:15 AM" or "11 March 2026 10:00 AM"
    datetime_match = re.search(
        r'(\w+\s+\d{1,2},?\s+\d{4})\s+(\d{1,2}:\d{2}\s*[aApP][mM](?:\s*[-–]\s*\d{1,2}:\d{2}\s*[aApP][mM])?)',
        body
    )
    if datetime_match:
        return f"{datetime_match.group(1)} at {datetime_match.group(2).strip()}"

    # Pattern 5: Separate date and time anywhere in body
    date_match = re.search(r'(\w+day,?\s+\w+\s+\d{1,2},?\s+\d{4})', body)
    time_match = re.search(r'(\d{1,2}:\d{2}\s*[aApP][mM])', body)
    if date_match and time_match:
        return f"{date_match.group(1)} at {time_match.group(1)}"
    if date_match:
        return date_match.group(1)

    # Pattern 6: Just an ISO date  "2026-03-11"
    iso_date = re.search(r'(\d{4}-\d{2}-\d{2})', body)
    if iso_date:
        try:
            parsed = dt.strptime(iso_date.group(1), "%Y-%m-%d")
            return parsed.strftime("%A, %B %d, %Y")
        except Exception:
            return iso_date.group(1)

    # Nothing matched — log the raw body for debugging
    print(f"[Cal] ⚠️ Could not extract date/time from email body (first 500 chars): {body[:500]}")
    return "Check your calendar"


async def _find_lead_by_email(email: str, db: AsyncSession):
    """Find a lead by email."""
    result = await db.execute(select(Lead).where(Lead.email == email).limit(1))
    return result.scalar_one_or_none()


async def _record_meeting_booked(lead: Lead, start_time: str, db: AsyncSession):
    """Log meeting_booked event."""
    lead_name = f"{lead.first_name} {lead.last_name}".strip()

    # Find campaign for this lead
    cl = await db.scalar(
        select(CampaignLead.campaign_id).where(CampaignLead.lead_id == lead.id).limit(1)
    )
    campaign_id = cl or 1

    ev = Event(
        campaign_id=campaign_id, lead_id=lead.id, node_id="cal",
        event_type="meeting_confirmed",
        payload={
            "lead_name": lead_name,
            "company": lead.company,
            "start_time": start_time,
            "cal_url": CAL_URL,
            "via": "cal.com"
        }
    )
    db.add(ev)
    await db.commit()
    await db.refresh(ev)

    event_bus.publish({
        "id": ev.id, "campaign_id": campaign_id, "lead_id": lead.id,
        "node_id": "cal", "event_type": "meeting_confirmed",
        "payload": ev.payload, "created_at": ev.created_at.isoformat()
    })
    print(f"[Cal] ✅ Meeting CONFIRMED event logged for {lead_name}")
