# services/inbox_monitor.py
"""
Synaptiq — Gmail IMAP Inbox Monitor
Background task that polls Gmail for replies to Synaptiq-sent emails.
When a reply is detected, it:
  1. Matches the sender to a lead in the DB
  2. Classifies intent (positive = wants meeting, objection = pushback)
  3. Triggers ClawBot WhatsApp alert
  4. Records events + publishes to SSE bus
"""

import os
import re
import email
import imaplib
import asyncio
from pathlib import Path
from datetime import datetime
from email.header import decode_header

# Load .env from project root
_env_file = Path(__file__).resolve().parent.parent.parent / ".env"
from dotenv import load_dotenv
load_dotenv(_env_file, override=True)
from sqlalchemy import select, func
from database import AsyncSessionLocal
from models import Lead, Event, ClawbotPending
from engine.executor import event_bus
from services.clawbot_service import send_whatsapp, build_objection_alert

# Config from env
IMAP_HOST = os.getenv("IMAP_HOST", "imap.gmail.com")
IMAP_PORT = int(os.getenv("IMAP_PORT", "993"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
USER_PHONE = os.getenv("USER_PHONE", "").replace("whatsapp:", "")
CAL_URL = os.getenv("CAL_URL", "cal.com/ravi/intro")
POLL_INTERVAL = int(os.getenv("INBOX_POLL_INTERVAL", "30"))  # seconds

# Keywords for intent classification
POSITIVE_KEYWORDS = [
    "yes", "sure", "let's", "lets", "schedule", "meeting", "call",
    "interested", "book", "connect", "chat", "open to", "sounds good",
    "love to", "would be great", "absolutely", "definitely", "keen",
    "looking forward", "count me in", "sign me up", "let's do it",
]
OBJECTION_KEYWORDS = [
    "not interested", "no thanks", "busy", "later", "next quarter",
    "already have", "locked in", "unsubscribe", "stop", "remove",
    "not right now", "not the right time", "pass", "decline",
    "sorry", "don't require", "don't need", "not need", "no need",
    "not at this time", "not for us", "we're good", "we are good",
    "take me off", "opt out", "not looking", "not relevant",
]


def _strip_quoted_reply(body: str) -> str:
    """Strip quoted original email from reply body so it doesn't pollute intent classification."""
    lines = body.split("\n")
    clean_lines = []
    for line in lines:
        stripped = line.strip()
        # Stop at quoted text markers
        if stripped.startswith(">"):
            break
        if re.match(r"^On .+ wrote:$", stripped):
            break
        if re.match(r"^-{3,}.*Original Message.*-{3,}$", stripped, re.IGNORECASE):
            break
        if re.match(r"^From:", stripped) and len(clean_lines) > 0:
            break
        clean_lines.append(line)
    return "\n".join(clean_lines).strip()


def _decode_header_value(raw: str) -> str:
    """Decode email header value."""
    parts = decode_header(raw)
    decoded = []
    for part, encoding in parts:
        if isinstance(part, bytes):
            decoded.append(part.decode(encoding or "utf-8", errors="replace"))
        else:
            decoded.append(part)
    return " ".join(decoded)


def _extract_email_address(from_header: str) -> str:
    """Extract email address from 'Name <email>' format."""
    match = re.search(r'<([^>]+)>', from_header)
    return match.group(1).lower() if match else from_header.strip().lower()


def _get_body(msg: email.message.Message) -> str:
    """Extract plain text body from email message."""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                payload = part.get_payload(decode=True)
                if payload:
                    return payload.decode("utf-8", errors="replace")
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            return payload.decode("utf-8", errors="replace")
    return ""


def _classify_intent(body: str) -> tuple[str, float]:
    """Classify reply intent: 'positive' or 'objection'. Strips quoted text first."""
    # Strip quoted original email so our own template words don't inflate positive score
    clean_body = _strip_quoted_reply(body)
    lower = clean_body.lower()

    print(f"[InboxMonitor] 🧠 Classifying: \"{lower[:80]}...\"")

    pos_score = sum(1 for kw in POSITIVE_KEYWORDS if kw in lower)
    neg_score = sum(1 for kw in OBJECTION_KEYWORDS if kw in lower)

    print(f"[InboxMonitor] 🧠 Scores: positive={pos_score}, objection={neg_score}")

    if pos_score > neg_score:
        confidence = min(0.99, 0.7 + pos_score * 0.08)
        return "positive", confidence
    elif neg_score > 0:
        confidence = min(0.99, 0.7 + neg_score * 0.08)
        return "objection", confidence
    else:
        # Default to OBJECTION if no clear signals — safer to ask before acting
        return "objection", 0.60


async def _process_reply(sender_email: str, subject: str, body: str, campaign_id: int = 1):
    """Process a detected email reply: match to lead, classify, trigger ClawBot."""
    async with AsyncSessionLocal() as db:
        # Find the lead by email
        stmt = select(Lead).where(Lead.email == sender_email)
        result = await db.execute(stmt)
        lead = result.scalar_one_or_none()

        if not lead:
            print(f"[InboxMonitor] ⚠️ Reply from {sender_email} — no matching lead found")
            return

        lead_name = f"{lead.first_name} {lead.last_name}"
        print(f"[InboxMonitor] 📬 Reply detected from {lead_name} ({sender_email})")

        # Classify intent
        intent, confidence = _classify_intent(body)
        body_preview = body.strip()[:200]

        # Record reply event
        ev = Event(
            campaign_id=campaign_id, lead_id=lead.id,
            node_id="inbox_monitor", event_type="reply_received",
            payload={
                "lead_name": lead_name, "company": lead.company,
                "reply_text": body_preview, "intent": intent,
                "confidence": confidence, "source": "imap_monitor"
            }
        )
        db.add(ev)
        await db.commit()
        await db.refresh(ev)

        # Publish to SSE bus (live monitoring feed)
        event_bus.publish({
            "id": ev.id, "campaign_id": campaign_id, "lead_id": lead.id,
            "node_id": "inbox_monitor", "event_type": "reply_received",
            "payload": ev.payload, "created_at": ev.created_at.isoformat()
        })

        lead_dict = {
            "first_name": lead.first_name, "last_name": lead.last_name,
            "title": lead.title, "company": lead.company
        }

        if intent == "positive":
            # Positive reply → meeting booking flow
            draft = f"Send your booking link?\n{CAL_URL}"
            alert = f"""🦅 Positive Intent — {lead_name}
─────────────────────────────────────
💬 "{body_preview[:100]}"

Send your booking link?
{CAL_URL}

Reply: ✅ YES  📅 SLOTS  ✏️ CUSTOM"""

            cp = ClawbotPending(
                campaign_id=campaign_id, lead_id=lead.id,
                action_type="meeting", draft_message=draft,
                user_phone=os.getenv("USER_PHONE", ""), status="pending"
            )
            db.add(cp)
            await db.commit()

        else:
            # Objection → generate response draft
            try:
                from services.llm_service import llm_service
                classification = await llm_service.classify_objection(body_preview)
                obj_type = classification.get("type", "timing")
                draft = await llm_service.generate_objection_response(lead_dict, obj_type, body_preview)
            except Exception:
                obj_type = "timing"
                draft = f"That's totally fair {lead.first_name} — timing is everything. I'll check back next quarter. One quick thought in the meantime?"

            label = f"⏰ {obj_type.upper()} ({int(confidence * 100)}% confidence)"
            alert = build_objection_alert(lead_dict, body_preview, label, draft)

            cp = ClawbotPending(
                campaign_id=campaign_id, lead_id=lead.id,
                action_type="objection", draft_message=draft,
                user_phone=os.getenv("USER_PHONE", ""), status="pending"
            )
            db.add(cp)
            await db.commit()

        # Send WhatsApp alert
        if USER_PHONE:
            success = send_whatsapp(USER_PHONE, alert)
            print(f"[InboxMonitor] 🦅 ClawBot alert {'✅ sent' if success else '❌ failed'} — {intent} intent from {lead_name}")

        # Log ClawBot event
        clawbot_ev = Event(
            campaign_id=campaign_id, lead_id=lead.id,
            node_id="clawbot", event_type=f"{'positive_intent' if intent == 'positive' else 'objection_detected'}",
            payload={
                "lead_name": lead_name, "intent": intent,
                "confidence": confidence, "reply_preview": body_preview[:80],
                "source": "imap_monitor"
            }
        )
        db.add(clawbot_ev)
        await db.commit()
        await db.refresh(clawbot_ev)

        event_bus.publish({
            "id": clawbot_ev.id, "campaign_id": campaign_id, "lead_id": lead.id,
            "node_id": "clawbot",
            "event_type": f"{'positive_intent' if intent == 'positive' else 'objection_detected'}",
            "payload": clawbot_ev.payload, "created_at": clawbot_ev.created_at.isoformat()
        })


def _poll_gmail_once() -> list[dict]:
    """Connect to Gmail IMAP and fetch unread replies. Returns list of {sender, subject, body}."""
    if not SMTP_USER or not SMTP_PASS:
        return []

    replies = []
    mail = None
    try:
        mail = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
        mail.login(SMTP_USER, SMTP_PASS)
        mail.select("INBOX")

        # Search for unread emails (replies to our sent messages)
        status, data = mail.search(None, "UNSEEN")
        if status != "OK" or not data[0]:
            return []

        email_ids = data[0].split()
        print(f"[InboxMonitor] 📥 Found {len(email_ids)} unread emails")

        for eid in email_ids:
            status, msg_data = mail.fetch(eid, "(RFC822)")
            if status != "OK":
                continue

            msg = email.message_from_bytes(msg_data[0][1])
            from_header = _decode_header_value(msg.get("From", ""))
            sender = _extract_email_address(from_header)
            subject = _decode_header_value(msg.get("Subject", ""))
            body = _get_body(msg)

            # Skip emails from ourselves
            if SMTP_USER.lower() in sender:
                continue

            replies.append({
                "sender": sender,
                "subject": subject,
                "body": body,
            })

            # Mark as read
            mail.store(eid, "+FLAGS", "\\Seen")

    except Exception as e:
        print(f"[InboxMonitor] ❌ IMAP error: {e}")
    finally:
        if mail:
            try:
                mail.logout()
            except Exception:
                pass

    return replies


async def inbox_monitor_loop():
    """Main background loop — polls Gmail every POLL_INTERVAL seconds."""
    print(f"[InboxMonitor] 🚀 Started — polling every {POLL_INTERVAL}s | User: {SMTP_USER}")

    # Wait a few seconds for the app to initialize
    await asyncio.sleep(5)

    while True:
        try:
            # Run IMAP polling in a thread (it's blocking I/O)
            replies = await asyncio.to_thread(_poll_gmail_once)

            for reply in replies:
                print(f"[InboxMonitor] 📬 Processing reply from {reply['sender']}: {reply['subject']}")
                await _process_reply(
                    sender_email=reply["sender"],
                    subject=reply["subject"],
                    body=reply["body"],
                )

        except Exception as e:
            print(f"[InboxMonitor] ❌ Loop error: {e}")

        await asyncio.sleep(POLL_INTERVAL)
