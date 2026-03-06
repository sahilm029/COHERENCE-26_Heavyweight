# services/ghost_voice.py
"""
Synaptiq Ghost Voice Service
Extracts writing style fingerprints from sample emails so the AI
can replicate the user's exact tone and voice.
"""

import os
import json

import google.generativeai as genai

genai.configure(api_key=os.getenv("GEMINI_API_KEY", ""))
flash_model = genai.GenerativeModel("gemini-2.0-flash")


def _call_gemini_json(model, prompt: str) -> dict:
    """Call Gemini with JSON mode and return parsed dict."""
    response = model.generate_content(
        prompt + "\n\nRespond with valid JSON only. No markdown fences. No explanation.",
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json"
        ),
    )
    return json.loads(response.text)


# Default ghost voice (fallback)
DEFAULT_GHOST_VOICE = {
    "system_prompt": (
        "You write exactly like a specific person. Their style: "
        "Short punchy sentences. Casual but professional. Uses em-dashes frequently. "
        "Starts with the recipient's name, no 'Hi' or 'Hello'. Signs off with just their first name. "
        "Asks one question per email. Avoids exclamation marks entirely."
    ),
    "fingerprint_summary": (
        "Direct and casual writer who favors brevity. "
        "Uses name-only greetings and question-based CTAs."
    ),
    "sample_phrases": [
        "Quick thought on this —",
        "Curious how you're handling",
        "Worth a 15-min chat?",
    ],
}


async def extract_ghost_voice(sample_emails: list[str]) -> dict:
    """
    Analyze sample emails and extract a writing fingerprint as a system prompt
    that another AI can use to replicate the exact style.

    Args:
        sample_emails: List of email body strings written by one person.

    Returns:
        dict with keys: system_prompt, fingerprint_summary, sample_phrases
    """
    if not sample_emails:
        return DEFAULT_GHOST_VOICE

    try:
        combined = "\n---\n".join(sample_emails)

        prompt = f"""Analyze these emails written by one person and extract their
writing fingerprint as a detailed system prompt that another AI could use
to replicate their exact style.

Focus on:
- Average sentence length (short/medium/long)
- Punctuation habits (em-dashes, ellipses, exclamation avoidance)
- Greeting pattern (Hi/Hey/Hello/name-only/no greeting)
- CTA pattern (question-based/direct/soft/none)
- Sign-off style
- Paragraph structure (single line vs blocks)
- Vocabulary level and any distinctive phrases
- Most unique characteristic of their voice

Emails to analyze:
{combined}

Return JSON:
{{
  "system_prompt": "You write exactly like a specific person. Their style: [detailed description]",
  "fingerprint_summary": "2-sentence plain English summary of their style",
  "sample_phrases": ["phrase1", "phrase2", "phrase3"]
}}"""

        return _call_gemini_json(flash_model, prompt)

    except Exception:
        return DEFAULT_GHOST_VOICE
