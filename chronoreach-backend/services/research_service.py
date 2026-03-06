# services/research_service.py
"""
Synaptiq Research Service
Provides lead enrichment via hardcoded insights, persistent cache, and Tavily live search.
"""

import os
import json
import asyncio
from pathlib import Path

# ---------------------------------------------------------------------------
# Hardcoded Insights Map — 10 Indian companies, always available offline
# ---------------------------------------------------------------------------

HARDCODED_INSIGHTS = {
    "Razorpay":    "Just raised Series F funding — $160M",
    "CRED":        "Recently launched new vehicle management feature",
    "Zepto":       "Expanding dark store network to 100 cities by Q2 2026",
    "Meesho":      "Crossed 150M registered users milestone",
    "PhonePe":     "Launched international payments in 15 countries",
    "Groww":       "Received SEBI approval for mutual fund AMC license",
    "Slice":       "Completed merger with North East Small Finance Bank",
    "BharatPe":    "Launched merchant lending product at 18% interest rate",
    "Juspay":      "Processing 80M transactions per day across 500+ clients",
    "Cashfree":    "Launched instant bank account verification API",
}

# ---------------------------------------------------------------------------
# Cache helpers — simple JSON file at cache/research_cache.json
# ---------------------------------------------------------------------------

CACHE_PATH = Path(__file__).resolve().parent.parent / "cache" / "research_cache.json"


def _load_cache() -> dict:
    """Load the persistent research cache from disk."""
    try:
        if CACHE_PATH.exists():
            with open(CACHE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
    except (json.JSONDecodeError, IOError):
        pass
    return {}


def _save_to_cache(company: str, insight: str) -> None:
    """Append a new insight to the persistent cache and save."""
    cache = _load_cache()
    cache[company] = insight
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Summarisation helper (Gemini Flash-Lite — cheap, fast)
# ---------------------------------------------------------------------------

async def _summarize_to_sentence(raw_text: str) -> str:
    """Summarize raw search result into a single insight sentence."""
    try:
        import google.generativeai as genai

        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        model = genai.GenerativeModel("gemini-2.0-flash-lite")

        prompt = (
            f"Summarize this into ONE short sentence (under 15 words) "
            f"that could be used as a personalization hook in a cold email:\n\n"
            f"{raw_text[:500]}"
        )
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception:
        # If LLM fails, just take first sentence of raw text
        first_sentence = raw_text.split(".")[0].strip()
        return first_sentence[:120] if first_sentence else raw_text[:120]


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------

async def get_lead_insight(company: str) -> str | None:
    """
    Get a personalization insight for a company.
    Priority: hardcoded map → persistent cache → Tavily live search.
    """
    if not company or not company.strip():
        return None

    # Step 1: Hardcoded map — exact and partial match
    for key, value in HARDCODED_INSIGHTS.items():
        if key.lower() in company.lower():
            return value

    # Step 2: Check persistent cache
    cache = _load_cache()
    if company in cache:
        return cache[company]

    # Step 3: Tavily live search (only if API key present)
    tavily_key = os.getenv("TAVILY_API_KEY")
    if tavily_key:
        try:
            from tavily import TavilyClient

            tavily = TavilyClient(api_key=tavily_key)
            results = tavily.search(
                query=f"{company} latest news funding product launch 2026",
                max_results=1,
                search_depth="basic",
            )
            if results.get("results"):
                raw = results["results"][0]["content"][:500]
                summary = await _summarize_to_sentence(raw)
                _save_to_cache(company, summary)  # persist immediately
                return summary
        except Exception:
            pass

    return None  # No insight found — that is fine


async def enrich_leads_batch(leads: list[dict]) -> list[dict]:
    """
    Enrich a batch of leads with company insights (async, parallel).
    Adds 'insight' key to each lead dict where available.
    """
    tasks = [get_lead_insight(lead.get("company", "")) for lead in leads]
    insights = await asyncio.gather(*tasks, return_exceptions=True)
    for lead, insight in zip(leads, insights):
        if isinstance(insight, str):
            lead["insight"] = insight
    return leads
