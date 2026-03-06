# services/copilot_service.py
"""
Synaptiq Campaign Copilot Service
Converts natural language campaign descriptions into validated workflow DAG JSON.
Uses Gemini Flash with JSON mode. Falls back to pre-built templates on failure.
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
# Fallback templates (always valid, always available)
# ---------------------------------------------------------------------------


def _uid() -> str:
    return str(uuid.uuid4())


TEMPLATE_1STEP = {
    "nodes": [
        {"id": _uid(), "node_type": "trigger", "label": "Start", "config": {}, "position_x": 0, "position_y": 300},
        {"id": _uid(), "node_type": "blocklist", "label": "Blocklist Filter", "config": {"domains": ["zoho.com", "salesforce.com", "hubspot.com"]}, "position_x": 200, "position_y": 300},
        {"id": _uid(), "node_type": "ai_message", "label": "Draft Intro Email", "config": {"step": 1}, "position_x": 400, "position_y": 300},
        {"id": _uid(), "node_type": "delay", "label": "Wait 24h", "config": {"delay_hours": 24, "min_hours": 20, "max_hours": 28}, "position_x": 600, "position_y": 300},
        {"id": _uid(), "node_type": "send_email", "label": "Send Email", "config": {}, "position_x": 800, "position_y": 300},
    ],
    "edges": [],  # Will be auto-wired
}

TEMPLATE_3STEP = {
    "nodes": [
        {"id": "t1", "node_type": "trigger", "label": "Start", "config": {}, "position_x": 0, "position_y": 300},
        {"id": "b1", "node_type": "blocklist", "label": "Blocklist Filter", "config": {"domains": ["zoho.com", "salesforce.com", "hubspot.com", "freshworks.com", "pipedrive.com"]}, "position_x": 200, "position_y": 300},
        {"id": "m1", "node_type": "ai_message", "label": "Draft Intro Email", "config": {"step": 1}, "position_x": 400, "position_y": 300},
        {"id": "d1", "node_type": "delay", "label": "Wait 24-36h", "config": {"delay_hours": 30, "min_hours": 24, "max_hours": 36}, "position_x": 600, "position_y": 300},
        {"id": "s1", "node_type": "send_email", "label": "Send Intro", "config": {}, "position_x": 800, "position_y": 300},
        {"id": "c1", "node_type": "condition", "label": "Reply received?", "config": {"check": "reply_received"}, "position_x": 1000, "position_y": 300},
        {"id": "m2", "node_type": "ai_message", "label": "Draft Follow-up", "config": {"step": 2}, "position_x": 1200, "position_y": 300},
        {"id": "d2", "node_type": "delay", "label": "Wait 36-48h", "config": {"delay_hours": 42, "min_hours": 36, "max_hours": 48}, "position_x": 1400, "position_y": 300},
        {"id": "s2", "node_type": "send_email", "label": "Send Follow-up", "config": {}, "position_x": 1600, "position_y": 300},
        {"id": "c2", "node_type": "condition", "label": "Reply received?", "config": {"check": "reply_received"}, "position_x": 1800, "position_y": 300},
        {"id": "m3", "node_type": "ai_message", "label": "Draft Final Nudge", "config": {"step": 3}, "position_x": 2000, "position_y": 300},
        {"id": "d3", "node_type": "delay", "label": "Wait 48-72h", "config": {"delay_hours": 60, "min_hours": 48, "max_hours": 72}, "position_x": 2200, "position_y": 300},
        {"id": "cb1", "node_type": "clawbot", "label": "ClawBot Alert", "config": {"threshold": 3}, "position_x": 2400, "position_y": 300},
        {"id": "s3", "node_type": "send_email", "label": "Send Final", "config": {}, "position_x": 2600, "position_y": 300},
    ],
    "edges": [
        {"source": "t1", "target": "b1"},
        {"source": "b1", "target": "m1"},
        {"source": "m1", "target": "d1"},
        {"source": "d1", "target": "s1"},
        {"source": "s1", "target": "c1"},
        {"source": "c1", "target": "m2", "condition_label": "no_reply"},
        {"source": "m2", "target": "d2"},
        {"source": "d2", "target": "s2"},
        {"source": "s2", "target": "c2"},
        {"source": "c2", "target": "m3", "condition_label": "no_reply"},
        {"source": "m3", "target": "d3"},
        {"source": "d3", "target": "cb1"},
        {"source": "cb1", "target": "s3"},
    ],
}

TEMPLATE_5STEP = {
    "nodes": [
        {"id": "t1", "node_type": "trigger", "label": "Start", "config": {}, "position_x": 0, "position_y": 300},
        {"id": "b1", "node_type": "blocklist", "label": "Blocklist Filter", "config": {"domains": ["zoho.com", "salesforce.com", "hubspot.com", "freshworks.com", "pipedrive.com"]}, "position_x": 200, "position_y": 300},
        {"id": "m1", "node_type": "ai_message", "label": "Cold Intro", "config": {"step": 1}, "position_x": 400, "position_y": 300},
        {"id": "d1", "node_type": "delay", "label": "Wait 24h", "config": {"delay_hours": 24, "min_hours": 20, "max_hours": 28}, "position_x": 600, "position_y": 300},
        {"id": "s1", "node_type": "send_email", "label": "Send #1", "config": {}, "position_x": 800, "position_y": 300},
        {"id": "c1", "node_type": "condition", "label": "Reply?", "config": {"check": "reply_received"}, "position_x": 1000, "position_y": 300},
        {"id": "m2", "node_type": "ai_message", "label": "Value Add", "config": {"step": 2}, "position_x": 1200, "position_y": 300},
        {"id": "d2", "node_type": "delay", "label": "Wait 36h", "config": {"delay_hours": 36, "min_hours": 30, "max_hours": 42}, "position_x": 1400, "position_y": 300},
        {"id": "s2", "node_type": "send_email", "label": "Send #2", "config": {}, "position_x": 1600, "position_y": 300},
        {"id": "c2", "node_type": "condition", "label": "Reply?", "config": {"check": "reply_received"}, "position_x": 1800, "position_y": 300},
        {"id": "m3", "node_type": "ai_message", "label": "Case Study", "config": {"step": 2}, "position_x": 2000, "position_y": 300},
        {"id": "d3", "node_type": "delay", "label": "Wait 48h", "config": {"delay_hours": 48, "min_hours": 42, "max_hours": 54}, "position_x": 2200, "position_y": 300},
        {"id": "s3", "node_type": "send_email", "label": "Send #3", "config": {}, "position_x": 2400, "position_y": 300},
        {"id": "c3", "node_type": "condition", "label": "Reply?", "config": {"check": "reply_received"}, "position_x": 2600, "position_y": 300},
        {"id": "m4", "node_type": "ai_message", "label": "Social Proof", "config": {"step": 2}, "position_x": 2800, "position_y": 300},
        {"id": "d4", "node_type": "delay", "label": "Wait 48h", "config": {"delay_hours": 48, "min_hours": 42, "max_hours": 54}, "position_x": 3000, "position_y": 300},
        {"id": "s4", "node_type": "send_email", "label": "Send #4", "config": {}, "position_x": 3200, "position_y": 300},
        {"id": "c4", "node_type": "condition", "label": "Reply?", "config": {"check": "reply_received"}, "position_x": 3400, "position_y": 300},
        {"id": "m5", "node_type": "ai_message", "label": "Final Nudge", "config": {"step": 3}, "position_x": 3600, "position_y": 300},
        {"id": "d5", "node_type": "delay", "label": "Wait 72h", "config": {"delay_hours": 72, "min_hours": 60, "max_hours": 84}, "position_x": 3800, "position_y": 300},
        {"id": "cb1", "node_type": "clawbot", "label": "ClawBot Alert", "config": {"threshold": 3}, "position_x": 4000, "position_y": 300},
        {"id": "s5", "node_type": "send_email", "label": "Send Final", "config": {}, "position_x": 4200, "position_y": 300},
    ],
    "edges": [
        {"source": "t1", "target": "b1"},
        {"source": "b1", "target": "m1"},
        {"source": "m1", "target": "d1"},
        {"source": "d1", "target": "s1"},
        {"source": "s1", "target": "c1"},
        {"source": "c1", "target": "m2", "condition_label": "no_reply"},
        {"source": "m2", "target": "d2"},
        {"source": "d2", "target": "s2"},
        {"source": "s2", "target": "c2"},
        {"source": "c2", "target": "m3", "condition_label": "no_reply"},
        {"source": "m3", "target": "d3"},
        {"source": "d3", "target": "s3"},
        {"source": "s3", "target": "c3"},
        {"source": "c3", "target": "m4", "condition_label": "no_reply"},
        {"source": "m4", "target": "d4"},
        {"source": "d4", "target": "s4"},
        {"source": "s4", "target": "c4"},
        {"source": "c4", "target": "m5", "condition_label": "no_reply"},
        {"source": "m5", "target": "d5"},
        {"source": "d5", "target": "cb1"},
        {"source": "cb1", "target": "s5"},
    ],
}

# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate_workflow_json(data: dict) -> tuple[bool, list[str]]:
    """
    Validate LLM-generated workflow JSON.
    Returns (is_valid, list_of_errors).
    """
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
            errors.append(
                f"Node {node.get('id', i)}: invalid node_type '{ntype}'. "
                f"Allowed: {ALLOWED_NODE_TYPES}"
            )

    for i, edge in enumerate(data.get("edges", [])):
        if edge.get("source") not in node_ids:
            errors.append(f"Edge {i}: source '{edge.get('source')}' not in node list")
        if edge.get("target") not in node_ids:
            errors.append(f"Edge {i}: target '{edge.get('target')}' not in node list")

    return len(errors) == 0, errors


# ---------------------------------------------------------------------------
# NL → Workflow JSON
# ---------------------------------------------------------------------------


@retry(stop=stop_after_attempt(2), wait=wait_exponential(min=1, max=8))
async def natural_language_to_workflow(description: str) -> dict:
    """
    Convert a natural language campaign description into a validated workflow JSON.
    Falls back to TEMPLATE_3STEP if LLM output fails validation.
    """
    try:
        prompt = f"""You are a workflow architect for Synaptiq, an AI outreach automation platform.
Convert the campaign description below into a workflow JSON.

Valid node types and their configs:
- trigger:    Always first. config: {{}}
- blocklist:  Always second. config: {{"domains": ["zoho.com","salesforce.com","hubspot.com","freshworks.com","pipedrive.com"]}}
- ai_message: config: {{"step": 1 or 2 or 3}}
- delay:      config: {{"delay_hours": int, "min_hours": int, "max_hours": int}}
- send_email: config: {{}}
- condition:  config: {{"check": "reply_received"}}
- clawbot:    config: {{"threshold": 3}}

Mandatory rules:
1. Always: trigger → blocklist → first ai_message
2. Every ai_message must be followed by: delay → send_email
3. Add condition node after final send_email
4. Campaigns > 2 steps: add clawbot before final send_email
5. All node IDs must be unique UUID v4 strings
6. Every edge source and target must exist in nodes array
7. Node positions: x increases by 200 per column, y=300 default
8. Each node must have: id, node_type, label, config, position_x, position_y
9. Each edge must have: source, target (and optionally condition_label)

Campaign: {description}

Return JSON only:
{{"nodes": [...], "edges": [...]}}"""

        response = flash_model.generate_content(
            prompt + "\n\nRespond with valid JSON only. No markdown fences. No explanation.",
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json"
            ),
        )
        result = json.loads(response.text)

        # Validate
        is_valid, errors = validate_workflow_json(result)
        if is_valid:
            return result
        else:
            print(f"[Copilot] Validation failed: {errors}. Falling back to template.")
            return TEMPLATE_3STEP

    except Exception as e:
        print(f"[Copilot] LLM failed: {e}. Falling back to TEMPLATE_3STEP.")
        return TEMPLATE_3STEP
