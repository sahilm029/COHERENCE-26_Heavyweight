"""
Synaptiq — Bland.ai Calls Router

Endpoints:
  POST /api/calls/initiate     — Trigger a Bland.ai call to a lead
  POST /webhook/bland          — Receive Bland.ai end-of-call webhook
  GET  /api/calls/history      — List all call records
"""
import os
from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models import Lead, Campaign, BlandCall, Event, CampaignLead
from services.call_service import trigger_bland_call, analyze_transcript_keywords
from services.clawbot_service import send_whatsapp
from engine.executor import event_bus

router = APIRouter(tags=["calls"])

USER_PHONE = os.getenv("USER_PHONE", "").replace("whatsapp:", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
# Demo fallback: if lead has no phone, call this number instead
DEMO_CALL_PHONE = os.getenv("DEMO_CALL_PHONE", "+917738786485")

# Try to set up Gemini for transcript analysis
try:
    from google import genai as _genai
    _gemini_client = _genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None
except Exception:
    _gemini_client = None


async def _analyze_transcript_gemini(transcript: str) -> bool:
    """Use Gemini to determine if a meeting was booked from the transcript."""
    if not _gemini_client:
        return analyze_transcript_keywords(transcript)

    prompt = (
        "You are an expert sales analyst. Read the following call transcript and determine "
        "if the lead explicitly agreed to book a meeting or briefing. "
        "Reply ONLY with the word TRUE or FALSE.\n\n"
        f"Transcript:\n{transcript}"
    )
    try:
        response = _gemini_client.models.generate_content(
            model="gemini-2.0-flash-lite",
            contents=prompt,
        )
        return "true" in response.text.strip().lower()
    except Exception as e:
        print(f"[Bland Gemini Error] {e}")
        return analyze_transcript_keywords(transcript)


# ─── POST /api/calls/initiate ──────────────────────────────────────────────
@router.post("/api/calls/initiate")
async def initiate_call(payload: dict, db: AsyncSession = Depends(get_db)):
    """
    Trigger a Bland.ai call to a lead.
    Body: { campaign_id, lead_id }  (phone taken from lead.phone)
    """
    campaign_id = payload.get("campaign_id", 1)
    lead_id = payload.get("lead_id")

    if not lead_id:
        raise HTTPException(status_code=400, detail="lead_id required")

    # Fetch lead
    lead = await db.scalar(select(Lead).where(Lead.id == lead_id))
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    to_phone = lead.phone or DEMO_CALL_PHONE
    if not to_phone:
        raise HTTPException(status_code=400, detail="No phone number available")

    # Fetch campaign for persona name
    campaign = await db.scalar(select(Campaign).where(Campaign.id == campaign_id))
    persona = campaign.persona_config or {} if campaign else {}
    agent_name = persona.get("agentName", "Synaptiq AI")

    lead_name = f"{lead.first_name} {lead.last_name}".strip() or lead.email
    company = lead.company or "your company"
    insight = lead.insight or ""

    # Trigger the call
    result = trigger_bland_call(
        to_phone=to_phone,
        lead_name=lead_name,
        company=company,
        agent_name=agent_name,
        campaign_id=campaign_id,
        lead_id=lead_id,
        insight=insight,
    )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    call_id = result["call_id"]

    # Log to BlandCall table
    bland_call = BlandCall(
        call_id=call_id,
        campaign_id=campaign_id,
        lead_id=lead_id,
        to_phone=to_phone,
        status="initiated",
    )
    db.add(bland_call)

    # Log event to campaign events
    ev = Event(
        campaign_id=campaign_id,
        lead_id=lead_id,
        node_id="bland_call",
        event_type="call_initiated",
        payload={
            "call_id": call_id,
            "to_phone": to_phone,
            "lead_name": lead_name,
            "company": company,
            "agent_name": agent_name,
        },
    )
    db.add(ev)
    await db.commit()
    await db.refresh(ev)

    # Publish to SSE
    event_bus.publish({
        "id": ev.id, "campaign_id": campaign_id, "lead_id": lead_id,
        "node_id": "bland_call", "event_type": "call_initiated",
        "payload": ev.payload,
    })

    print(f"[Calls] 📞 Call initiated — {lead_name} @ {to_phone} | call_id: {call_id}")
    return {"status": "success", "call_id": call_id, "message": f"Calling {lead_name}..."}


# ─── POST /webhook/bland ───────────────────────────────────────────────────
@router.post("/webhook/bland")
async def bland_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Bland.ai posts end-of-call payload here.
    Analyzes transcript → logs meeting_confirmed event → WhatsApp alert.
    """
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    call_id = payload.get("call_id")
    transcript = payload.get("concatenated_transcript") or payload.get("transcript") or ""
    metadata = payload.get("metadata", {})
    campaign_id = metadata.get("campaign_id", 1)
    lead_id = metadata.get("lead_id")
    lead_name = metadata.get("lead_name", "Lead")
    company = metadata.get("company", "")

    print(f"[Bland Webhook] 📩 call_id={call_id}, lead={lead_name}")

    if not call_id:
        return {"status": "ignored", "reason": "no call_id"}

    # Analyze transcript
    meeting_booked = await _analyze_transcript_gemini(transcript)
    status = "completed" if payload.get("completed") else "failed"

    # Update BlandCall record
    bland_call = await db.scalar(select(BlandCall).where(BlandCall.call_id == call_id))
    if bland_call:
        bland_call.status = status
        bland_call.transcript = transcript[:4000]  # cap length
        bland_call.meeting_booked = meeting_booked

    # Log event
    event_type = "meeting_confirmed_via_call" if meeting_booked else "call_completed"
    ev = Event(
        campaign_id=campaign_id,
        lead_id=lead_id,
        node_id="bland_call",
        event_type=event_type,
        payload={
            "call_id": call_id,
            "meeting_booked": meeting_booked,
            "status": status,
            "lead_name": lead_name,
            "company": company,
            "transcript_excerpt": transcript[-300:] if transcript else "",
        },
    )
    db.add(ev)
    await db.commit()
    if bland_call:
        await db.refresh(bland_call)
    await db.refresh(ev)

    # Publish to SSE
    event_bus.publish({
        "id": ev.id, "campaign_id": campaign_id, "lead_id": lead_id,
        "node_id": "bland_call", "event_type": event_type,
        "payload": ev.payload,
    })

    # WhatsApp notification
    if USER_PHONE:
        if meeting_booked:
            msg = (
                f"🎉 *Meeting Booked via Call!*\n"
                f"──────────────────\n"
                f"📌 {lead_name} ({company}) just agreed to a meeting!\n"
                f"📞 Call ID: {call_id}\n\n"
                f"🗣️ Transcript snippet:\n_{transcript[-200:]}_"
            )
        else:
            msg = (
                f"📞 *Call Completed*\n"
                f"──────────────────\n"
                f"Lead: {lead_name} ({company})\n"
                f"Status: {status} | Meeting booked: No\n"
                f"Call ID: {call_id}"
            )
        send_whatsapp(USER_PHONE, msg)

    return {"status": "success", "meeting_booked": meeting_booked}


# ─── GET /api/calls/history ────────────────────────────────────────────────
@router.get("/api/calls/history")
async def get_call_history(db: AsyncSession = Depends(get_db)):
    """Return all call records, newest first."""
    result = await db.execute(
        select(BlandCall).order_by(BlandCall.id.desc()).limit(50)
    )
    calls = result.scalars().all()
    return [
        {
            "id": c.id,
            "call_id": c.call_id,
            "campaign_id": c.campaign_id,
            "lead_id": c.lead_id,
            "to_phone": c.to_phone,
            "status": c.status,
            "meeting_booked": c.meeting_booked,
            "transcript": c.transcript,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in calls
    ]
