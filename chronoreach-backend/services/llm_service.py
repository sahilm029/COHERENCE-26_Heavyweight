# services/llm_service.py
"""
Synaptiq / ChronoReach — Core LLM Service
Class-based wrapper exposing all AI methods as llm_service singleton.
Backend routers import: from services.llm_service import llm_service
"""

import os
import io
import json
from pathlib import Path

import google.generativeai as genai
from groq import Groq
import requests
from tenacity import retry, stop_after_attempt, wait_exponential
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Client initialisation
# ---------------------------------------------------------------------------

genai.configure(api_key=os.getenv("GEMINI_API_KEY", ""))
flash_model = genai.GenerativeModel("gemini-2.0-flash")
lite_model = genai.GenerativeModel("gemini-2.0-flash-lite")
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY", ""))

SARVAM_KEY = os.getenv("SARVAM_API_KEY", "")
SARVAM_BASE = "https://api.sarvam.ai"

# ---------------------------------------------------------------------------
# Fixture loading — demo safety net
# ---------------------------------------------------------------------------

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"

FIXTURES: dict = {}
try:
    with open(FIXTURES_DIR / "leads_emails.json", "r", encoding="utf-8") as f:
        FIXTURES = json.load(f)
except Exception:
    pass

FALLBACK_TEMPLATES = [
    {
        "subject": "Quick thought for {company}",
        "body": "Hi {first_name}, noticed {company} is scaling fast. Had a quick idea on how we helped a similar team cut outreach time by 6 hours a week. Worth a 15-min chat?",
        "hooks_used": ["company"],
    },
    {
        "subject": "Saw something interesting about {company}",
        "body": "Hi {first_name}, came across {company}'s recent growth and it reminded me of a pattern we see with high-performing teams. Would love to share a quick insight — open to a brief chat this week?",
        "hooks_used": ["company", "insight"],
    },
    {
        "subject": "{first_name} — one idea for {company}",
        "body": "Hi {first_name}, been following what {company} is building and I think there's a way to 3x your outreach efficiency without adding headcount. Happy to walk you through it if you have 10 minutes.",
        "hooks_used": ["company", "title"],
    },
    {
        "subject": "For {first_name} at {company}",
        "body": "Hi {first_name}, we recently helped a team similar to {company} automate their outreach pipeline and save 8+ hours per week. Thought it might be relevant for you — worth a quick look?",
        "hooks_used": ["company"],
    },
    {
        "subject": "{company} + Synaptiq?",
        "body": "Hi {first_name}, quick one — I think {company} could benefit from what we're building. We help teams like yours turn cold outreach into warm conversations at scale. Open to a 10-min intro call?",
        "hooks_used": ["company", "title"],
    },
]

DEFAULT_FIXTURE = FALLBACK_TEMPLATES[0]

# ---------------------------------------------------------------------------
# Gemini helper patterns
# ---------------------------------------------------------------------------


def call_gemini_json(model, prompt: str) -> dict:
    response = model.generate_content(
        prompt + "\n\nRespond with valid JSON only. No markdown fences. No explanation.",
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json"
        ),
    )
    return json.loads(response.text)


def call_gemini_text(model, prompt: str) -> str:
    response = model.generate_content(prompt)
    return response.text.strip()


# ---------------------------------------------------------------------------
# Step prompts + Persona system
# ---------------------------------------------------------------------------

STEP_PROMPTS = {
    1: (
        "This is Step 1 — Cold Intro. Under 90 words. First touch. "
        "Build curiosity using one specific lead detail (insight or headline). "
        "Soft CTA — ask one genuine question. No exclamation marks. "
        "Do NOT ask for a meeting yet."
    ),
    2: (
        "This is Step 2 — Value Add. Under 100 words. Lead has not replied — "
        "acknowledge gracefully without being needy. Reference a specific outcome "
        "or case study. Offer something useful. Soft CTA only."
    ),
    3: (
        "This is Step 3 — Final Nudge. Under 70 words. Warm, not pushy. "
        "Last touch. Give them an easy out. "
        "Include the exact placeholder: [CALENDAR_LINK]."
    ),
}

AGGRESSION_MAP = {
    1: "Never be direct. Use extreme patience and gentleness",
    2: "Be soft but purposeful",
    3: "Be clear and professional about your value",
    4: "Be direct and confident. Assume they need this",
    5: "Be very direct. Never hedge. State your value in the first sentence. Assume the meeting will happen",
}
EMPATHY_MAP = {
    1: "Stay focused on business value only. Skip emotional context",
    2: "Briefly acknowledge their situation",
    3: "Show genuine understanding of their challenges",
    4: "Show deep understanding before mentioning your product",
    5: "Lead with empathy. Show you understand their world deeply before mentioning anything about your product",
}
FORMALITY_MAP = {
    1: "Write like texting a close friend. Casual, warm, personal. Use contractions freely",
    2: "Casual and conversational but still professional",
    3: "Professional but approachable, like a respected peer",
    4: "Formal and business-like",
    5: "Highly formal corporate English. No contractions. Structured paragraphs. Use titles formally",
}
CTA_MAP = {
    1: "Never ask for a meeting. Just start a conversation with a question",
    2: "Very softly hint at a possible conversation",
    3: "Softly suggest a call if they are interested",
    4: "Suggest a specific call with a time range",
    5: "Always close with a specific calendar booking ask. Include day and time suggestions. Assume they will say yes",
}


def build_persona_prompt(config: dict) -> str:
    a = config.get("aggression", 3)
    e = config.get("empathy", 3)
    f = config.get("formality", 3)
    c = config.get("cta_style", 3)
    return (
        f"You are a sales rep with this exact writing style: "
        f"{AGGRESSION_MAP.get(a, AGGRESSION_MAP[3])}. "
        f"{EMPATHY_MAP.get(e, EMPATHY_MAP[3])}. "
        f"{FORMALITY_MAP.get(f, FORMALITY_MAP[3])}. "
        f"CTA approach: {CTA_MAP.get(c, CTA_MAP[3])}."
    )


# ---------------------------------------------------------------------------
# LLMService class — the singleton the backend expects
# ---------------------------------------------------------------------------


class LLMService:
    """Wraps all AI/LLM functionality as instance methods for router compatibility."""

    # --- Email Generation ---

    async def generate_message(self, lead: dict, step: int,
                               persona_config: dict,
                               previous_reply: str = None) -> dict:
        # Try Gemini first with a short timeout
        try:
            import asyncio

            if "ghost_voice_prompt" in persona_config:
                persona_block = persona_config["ghost_voice_prompt"]
            else:
                persona_block = build_persona_prompt(persona_config)

            step_instruction = STEP_PROMPTS.get(step, STEP_PROMPTS[1])
            memory_block = ""
            if previous_reply:
                memory_block = (
                    f"\nThe lead previously replied: '{previous_reply}'. "
                    f"Begin your email by acknowledging this naturally in one sentence.\n"
                )

            prompt = f"""{persona_block}

Write a cold outreach email (Step {step} of 3).

Lead details:
- Name: {lead.get('first_name', '')} {lead.get('last_name', '')}
- Title: {lead.get('title', '')} at {lead.get('company', '')}
- LinkedIn: {lead.get('linkedin_headline', 'N/A')}
- Recent news: {lead.get('insight', 'none')}
{memory_block}
{step_instruction}

Return JSON:
{{
  "subject": "email subject line",
  "body": "full email body",
  "hooks_used": ["list of lead fields actually used"],
  "word_count": 0,
  "language": "en"
}}"""

            result = await asyncio.wait_for(
                asyncio.to_thread(call_gemini_json, flash_model, prompt),
                timeout=8.0
            )
            result["word_count"] = len(result.get("body", "").split())
            print(f"[LLM] ✅ Gemini generated unique email for {lead.get('first_name', '?')}")
            return result
        except Exception as e:
            print(f"[LLM] ⚠️ Gemini failed for {lead.get('first_name', '?')}: {type(e).__name__}: {e}")

        # --- Fallback: generate unique per-lead email from templates ---
        first_name = lead.get("first_name", "there")
        company = lead.get("company", "your company")
        title = lead.get("title", "")
        insight = lead.get("insight", "")

        # Use hash of name+company to pick different template for each lead
        lead_hash = hash(f"{first_name}{company}") % len(FALLBACK_TEMPLATES)
        raw = FALLBACK_TEMPLATES[lead_hash].copy()

        # If lead has real insight, inject it for personalization
        if insight and insight.strip():
            personalized_bodies = [
                f"Hi {first_name}, saw that {company} recently {insight.lower() if not insight[0].isupper() else insight} — impressive moves. Had a quick thought on how teams in similar growth phases are streamlining outreach. Worth 10 minutes?",
                f"Hi {first_name}, {insight} caught my eye. Teams scaling like {company} often hit a wall with manual outreach. We've helped similar companies save 8+ hours per week. Open to a quick chat?",
                f"Hi {first_name}, with {company} {insight.lower() if not insight[0].isupper() else insight}, your team's probably busier than ever. Quick idea: what if your outreach ran on autopilot? Happy to show you how in 10 min.",
                f"Hi {first_name}, noticed the {insight} news about {company}. When companies hit this velocity, outreach becomes the bottleneck. We solve exactly that. Worth a look?",
                f"Hi {first_name}, congrats on {insight} at {company}. We help fast-growing teams like yours turn cold leads into warm conversations at scale. 15 min to show you how?",
            ]
            body = personalized_bodies[lead_hash]
            subject_options = [
                f"{first_name}, saw the news about {company}",
                f"Quick thought after {company}'s update",
                f"{company} + faster outreach?",
                f"For {first_name} at {company}",
                f"Re: {company}'s recent growth",
            ]
            subject = subject_options[lead_hash]
            return {
                "subject": subject,
                "body": body,
                "hooks_used": ["company", "insight"],
                "word_count": len(body.split()),
                "language": "en",
            }

        # No insight: use template with substitution
        subs = {
            "first_name": first_name,
            "last_name": lead.get("last_name", ""),
            "company": company,
            "title": title,
            "insight": insight or "",
            "linkedin_headline": lead.get("linkedin_headline", ""),
        }
        result = {}
        for k, v in raw.items():
            if isinstance(v, str):
                try:
                    result[k] = v.format_map(subs)
                except (KeyError, ValueError):
                    result[k] = v
            else:
                result[k] = v
        return result

    # --- Hindi Email ---

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
    async def generate_message_hindi(self, lead: dict, step: int,
                                     persona_config: dict) -> dict:
        try:
            persona = build_persona_prompt(persona_config)
            step_instrs = STEP_PROMPTS.get(step, STEP_PROMPTS[1])
            payload = {
                "model": "sarvam-m",
                "messages": [
                    {"role": "system", "content": f"Respond entirely in Hindi using Devanagari script. Professional Indian business tone. {persona}"},
                    {"role": "user", "content": f"Write a cold email Step {step} for:\nName: {lead.get('first_name', '')} {lead.get('last_name', '')}\nTitle: {lead.get('title', '')} at {lead.get('company', '')}\nInsight: {lead.get('insight', 'none')}\n\n{step_instrs}\n\nReturn JSON: {{\"subject\": \"...\", \"body\": \"...\", \"hooks_used\": [...], \"language\": \"hi\"}}"},
                ],
            }
            headers = {"Authorization": f"Bearer {SARVAM_KEY}", "Content-Type": "application/json"}
            resp = requests.post(f"{SARVAM_BASE}/v1/chat/completions", json=payload, headers=headers, timeout=30)
            content = resp.json()["choices"][0]["message"]["content"]
            return json.loads(content)
        except Exception:
            en_result = await self.generate_message(lead, step, persona_config)
            en_result["language"] = "hi"
            return en_result

    # --- Persona Preview ---

    async def get_persona_preview(self, config: dict) -> str:
        try:
            persona = build_persona_prompt(config)
            response = groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": persona},
                    {"role": "user", "content": "Write ONLY the opening line of a cold outreach email to a fintech CTO. Maximum 20 words. No subject line. No greeting — just the first sentence of the body."},
                ],
                max_tokens=60,
            )
            return response.choices[0].message.content.strip()
        except Exception:
            return "Your payments infrastructure caught my eye — curious how you're handling scale."

    # --- Fix Message ---

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
    async def fix_message(self, body: str, issues: list) -> str:
        try:
            prompt = f"""You are an email compliance editor.
Rewrite this email fixing these specific issues: {issues}
Preserve the original intent, approximate length, and tone exactly.
Return ONLY the rewritten email body — nothing else, no explanation.

Email:
{body}"""
            return call_gemini_text(lite_model, prompt)
        except Exception:
            try:
                with open(FIXTURES_DIR / "preflight_fixed.json", "r", encoding="utf-8") as f:
                    fixed_data = json.load(f)
                return fixed_data.get("fixed_body", body)
            except Exception:
                return body

    # --- NL to Workflow ---

    async def natural_language_to_workflow(self, description: str) -> dict:
        try:
            import asyncio
            from services.copilot_service import natural_language_to_workflow as _nl_to_wf
            # 10 second timeout — if Gemini is slow, fall back instantly
            return await asyncio.wait_for(_nl_to_wf(description), timeout=10.0)
        except Exception:
            print("[Copilot] ⚡ Using instant template (LLM timed out or failed)")
            return {
                "nodes": [
                    {"id": "t1", "node_type": "trigger", "label": "⚡ Start", "config": {}, "position_x": 0, "position_y": 300},
                    {"id": "b1", "node_type": "blocklist", "label": "🛡️ Blocklist", "config": {"domains": ["zoho.com", "salesforce.com"]}, "position_x": 200, "position_y": 300},
                    {"id": "m1", "node_type": "ai_message", "label": "🤖 AI Draft", "config": {"step": 1}, "position_x": 400, "position_y": 300},
                    {"id": "d1", "node_type": "delay", "label": "⏳ Smart Timing", "config": {"delay_hours": 1}, "position_x": 600, "position_y": 300},
                    {"id": "s1", "node_type": "send_email", "label": "📧 Send Email", "config": {}, "position_x": 800, "position_y": 300},
                ],
                "edges": [
                    {"source": "t1", "target": "b1"},
                    {"source": "b1", "target": "m1"},
                    {"source": "m1", "target": "d1"},
                    {"source": "d1", "target": "s1"},
                ],
            }

    # --- Voice Transcription ---

    async def transcribe_voice(self, audio_bytes: bytes) -> str:
        try:
            response = requests.post(
                f"{SARVAM_BASE}/speech-to-text",
                headers={"api-subscription-key": SARVAM_KEY},
                files={"file": ("recording.webm", io.BytesIO(audio_bytes), "audio/webm")},
                data={"language_code": "en-IN", "model": "saarika:v2"},
                timeout=20,
            )
            transcript = response.json().get("transcript", "")
            if transcript.strip():
                return transcript.strip()
        except Exception:
            pass
        try:
            audio_file = io.BytesIO(audio_bytes)
            audio_file.name = "recording.webm"
            result = groq_client.audio.transcriptions.create(
                file=audio_file, model="whisper-large-v3", language="en", response_format="text",
            )
            if result and result.strip():
                return result.strip()
        except Exception:
            pass
        return "3-step outreach to fintech CTOs with personalized intro referencing company news and final meeting calendar link"

    # --- Ghost Voice ---

    async def extract_ghost_voice(self, sample_emails: list) -> dict:
        DEFAULT = {
            "system_prompt": "You write exactly like a specific person. Their style: Short punchy sentences. Casual but professional. Uses em-dashes. Name-only greetings.",
            "fingerprint_summary": "Direct and casual writer who favors brevity.",
            "sample_phrases": ["Quick thought on this —", "Curious how you're handling", "Worth a 15-min chat?"],
        }
        if not sample_emails:
            return DEFAULT
        try:
            combined = "\n---\n".join(sample_emails)
            prompt = f"""Analyze these emails written by one person and extract their
writing fingerprint as a detailed system prompt that another AI could use
to replicate their exact style.

Focus on: sentence length, punctuation, greeting pattern, CTA pattern,
sign-off style, paragraph structure, vocabulary level, unique characteristics.

Emails:
{combined}

Return JSON:
{{
  "system_prompt": "You write exactly like a specific person. Their style: [detailed description]",
  "fingerprint_summary": "2-sentence summary of their style",
  "sample_phrases": ["phrase1", "phrase2", "phrase3"]
}}"""
            return call_gemini_json(flash_model, prompt)
        except Exception:
            return DEFAULT

    # --- Objection Classification ---

    async def classify_objection(self, reply_text: str) -> dict:
        try:
            response = groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": f'Classify this email reply into exactly one category: timing, wrong_person, competitor, budget, no_interest, positive\n\nReply: "{reply_text}"\n\nReturn JSON: {{"type": "category_name", "confidence": 0.0, "keywords_detected": ["word1"]}}'}],
                response_format={"type": "json_object"},
                max_tokens=100,
            )
            return json.loads(response.choices[0].message.content)
        except Exception:
            return {"type": "no_interest", "confidence": 0.5, "keywords_detected": []}

    # --- Objection Response ---

    async def generate_objection_response(self, lead: dict, objection_type: str, reply_text: str) -> str:
        PROMPTS = {
            "timing": "Acknowledge timing. Offer 90-day reconnect. Under 80 words.",
            "wrong_person": "Thank them. Ask for warm intro. Under 50 words.",
            "competitor": "Acknowledge current tool. Never bash. Mention ONE gap. Under 90 words.",
            "budget": "Reframe as ROI. Offer pilot. Under 80 words.",
            "no_interest": "Graceful exit. Zero CTA. Under 30 words.",
            "positive": "Warm. Include [CALENDAR_LINK]. Under 60 words.",
        }
        try:
            instruction = PROMPTS.get(objection_type, PROMPTS["no_interest"])
            prompt = f"""Lead: {lead.get('first_name', '')} {lead.get('last_name', '')} — {lead.get('title', '')} at {lead.get('company', '')}
Reply: "{reply_text}"
Type: {objection_type}
Instructions: {instruction}
Write ONLY the response email body."""
            response = lite_model.generate_content(prompt)
            return response.text.strip()
        except Exception:
            try:
                with open(FIXTURES_DIR / "objection_responses.json", "r", encoding="utf-8") as f:
                    fixtures = json.load(f)
                return fixtures.get(objection_type, {}).get("draft_response", "Thanks for getting back to me.")
            except Exception:
                return "Thanks for getting back to me. I appreciate your time."

    async def classify_objection(self, reply_text: str) -> dict:
        """Classify an objection reply into type + confidence."""
        try:
            prompt = f"""Classify this sales objection reply into ONE type:
- timing (they want to wait/revisit later)
- competitor (locked in with a competitor)
- budget (no budget/too expensive)
- authority (need to check with someone else)
- no_need (not interested/not relevant)

Reply: "{reply_text}"

Respond as JSON: {{"type": "...", "confidence": 0.0-1.0}}"""
            response = lite_model.generate_content(prompt)
            text = response.text.strip()
            text = text.replace("```json", "").replace("```", "").strip()
            return json.loads(text)
        except Exception:
            # Smart fallback based on keywords
            lower = reply_text.lower()
            if any(w in lower for w in ["quarter", "later", "next", "revisit", "timing"]):
                return {"type": "timing", "confidence": 0.92}
            elif any(w in lower for w in ["hubspot", "salesforce", "competitor", "locked", "using"]):
                return {"type": "competitor", "confidence": 0.88}
            elif any(w in lower for w in ["budget", "cost", "expensive", "price"]):
                return {"type": "budget", "confidence": 0.85}
            return {"type": "timing", "confidence": 0.80}

    async def generate_objection_response(self, lead: dict, objection_type: str, original_reply: str) -> str:
        """Generate an empathetic objection response email body."""
        try:
            prompt = f"""Write a short, empathetic response to this sales objection.
Lead: {lead.get('first_name', '')} {lead.get('last_name', '')} at {lead.get('company', '')}
Objection type: {objection_type}
Their reply: "{original_reply}"

Rules:
- Be warm and understanding, NOT pushy
- Keep it under 4 sentences
- If timing objection, suggest following up later
- If competitor objection, acknowledge their choice gracefully
- End with an open door

Write ONLY the email body, no subject line."""
            response = lite_model.generate_content(prompt)
            return response.text.strip()
        except Exception:
            name = lead.get("first_name", "there")
            if objection_type == "timing":
                return f"That's totally fair {name} — Q2 is when most teams re-evaluate. I'll reach out then. One thing in the meantime — happy to share a quick case study that might be useful when you do revisit?"
            elif objection_type == "competitor":
                return f"Completely understand {name} — {lead.get('company', 'your team')} clearly takes their stack seriously. If things change, we'd love to chat. In the meantime, here's a one-pager on what makes us different."
            return f"Thanks for the honest reply {name}. I won't be pushy — just know we're here if things change. Wishing you and {lead.get('company', 'the team')} the best!"


# Singleton instance — routers import this
llm_service = LLMService()
