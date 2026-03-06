import uuid
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database import get_db
from models import Campaign, CampaignLead, Event, WorkflowNode, WorkflowEdge, Lead, Workflow
from engine.executor import WorkflowExecutor
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/campaigns", tags=["campaigns"])

# Default workflow template when no copilot workflow exists
DEFAULT_WORKFLOW = {
    "nodes": [
        {"id": "t1", "node_type": "trigger", "label": "Start", "config": {}},
        {"id": "b1", "node_type": "blocklist", "label": "Blocklist Filter", "config": {"domains": ["zoho.com", "salesforce.com", "hubspot.com"]}},
        {"id": "m1", "node_type": "ai_message", "label": "Draft Intro Email", "config": {"step": 1}},
        {"id": "d1", "node_type": "delay", "label": "Wait 24-36h", "config": {"delay_hours": 30}},
        {"id": "s1", "node_type": "send_email", "label": "Send Intro", "config": {}},
    ],
    "edges": [
        {"source": "t1", "target": "b1"},
        {"source": "b1", "target": "m1"},
        {"source": "m1", "target": "d1"},
        {"source": "d1", "target": "s1"},
    ],
}

async def _ensure_campaign_exists(camp_id: int, db: AsyncSession):
    """Auto-create workflow + campaign + campaign_leads if they don't exist."""
    camp = await db.get(Campaign, camp_id)
    if camp:
        # Check if it has campaign_leads — if not, add them
        cl_count = await db.scalar(select(func.count(CampaignLead.id)).where(CampaignLead.campaign_id == camp_id))
        if cl_count == 0:
            leads_res = await db.execute(select(Lead))
            all_leads = leads_res.scalars().all()
            for ld in all_leads:
                db.add(CampaignLead(campaign_id=camp_id, lead_id=ld.id, status="pending"))
            await db.commit()
            print(f"[Campaign] Added {len(all_leads)} leads to existing campaign {camp_id}")
        return camp
    
    print(f"[Campaign] Campaign {camp_id} not found, auto-creating...")
    
    # Check if a copilot-saved workflow exists (id=1)
    existing_wf = await db.get(Workflow, 1)
    if existing_wf:
        wf_id = existing_wf.id
        # Check if it has nodes
        node_count = await db.scalar(select(func.count(WorkflowNode.id)).where(WorkflowNode.workflow_id == wf_id))
        if node_count == 0:
            # Add default nodes
            wf_data = DEFAULT_WORKFLOW
            for nd in wf_data["nodes"]:
                db.add(WorkflowNode(
                    id=nd["id"], workflow_id=wf_id, node_type=nd["node_type"],
                    label=nd["label"], config=nd["config"]
                ))
            for ed in wf_data["edges"]:
                db.add(WorkflowEdge(
                    id=str(uuid.uuid4()), workflow_id=wf_id,
                    source=ed["source"], target=ed["target"],
                    condition_label=ed.get("condition_label")
                ))
            await db.commit()
    else:
        # Create new workflow from template
        wf = Workflow(name="Auto-generated Campaign", description="Created automatically on launch")
        db.add(wf)
        await db.flush()
        wf_id = wf.id
        
        wf_data = DEFAULT_WORKFLOW
        for nd in wf_data["nodes"]:
            db.add(WorkflowNode(
                id=nd["id"], workflow_id=wf_id, node_type=nd["node_type"],
                label=nd["label"], config=nd["config"]
            ))
        for ed in wf_data["edges"]:
            db.add(WorkflowEdge(
                id=str(uuid.uuid4()), workflow_id=wf_id,
                source=ed["source"], target=ed["target"],
                condition_label=ed.get("condition_label")
            ))
        await db.commit()
    
    # Create campaign
    camp = Campaign(
        id=camp_id, name="Synaptiq Campaign", workflow_id=wf_id,
        status="draft", safe_mode=True
    )
    db.add(camp)
    await db.flush()
    
    # Add all leads as campaign_leads
    leads_res = await db.execute(select(Lead))
    all_leads = leads_res.scalars().all()
    for ld in all_leads:
        db.add(CampaignLead(campaign_id=camp_id, lead_id=ld.id, status="pending"))
    
    await db.commit()
    print(f"[Campaign] Created campaign {camp_id} with workflow {wf_id} and {len(all_leads)} leads")
    return camp


@router.post("")
async def create_campaign(payload: dict, db: AsyncSession = Depends(get_db)):
    camp = Campaign(
        name=payload["name"],
        workflow_id=payload["workflow_id"],
        persona_config=payload.get("persona_config"),
        cal_url=payload.get("cal_url"),
        user_phone=payload.get("user_phone")
    )
    db.add(camp)
    await db.commit()
    await db.refresh(camp)
    
    lead_ids = payload.get("lead_ids", [])
    for lid in lead_ids:
        db.add(CampaignLead(campaign_id=camp.id, lead_id=lid))
        
    await db.commit()
    return {"id": camp.id}

@router.post("/{camp_id}/launch")
async def launch_campaign(camp_id: int, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    # Auto-create campaign + workflow + leads if needed
    camp = await _ensure_campaign_exists(camp_id, db)
    camp.status = 'running'
    await db.commit()
    
    from main import scheduler
    executor = WorkflowExecutor(camp_id, scheduler)
    
    async def exec_async():
        await executor.execute_campaign()
        
    def exec_sync():
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(exec_async())
        loop.close()
        
    background_tasks.add_task(exec_sync)
    return {"status": "launching", "campaign_id": camp_id}

@router.get("/{camp_id}/status")
async def get_c_status(camp_id: int, db: AsyncSession = Depends(get_db)):
    camp = await db.get(Campaign, camp_id)
    if not camp:
        # Return empty status if campaign doesn't exist yet
        return {"status": "not_started", "total_leads": 0, "sent": 0, "opened": 0, "replied": 0, "blocked": 0, "meetings_booked": 0, "errors": 0, "leads": []}
    
    total_leads = await db.scalar(select(func.count(CampaignLead.id)).where(CampaignLead.campaign_id==camp_id))
    sent = await db.scalar(select(func.count(Event.id)).where(Event.campaign_id==camp_id, Event.event_type=="email_sent"))
    opened = await db.scalar(select(func.count(Event.id)).where(Event.campaign_id==camp_id, Event.event_type=="email_opened"))
    replied = await db.scalar(select(func.count(Event.id)).where(Event.campaign_id==camp_id, Event.event_type=="reply_received"))
    blocked = await db.scalar(select(func.count(Event.id)).where(Event.campaign_id==camp_id, Event.event_type=="blocked"))
    booked = await db.scalar(select(func.count(Event.id)).where(Event.campaign_id==camp_id, Event.event_type=="meeting_booked"))
    errors = await db.scalar(select(func.count(Event.id)).where(Event.campaign_id==camp_id, Event.event_type=="email_failed"))
    
    res = await db.execute(select(CampaignLead).where(CampaignLead.campaign_id==camp_id))
    cls = res.scalars().all()
    leads_out = []
    for cl in cls:
        ld = await db.get(Lead, cl.lead_id)
        if ld:
            leads_out.append({
                "id": ld.id, "name": f"{ld.first_name} {ld.last_name}".strip() or ld.email,
                "company": ld.company, "email": ld.email,
                "current_stage": cl.current_node_id, "status": cl.status
            })
        
    return {
        "status": camp.status, "total_leads": total_leads, "sent": sent,
        "opened": opened, "replied": replied, "blocked": blocked, 
        "meetings_booked": booked, "errors": errors, "leads": leads_out,
        "lead_progress": leads_out
    }

@router.get("/{camp_id}/heatmap")
async def get_c_heatmap(camp_id: int, db: AsyncSession = Depends(get_db)):
    now = datetime.utcnow()
    cells = []
    
    res = await db.execute(select(Event).where(Event.campaign_id==camp_id, Event.event_type.in_(["scheduled", "email_sent"])))
    events = res.scalars().all()
    
    for i in range(96):
        start = now + timedelta(minutes=30*i)
        end = start + timedelta(minutes=30)
        status = "empty"
        count = 0
        for e in events:
            t = e.created_at
            try:
                if e.event_type == "scheduled" and "scheduled_for" in e.payload:
                    t = datetime.fromisoformat(e.payload["scheduled_for"])
            except: pass
            if start <= t < end:
                count += 1
                status = "scheduled" if e.event_type == "scheduled" else "sent"
        cells.append({"window_start": start.isoformat(), "count": count, "status": status})
        
    return cells

@router.get("/{camp_id}/autopsy")
async def autopsy(camp_id: int, db: AsyncSession = Depends(get_db)):
    sent = await db.scalar(select(func.count(Event.id)).where(Event.campaign_id==camp_id, Event.event_type=="email_sent"))
    booked = await db.scalar(select(func.count(Event.id)).where(Event.campaign_id==camp_id, Event.event_type=="meeting_booked"))
    blocked = await db.scalar(select(func.count(Event.id)).where(Event.campaign_id==camp_id, Event.event_type=="blocked"))
    clawbot = await db.scalar(select(func.count(Event.id)).where(Event.campaign_id==camp_id, Event.event_type=="clawbot_triggered"))
    total = await db.scalar(select(func.count(CampaignLead.id)).where(CampaignLead.campaign_id==camp_id))
    
    return {
        "leads_processed": total,
        "emails_sent": sent,
        "blocked_competitor": blocked,
        "meetings_booked": booked,
        "clawbot_interventions": clawbot,
        "human_hours_saved": round((sent or 0) * 0.06, 1)
    }
