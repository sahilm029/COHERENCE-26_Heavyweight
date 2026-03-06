import uuid
from fastapi import APIRouter, File, UploadFile, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from database import get_db
from models import Workflow, WorkflowNode, WorkflowEdge
from services.llm_service import llm_service

router = APIRouter(prefix="/api/copilot", tags=["copilot"])

@router.post("")
async def generate_workflow(payload: dict, db: AsyncSession = Depends(get_db)):
    desc = payload.get("description") or payload.get("prompt") or ""
    wf_json = await llm_service.natural_language_to_workflow(desc)
    
    # Save workflow to DB so launch can use it
    try:
        # Check if workflow 1 exists
        existing = await db.get(Workflow, 1)
        if existing:
            wf_id = existing.id
            # Clear old nodes and edges
            await db.execute(delete(WorkflowEdge).where(WorkflowEdge.workflow_id == wf_id))
            await db.execute(delete(WorkflowNode).where(WorkflowNode.workflow_id == wf_id))
        else:
            wf = Workflow(name="Copilot Campaign", description=desc[:200])
            db.add(wf)
            await db.flush()
            wf_id = wf.id
        
        # Save nodes
        for nd in wf_json.get("nodes", []):
            node_id = nd.get("id") or str(uuid.uuid4())
            db.add(WorkflowNode(
                id=node_id, workflow_id=wf_id,
                node_type=nd["node_type"], label=nd.get("label", nd["node_type"]),
                config=nd.get("config", {}),
                position_x=nd.get("position_x"), position_y=nd.get("position_y")
            ))
        
        # Save edges
        for ed in wf_json.get("edges", []):
            db.add(WorkflowEdge(
                id=str(uuid.uuid4()), workflow_id=wf_id,
                source=ed["source"], target=ed["target"],
                condition_label=ed.get("condition_label")
            ))
        
        await db.commit()
        print(f"[Copilot] ✅ Saved workflow {wf_id}: {len(wf_json.get('nodes', []))} nodes, {len(wf_json.get('edges', []))} edges")
    except Exception as e:
        print(f"[Copilot] ❌ Failed to save workflow: {e}")
        import traceback
        traceback.print_exc()
    
    return wf_json

@router.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    audio_bytes = await file.read()
    res = await llm_service.transcribe_voice(audio_bytes)
    return res
