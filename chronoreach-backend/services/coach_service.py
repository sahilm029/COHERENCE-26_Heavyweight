# services/coach_service.py
"""
Synaptiq AI SDR Coach Service
Analyzes campaign performance stats and provides actionable improvements.
Uses Groq Llama-3.3-70B for analysis (saves Gemini quota).
"""

import os
import json

from groq import Groq
from tenacity import retry, stop_after_attempt, wait_exponential

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY", ""))

# ---------------------------------------------------------------------------
# Default coaching insights (fallback if API fails)
# ---------------------------------------------------------------------------

DEFAULT_INSIGHTS = {
    "insights": [
        {
            "issue": "Open rate below industry average",
            "fix": "Test shorter subject lines (under 6 words) with a question format",
            "impact": "HIGH",
            "metric_reference": "open_rate",
        },
        {
            "issue": "Low reply rate despite good opens",
            "fix": "Shorten email body to under 80 words and end with a single clear question",
            "impact": "HIGH",
            "metric_reference": "reply_rate",
        },
        {
            "issue": "Morning sends outperforming afternoon",
            "fix": "Shift all sends to 9-10 AM window in lead's timezone",
            "impact": "MEDIUM",
            "metric_reference": "send_time_performance",
        },
        {
            "issue": "Step 3 emails have significantly lower engagement",
            "fix": "Make final email a graceful exit with an easy yes/no ask instead of another pitch",
            "impact": "MEDIUM",
            "metric_reference": "step_3_metrics",
        },
    ]
}


# ---------------------------------------------------------------------------
# Campaign analysis
# ---------------------------------------------------------------------------


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
async def analyze_campaign(campaign_stats: dict) -> dict:
    """
    Analyze campaign performance and return 4 specific, actionable improvements.
    Uses Groq Llama-3.3-70B for fast, free analysis.

    Args:
        campaign_stats: dict with keys like sent, opened, replied, bounced,
                       open_rate, reply_rate, bounce_rate, step_metrics, etc.

    Returns:
        dict with 'insights' list, each containing issue, fix, impact, metric_reference
    """
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a blunt senior sales coach with 15 years of B2B experience. "
                        "You give 4 specific, actionable improvements. No generic advice. "
                        "Every suggestion must reference specific numbers from the stats provided."
                    ),
                },
                {
                    "role": "user",
                    "content": f"""Analyze these campaign results and give exactly 4 improvements.

Stats:
{json.dumps(campaign_stats, indent=2)}

Return JSON:
{{
  "insights": [
    {{
      "issue": "specific problem observed from stats",
      "fix": "exact change to make",
      "impact": "HIGH or MEDIUM or LOW",
      "metric_reference": "the stat number that revealed this"
    }}
  ]
}}""",
                },
            ],
            response_format={"type": "json_object"},
            max_tokens=600,
        )
        return json.loads(response.choices[0].message.content)

    except Exception:
        return DEFAULT_INSIGHTS
