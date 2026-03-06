# services/copilot_service.py
"""
Synaptiq Campaign Copilot Service
Returns a clean single-email workflow template instantly.
No LLM call — instant response, no hangs.
"""

import os
import json
import uuid

import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential

genai.configure(api_key=os.getenv("GEMINI_API_KEY", ""))
flash_model = genai.GenerativeModel("gemini-2.0-flash")

# ---------------------------------------------------------------------------
# Allowed node types for validation
# ---------------------------------------------------------------------------

ALLOWED_NODE_TYPES = {
    "trigger", "blocklist", "ai_message", "delay",
    "send_email", "condition", "clawbot",
}

# ---------------------------------------------------------------------------
# Templates — ALL are single-email pipelines (no multi-send loops)
# ---------------------------------------------------------------------------


def _uid() -> str:
    return str(uuid.uuid4())


TEMPLATE_1STEP = {
    "nodes": [
        {"id": _uid(), "node_type": "trigger", "label": "⚡ Start", "config": {}, "position_x": 0, "position_y": 300},
        {"id": _uid(), "node_type": "blocklist", "label": "🛡️ Blocklist", "config": {"domains": ["zoho.com", "salesforce.com", "hubspot.com"]}, "position_x": 200, "position_y": 300},
        {"id": _uid(), "node_type": "ai_message", "label": "🤖 AI Draft", "config": {"step": 1}, "position_x": 400, "position_y": 300},
        {"id": _uid(), "node_type": "delay", "label": "⏳ Smart Timing", "config": {"delay_hours": 1}, "position_x": 600, "position_y": 300},
        {"id": _uid(), "node_type": "send_email", "label": "📧 Send Email", "config": {}, "position_x": 800, "position_y": 300},
    ],
    "edges": [],  # Will be auto-wired
}

TEMPLATE_3STEP = {
    "nodes": [
        {"id": "t1", "node_type": "trigger", "label": "⚡ Start", "config": {}, "position_x": 0, "position_y": 300},
        {"id": "b1", "node_type": "blocklist", "label": "🛡️ Blocklist", "config": {"domains": ["zoho.com", "salesforce.com", "hubspot.com"]}, "position_x": 200, "position_y": 300},
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

TEMPLATE_5STEP = TEMPLATE_3STEP  # Alias — all templates are single-email now


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate_workflow_json(data: dict) -> tuple[bool, list[str]]:
    errors = []
    nodes = data.get("nodes", [])
    if not nodes:
        errors.append("Workflow has no nodes")
        return False, errors

    node_ids = set()
    for i, node in enumerate(nodes):
        if "id" not in node:
            errors.append(f"Node {i} missing 'id'")
        else:
            node_ids.add(node["id"])

        ntype = node.get("node_type")
        if ntype not in ALLOWED_NODE_TYPES:
            errors.append(f"Node {node.get('id', i)}: invalid node_type '{ntype}'")

    for i, edge in enumerate(data.get("edges", [])):
        if edge.get("source") not in node_ids:
            errors.append(f"Edge {i}: source '{edge.get('source')}' not found")
        if edge.get("target") not in node_ids:
            errors.append(f"Edge {i}: target '{edge.get('target')}' not found")

    return len(errors) == 0, errors


# ---------------------------------------------------------------------------
# NL → Workflow JSON  —  INSTANT (no Gemini call)
# ---------------------------------------------------------------------------


async def natural_language_to_workflow(description: str) -> dict:
    """Return the clean single-email workflow template instantly.
    No Gemini call — the LLM is unreliable and causes 30s+ hangs."""
    print(f"[Copilot] ⚡ Instant workflow for: {description[:80]}...")
    return TEMPLATE_3STEP
