"""
Synaptiq — Bland.ai Agentic Call Service

Triggers outbound AI calls via Bland.ai REST API.
The AI agent (named from the persona_config) calls the lead,
qualifies them, and aims to book a 10-minute meeting.
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

BLAND_API_KEY = os.getenv("BLAND_API_KEY", "")
NGROK_DOMAIN = os.getenv("NGROK_DOMAIN", "")  # e.g. "abc123.ngrok-free.app"


def trigger_bland_call(
    to_phone: str,
    lead_name: str,
    company: str,
    agent_name: str,
    campaign_id: int,
    lead_id: int,
    insight: str = "",
) -> dict:
    """
    Triggers an outbound Bland.ai call to a lead.
    The AI agent tries to qualify and book a 10-minute meeting.
    Returns {"call_id": str} on success or {"error": str} on failure.
    """
    if not BLAND_API_KEY:
        return {"error": "Missing BLAND_API_KEY in environment"}

    url = "https://api.bland.ai/v1/calls"
    headers = {
        "authorization": BLAND_API_KEY,
        "Content-Type": "application/json",
    }

    company_insight = f" I noticed {insight}." if insight else ""

    prompt = (
        f"You are {agent_name}, a Senior Growth Specialist at Synaptiq. "
        f"You are calling {lead_name} from {company}.{company_insight} "
        "Your goal is to qualify the lead for our AI-powered outreach solution. "
        "If they are interested, schedule a 10-minute discovery call for tomorrow. "
        "Keep the call brief, friendly, and professional. "
        "If they agree to a meeting, confirm the time and tell them a WhatsApp confirmation is being sent. "
        "If they are not interested, thank them politely and end the call."
    )

    first_sentence = (
        f"Hello, am I speaking with {lead_name}? "
        f"I'm {agent_name} calling from Synaptiq — do you have 30 seconds?"
    )

    webhook_url = f"https://{NGROK_DOMAIN}/webhook/bland" if NGROK_DOMAIN else None

    payload = {
        "phone_number": to_phone,
        "task": prompt,
        "first_sentence": first_sentence,
        "voice": "maya",
        "language": "en",
        "reduce_latency": True,
        "record": True,
        "webhook": webhook_url,
        "metadata": {
            "campaign_id": campaign_id,
            "lead_id": lead_id,
            "lead_name": lead_name,
            "company": company,
        },
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        if response.status_code in [200, 201]:
            data = response.json()
            call_id = data.get("call_id")
            print(f"[Bland] 📞 Call dispatched to {to_phone} — call_id: {call_id}")
            return {"call_id": call_id}
        else:
            print(f"[Bland] ❌ API Error {response.status_code}: {response.text}")
            return {"error": f"Bland API Error {response.status_code}: {response.text}"}
    except requests.exceptions.RequestException as e:
        print(f"[Bland] ❌ Request error: {e}")
        return {"error": str(e)}


def analyze_transcript_keywords(transcript: str) -> bool:
    """
    Fallback keyword check to determine if meeting was booked.
    Used when Gemini is unavailable.
    """
    lower = transcript.lower()
    positive_signals = [
        "yes", "sure", "sounds good", "okay", "ok", "book",
        "meeting", "briefing", "tomorrow", "2 pm", "call",
        "interested", "let's do it", "great",
    ]
    return any(w in lower for w in positive_signals)
