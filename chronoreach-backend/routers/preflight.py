from fastapi import APIRouter
from services.preflight_ai import compute_spam_score, fix_campaign_content

router = APIRouter(prefix="/api/preflight", tags=["preflight"])


@router.post("")
async def run_preflight(payload: dict):
    """Run rule-based spam scoring on workflow nodes."""
    nodes = payload.get("nodes", [])
    result = compute_spam_score(nodes, payload.get("campaign_config"))
    return result


@router.post("/fix")
async def fix_preflight(payload: dict):
    """AI-powered content rewrite to reduce spam score."""
    nodes = payload.get("nodes", [])
    result = await fix_campaign_content(nodes, payload.get("campaign_config"))
    return result
