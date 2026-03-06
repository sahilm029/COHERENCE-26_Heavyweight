# services/preflight_ai.py
"""
Synaptiq Preflight AI Service
Pre-launch spam/compliance analysis with risk scoring and AI-powered Fix It.
Scoring is pure rule-based Python (no LLM) for reliability.
Fix It uses Gemini Flash-Lite for content rewriting.
"""

import os
import json
from pathlib import Path

# ---------------------------------------------------------------------------
# Spam phrase blacklist
# ---------------------------------------------------------------------------

SPAM_PHRASES = [
    "buy now", "limited offer", "act fast", "click here",
    "free trial", "don't miss", "guaranteed", "no risk",
    "make money", "winner", "congratulations", "urgent",
    "exclusive deal", "special offer", "100% free",
    "risk-free", "incredible deal", "amazing offer",
    "instant approval", "you've been selected", "last chance",
]

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"

# ---------------------------------------------------------------------------
# Recommendation builder
# ---------------------------------------------------------------------------


def _build_recommendation(risk: str, issues: list[dict]) -> str:
    """Build a human-readable recommendation based on risk level and issues."""
    if risk == "LOW":
        return "✅ Campaign looks clean. Safe to launch."

    issue_types = set(i.get("type", "") for i in issues)
    recommendations = []

    if "spam_phrase" in issue_types:
        recommendations.append("Remove or rephrase flagged spam trigger words")
    if "excessive_caps" in issue_types:
        recommendations.append("Reduce ALL CAPS words — they trigger spam filters")
    if "too_many_links" in issue_types:
        recommendations.append("Limit to 1–2 links per email maximum")
    if "exclamation_overuse" in issue_types:
        recommendations.append("Reduce exclamation marks to 1 or fewer per email")
    if "too_long" in issue_types:
        recommendations.append("Shorten emails to under 150 words for better engagement")
    if "gap_too_small" in issue_types:
        recommendations.append("Increase delay between emails to at least 24 hours")
    if "too_many_touches" in issue_types:
        recommendations.append("Reduce to 3–4 touches maximum per sequence")

    prefix = "⚠️ MEDIUM RISK" if risk == "MEDIUM" else "🚨 HIGH RISK"
    return f"{prefix}. Recommended fixes:\n" + "\n".join(
        f"  • {r}" for r in recommendations
    )


# ---------------------------------------------------------------------------
# Core scoring function (NO LLM — pure rule-based)
# ---------------------------------------------------------------------------


def compute_spam_score(nodes: list, campaign_config: dict = None) -> dict:
    """
    Analyze workflow nodes for spam risk factors.
    Returns risk score, risk level, list of issues, and recommendation.
    """
    score = 0.0
    issues = []

    message_nodes = [n for n in nodes if n.get("node_type") == "ai_message"]
    delay_nodes = [n for n in nodes if n.get("node_type") == "delay"]

    # --- Content checks per message node ---
    for node in message_nodes:
        body = node.get("config", {}).get("preview_body", "")
        node_id = node.get("id", "unknown")

        if not body:
            continue

        # Spam phrase detection
        for phrase in SPAM_PHRASES:
            if phrase.lower() in body.lower():
                score += 2.0
                issues.append({
                    "type": "spam_phrase",
                    "text": phrase,
                    "node_id": node_id,
                })

        # Excessive CAPS
        caps_words = [w for w in body.split() if w.isupper() and len(w) > 2]
        if len(caps_words) > 3:
            score += 1.5
            issues.append({
                "type": "excessive_caps",
                "count": len(caps_words),
                "node_id": node_id,
            })

        # Link density
        link_count = body.lower().count("http")
        if link_count > 2:
            score += 1.5 * (link_count - 2)
            issues.append({
                "type": "too_many_links",
                "count": link_count,
                "node_id": node_id,
            })

        # Exclamation overuse
        excl_count = body.count("!")
        if excl_count > 2:
            score += 1.0
            issues.append({
                "type": "exclamation_overuse",
                "count": excl_count,
                "node_id": node_id,
            })

        # Email too long
        word_count = len(body.split())
        if word_count > 200:
            score += 1.0
            issues.append({
                "type": "too_long",
                "word_count": word_count,
                "node_id": node_id,
            })

    # --- Cadence checks ---
    for node in delay_nodes:
        hrs = node.get("config", {}).get("delay_hours", 24)
        node_id = node.get("id", "unknown")
        if hrs < 12:
            score += 2.5
            issues.append({
                "type": "gap_too_small",
                "hours": hrs,
                "node_id": node_id,
            })

    # Too many touches
    if len(message_nodes) > 5:
        score += 2.0
        issues.append({"type": "too_many_touches", "count": len(message_nodes)})

    # --- Risk level ---
    if score <= 3:
        risk = "LOW"
    elif score <= 6:
        risk = "MEDIUM"
    else:
        risk = "HIGH"

    return {
        "score": round(score, 1),
        "risk": risk,
        "issues": issues,
        "recommendation": _build_recommendation(risk, issues),
    }


# ---------------------------------------------------------------------------
# Fix It — AI content rewriter
# ---------------------------------------------------------------------------


async def fix_campaign_content(nodes: list, campaign_config: dict = None) -> dict:
    """
    Fix all flagged nodes by rewriting content via LLM.
    Returns updated nodes list + new score after re-scoring.
    """
    from services.llm_service import fix_message

    # First, score to find issues
    initial_result = compute_spam_score(nodes, campaign_config)

    if initial_result["risk"] == "LOW":
        return {
            "nodes": nodes,
            "score_before": initial_result["score"],
            "score_after": initial_result["score"],
            "fixes_applied": 0,
        }

    # Group issues by node_id
    flagged_nodes = {}
    for issue in initial_result["issues"]:
        nid = issue.get("node_id")
        if nid:
            flagged_nodes.setdefault(nid, []).append(issue["type"])

    # Fix each flagged node
    fixes_applied = 0
    for node in nodes:
        nid = node.get("id")
        if nid in flagged_nodes and node.get("node_type") == "ai_message":
            body = node.get("config", {}).get("preview_body", "")
            if body:
                issue_types = flagged_nodes[nid]
                fixed_body = await fix_message(body, issue_types)
                node["config"]["preview_body"] = fixed_body
                fixes_applied += 1

    # Re-score after fixes
    new_result = compute_spam_score(nodes, campaign_config)

    return {
        "nodes": nodes,
        "score_before": initial_result["score"],
        "score_after": new_result["score"],
        "risk_before": initial_result["risk"],
        "risk_after": new_result["risk"],
        "fixes_applied": fixes_applied,
    }
