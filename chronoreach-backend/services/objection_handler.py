# services/objection_handler.py
"""
Synaptiq Objection Handler
Classifies lead replies into 6 archetypes and generates appropriate responses.
Uses Groq for fast classification, Gemini Flash-Lite for response generation.
"""

import os
import json
from pathlib import Path

import google.generativeai as genai
from groq import Groq
from tenacity import retry, stop_after_attempt, wait_exponential

genai.configure(api_key=os.getenv("GEMINI_API_KEY", ""))
lite_model = genai.GenerativeModel("gemini-2.0-flash-lite")
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY", ""))

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"

# ---------------------------------------------------------------------------
# Labels and type-specific prompts
# ---------------------------------------------------------------------------

LABELS = {
    "timing":       "⏰ Timing Objection",
    "wrong_person": "👤 Wrong Person",
    "competitor":   "⚔️ Competitor Loyal",
    "budget":       "💰 Budget Concern",
    "no_interest":  "🚫 No Interest — Mark DNC",
    "positive":     "✅ Positive Intent — Book Meeting",
}

RESPONSE_PROMPTS = {
    "timing": (
        "Acknowledge timing fully. Offer 90-day reconnect. "
        "Include one useful resource. Ask if Q2 works. Under 80 words."
    ),
    "wrong_person": (
        "Thank them. Ask for warm intro by name. "
        "Include 1-sentence pitch they can paste. Under 50 words."
    ),
    "competitor": (
        "Acknowledge current tool respectfully. Never bash competitor. "
        "Mention ONE specific gap. Ask one curious question about their setup. "
        "Under 90 words."
    ),
    "budget": (
        "Reframe as ROI not price. Mention a specific result from similar company. "
        "Offer a pilot. Under 80 words."
    ),
    "no_interest": (
        "Graceful 2-sentence exit. Thank them genuinely. "
        "Leave door open. Zero CTA. Under 30 words."
    ),
    "positive": (
        "Warm acknowledgment. Immediately include [CALENDAR_LINK]. "
        "Set expectations for call. Under 60 words."
    ),
}

# ---------------------------------------------------------------------------
# Classification (Groq — fast)
# ---------------------------------------------------------------------------

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
async def classify_objection(reply_text: str) -> dict:
    """
    Classify an email reply into one of 6 categories using Groq Llama-3.1-8B.
    Returns: {"type": "category", "confidence": 0.0, "keywords_detected": [...]}
    """
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Classify this email reply into exactly one of these categories:\n"
                        f"timing, wrong_person, competitor, budget, no_interest, positive\n\n"
                        f'Reply: "{reply_text}"\n\n'
                        f'Return JSON only: {{"type": "category_name", '
                        f'"confidence": 0.0, "keywords_detected": ["word1"]}}'
                    ),
                }
            ],
            response_format={"type": "json_object"},
            max_tokens=100,
        )
        return json.loads(response.choices[0].message.content)
    except Exception:
        # Default to no_interest if classification fails
        return {
            "type": "no_interest",
            "confidence": 0.5,
            "keywords_detected": ["classification_failed"],
        }


# ---------------------------------------------------------------------------
# Response generation (Gemini Flash-Lite)
# ---------------------------------------------------------------------------

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
async def generate_objection_response(
    lead: dict,
    objection_type: str,
    original_reply: str,
) -> str:
    """Generate a tailored response based on the objection type."""
    try:
        type_instruction = RESPONSE_PROMPTS.get(objection_type, RESPONSE_PROMPTS["no_interest"])

        prompt = f"""You are a skilled B2B sales rep responding to a lead's reply.

Lead: {lead.get('first_name', '')} {lead.get('last_name', '')} — {lead.get('title', '')} at {lead.get('company', '')}

Their reply: "{original_reply}"

Objection type: {objection_type}

Instructions: {type_instruction}

Write ONLY the response email body. No subject line. No explanation."""

        response = lite_model.generate_content(prompt)
        return response.text.strip()

    except Exception:
        # Load from fixtures
        try:
            with open(FIXTURES_DIR / "objection_responses.json", "r", encoding="utf-8") as f:
                fixtures = json.load(f)
            return fixtures.get(objection_type, {}).get(
                "draft_response",
                "Thanks for getting back to me. I appreciate your time.",
            )
        except Exception:
            return "Thanks for getting back to me. I appreciate your time."


# ---------------------------------------------------------------------------
# Combined handler
# ---------------------------------------------------------------------------

async def handle_reply(reply_text: str, lead: dict) -> dict:
    """
    Full pipeline: classify reply → generate response → return structured result.
    """
    classification = await classify_objection(reply_text)
    objection_type = classification.get("type", "no_interest")

    response = await generate_objection_response(lead, objection_type, reply_text)

    return {
        "type": objection_type,
        "label": LABELS.get(objection_type, "❓ Unknown"),
        "confidence": classification.get("confidence", 0.0),
        "draft_response": response,
        "is_dnc": objection_type == "no_interest",
        "book_meeting": objection_type == "positive",
    }
