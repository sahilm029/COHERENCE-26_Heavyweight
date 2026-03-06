# services/whatsapp_poller.py
"""
Synaptiq — WhatsApp Reply Poller
Polls Twilio Messages API for incoming WhatsApp replies.
Replaces unreliable webhook approach (localtunnel blocks Twilio POSTs).
Runs as a background task alongside the inbox monitor.
"""

import os
import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Load .env from project root
_env_file = Path(__file__).resolve().parent.parent.parent / ".env"
from dotenv import load_dotenv
load_dotenv(_env_file, override=True)

from sqlalchemy import select
from database import AsyncSessionLocal
from models import ClawbotPending, Lead, Event
from engine.email_sender import email_sender
from engine.executor import event_bus
from services.clawbot_service import send_whatsapp

TWILIO_SID = os.getenv("TWILIO_SID", "")
TWILIO_AUTH = os.getenv("TWILIO_AUTH", "")
TWILIO_WHATSAPP_FROM = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")
USER_PHONE = os.getenv("USER_PHONE", "")
CAL_URL = os.getenv("CAL_URL", "app.cal.com/synaptiq")
POLL_INTERVAL = 15  # seconds

# Track last processed message SID to avoid re-processing
_last_processed_sid = None
_processed_sids: set[str] = set()


def _fetch_recent_incoming() -> list[dict]:
    """Fetch recent incoming WhatsApp messages from Twilio API."""
    if not TWILIO_SID or not TWILIO_AUTH:
        return []
    
    try:
        from twilio.rest import Client
        client = Client(TWILIO_SID, TWILIO_AUTH)
        
        # Fetch messages from the last 2 minutes, incoming only
        since = datetime.now(timezone.utc) - timedelta(minutes=2)
        messages = client.messages.list(
            to=TWILIO_WHATSAPP_FROM,  # incoming = messages TO our sandbox number
            date_sent_after=since,
            limit=10,
        )
        
        results = []
        for msg in messages:
            if msg.sid in _processed_sids:
                continue
            if msg.direction in ("inbound",):
                results.append({
                    "sid": msg.sid,
                    "body": msg.body or "",
                    "from": msg.from_ or "",
                    "date": msg.date_sent,
                })
        return results
    except Exception as e:
        print(f"[WhatsAppPoller] ❌ Twilio fetch error: {e}")
        return []


async def _process_reply(body: str, from_phone: str):
    """Process a WhatsApp reply — mirrors the webhook handler logic."""
    reply = body.strip().upper()
    phone = from_phone.replace("whatsapp:", "")
    print(f"[WhatsAppPoller] 📱 Processing reply: '{body}' from {from_phone}")

    async with AsyncSessionLocal() as db:
        # Find latest pending action
        stmt = (
            select(ClawbotPending)
            .where(ClawbotPending.status == "pending")
            .order_by(ClawbotPending.created_at.desc())
            .limit(1)
        )
        result = await db.execute(stmt)
        pending = result.scalar_one_or_none()

        if not pending:
            send_whatsapp(phone, "🦅 No pending actions right now. Campaign is running smoothly!")
            return

        lead = await db.get(Lead, pending.lead_id)
        lead_name = f"{lead.first_name} {lead.last_name}" if lead else "Lead"

        if reply in ("YES", "✅", "Y"):
            await _handle_yes(pending, lead, phone, db)
        elif reply in ("SKIP", "⏭️", "⏭"):
            pending.status = "skipped"
            await db.commit()
            send_whatsapp(phone, f"⏭️ Skipped action for {lead_name}.")
            await _log_event(pending.campaign_id, pending.lead_id, "clawbot_skipped",
                            {"lead_name": lead_name}, db)
        elif reply in ("PAUSE", "🛑", "STOP"):
            pending.status = "paused"
            await db.commit()
            send_whatsapp(phone, f"🛑 Campaign paused. Reply RESUME to continue.")
            await _log_event(pending.campaign_id, pending.lead_id, "campaign_paused",
                            {"lead_name": lead_name}, db)
        else:
            # Custom reply — use user's text as the email body
            if lead and lead.email:
                subject = f"Re: Following up"
                success = await email_sender.send(lead.email, subject, body.strip())
                pending.status = "completed"
                await db.commit()
                if success:
                    send_whatsapp(phone, f"✅ Your custom reply sent to {lead_name} ({lead.email})!")
                    await _log_event(pending.campaign_id, pending.lead_id, "custom_reply_sent",
                                    {"lead_name": lead_name, "body_preview": body[:50]}, db)


async def _handle_yes(pending: ClawbotPending, lead: Lead, phone: str, db):
    """Handle YES reply based on action type."""
    lead_name = f"{lead.first_name} {lead.last_name}" if lead else "Lead"

    if pending.action_type == "high_intent":
        if lead and lead.email and pending.draft_message:
            subject = f"Following up — {lead.company or 'your team'}"
            success = await email_sender.send(lead.email, subject, pending.draft_message)
            pending.status = "completed"
            await db.commit()
            if success:
                send_whatsapp(phone, f"✅ Follow-up sent to {lead.first_name} ({lead.email})!\nDashboard updated live.")
                await _log_event(pending.campaign_id, pending.lead_id, "followup_sent",
                                {"lead_name": lead_name, "subject": subject, "via": "whatsapp_approval"}, db)
            else:
                send_whatsapp(phone, f"❌ Failed to send to {lead.email}. Check SMTP config.")

    elif pending.action_type == "objection":
        if lead and lead.email and pending.draft_message:
            subject = f"Re: {lead.company or 'our conversation'}"
            success = await email_sender.send(lead.email, subject, pending.draft_message)
            pending.status = "completed"
            await db.commit()
            if success:
                send_whatsapp(phone, f"✅ Objection response sent to {lead.first_name}!\n🧠 AI handled it gracefully.")
                await _log_event(pending.campaign_id, pending.lead_id, "objection_response_sent",
                                {"lead_name": lead_name, "via": "whatsapp_approval"}, db)

    elif pending.action_type == "meeting":
        if lead and lead.email:
            body = f"Hi {lead.first_name},\n\nGreat to hear you're interested! Here's my calendar link to book a time that works:\n\nhttps://{CAL_URL}\n\nLooking forward to connecting!\n\nBest"
            subject = f"Let's connect — booking link inside"
            success = await email_sender.send(lead.email, subject, body)
            pending.status = "completed"
            await db.commit()
            if success:
                send_whatsapp(phone, f"📅 Booking link sent to {lead.first_name} ({lead.email})!\nWaiting for them to pick a slot.")
                await _log_event(pending.campaign_id, pending.lead_id, "meeting_booked",
                                {"lead_name": lead_name, "cal_url": CAL_URL, "via": "whatsapp_approval"}, db)


async def _log_event(campaign_id: int, lead_id: int, event_type: str, payload: dict, db):
    """Log event and publish to SSE bus."""
    ev = Event(campaign_id=campaign_id, lead_id=lead_id, node_id="clawbot",
               event_type=event_type, payload=payload)
    db.add(ev)
    await db.commit()
    await db.refresh(ev)
    event_bus.publish({
        "id": ev.id, "campaign_id": campaign_id, "lead_id": lead_id,
        "node_id": "clawbot", "event_type": event_type,
        "payload": payload, "created_at": ev.created_at.isoformat()
    })


async def whatsapp_poller_loop():
    """Main background loop — polls Twilio for incoming WhatsApp messages."""
    print(f"[WhatsAppPoller] 🚀 Started — polling every {POLL_INTERVAL}s | Phone: {USER_PHONE}")
    
    await asyncio.sleep(8)  # Wait for app to initialize

    while True:
        try:
            messages = await asyncio.to_thread(_fetch_recent_incoming)
            
            for msg in messages:
                sid = msg["sid"]
                if sid in _processed_sids:
                    continue
                _processed_sids.add(sid)
                
                print(f"[WhatsAppPoller] 📬 New message: '{msg['body']}' from {msg['from']}")
                await _process_reply(msg["body"], msg["from"])
            
            # Keep processed set small — remove old entries
            if len(_processed_sids) > 100:
                _processed_sids.clear()

        except Exception as e:
            print(f"[WhatsAppPoller] ❌ Loop error: {e}")

        await asyncio.sleep(POLL_INTERVAL)
