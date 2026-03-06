# services/clawbot_service.py
"""
Synaptiq ClawBot Service
WhatsApp message builder + Twilio sandbox sender.
No LLM needed — pure message formatting and delivery.
"""

import os

# ---------------------------------------------------------------------------
# Twilio sender
# ---------------------------------------------------------------------------


def send_whatsapp(to: str, message: str) -> bool:
    """Send a WhatsApp message via Twilio sandbox. Returns True on success."""
    try:
        from twilio.rest import Client

        client = Client(os.getenv("TWILIO_SID"), os.getenv("TWILIO_AUTH"))
        client.messages.create(
            from_=os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886"),
            to=f"whatsapp:{to}",
            body=message,
        )
        return True
    except Exception as e:
        print(f"[ClawBot] WhatsApp send failed: {e}")
        return False


# ---------------------------------------------------------------------------
# Message builders
# ---------------------------------------------------------------------------


def build_hot_lead_alert(lead: dict, draft: str, opens: int) -> str:
    """Build a WhatsApp alert for a hot lead (multiple email opens)."""
    return f"""🦅 ClawBot Alert
─────────────────────────────────
🔥 Hot lead: {lead.get('first_name', '')} {lead.get('last_name', '')} ({lead.get('title', '')}, {lead.get('company', '')})
   Opened your email {opens}x in 2 hours

Ready to send follow-up?
"{draft[:120]}..."

Reply:
✅ YES — send now
✏️ Type your own message
⏭️ SKIP
🛑 PAUSE campaign"""


def build_objection_alert(
    lead: dict, reply_text: str, label: str, draft: str
) -> str:
    """Build a WhatsApp alert when a lead replies."""
    return f"""🦅 ClawBot — Reply Detected
─────────────────────────────────────
💬 {lead.get('first_name', '')} replied:
"{reply_text[:100]}"

Classified: {label}

Suggested response:
"{draft[:150]}"

Reply YES to send, or type your own."""


def build_meeting_alert(lead: dict, start_time: str) -> str:
    """Build a WhatsApp alert when a meeting is booked."""
    return f"""🎉 Meeting Booked!
─────────────────────────────────
{lead.get('first_name', '')} {lead.get('last_name', '')} from {lead.get('company', '')}
just booked a call: {start_time}

Check your Google Calendar for the invite. 📅"""


def build_daily_digest(stats: dict) -> str:
    """Build a daily campaign digest message."""
    return f"""🦅 Synaptiq Daily Digest
─────────────────────────────────
📤 Sent today:      {stats.get('sent_today', 0)}
📬 Open rate:       {stats.get('open_rate', 0)}%
💬 Replies:         {stats.get('replied', 0)}
📅 Meetings booked: {stats.get('meetings_booked', 0)}
⚠️  Issues:          {stats.get('issues', 'None')}

Reply REPORT for full AI analysis"""
