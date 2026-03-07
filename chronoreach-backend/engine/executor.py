import json
import os
import asyncio
from collections import deque
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database import AsyncSessionLocal
from models import Campaign, Lead, CampaignLead, Event, WorkflowNode, WorkflowEdge, ClawbotPending
from engine.email_sender import email_sender
from engine.safety import is_send_allowed
from services.llm_service import llm_service

# Demo mode: use short delays instead of hours
DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"
DEMO_DELAY_SECS = 3  # seconds between pipeline stages in demo

class EventBus:
    def __init__(self):
        self.queues = []

    def subscribe(self):
        q = asyncio.Queue()
        self.queues.append(q)
        return q

    def unsubscribe(self, q):
        if q in self.queues:
            self.queues.remove(q)

    def publish(self, data: dict):
        for q in list(self.queues):
            try:
                q.put_nowait(data)
            except asyncio.QueueFull:
                pass

event_bus = EventBus()

class WorkflowExecutor:
    def __init__(self, campaign_id: int, scheduler=None):
        self.campaign_id = campaign_id
        self.scheduler = scheduler
        self.nodes = {}
        self.edges = []
        self.workflow_id = None
        
    async def load_workflow(self, session: AsyncSession):
        camp = await session.get(Campaign, self.campaign_id)
        if not camp:
            return False
        self.workflow_id = camp.workflow_id
        self.safe_mode = camp.safe_mode
        self.campaign_config = {"daily_send_cap": camp.daily_send_cap, "timezone": camp.timezone}
        
        res_nodes = await session.execute(select(WorkflowNode).where(WorkflowNode.workflow_id == self.workflow_id))
        for nd in res_nodes.scalars().all():
            self.nodes[nd.id] = {"id": nd.id, "node_type": nd.node_type, "label": nd.label, "config": nd.config or {}}
            
        res_edges = await session.execute(select(WorkflowEdge).where(WorkflowEdge.workflow_id == self.workflow_id))
        self.edges = res_edges.scalars().all()
        
        print(f"[Executor] Loaded workflow {self.workflow_id}: {len(self.nodes)} nodes, {len(self.edges)} edges")
        return True

    def get_topological_order(self) -> list[str]:
        in_degree = {nid: 0 for nid in self.nodes}
        adj = {nid: [] for nid in self.nodes}
        for edge in self.edges:
            src = edge.source if hasattr(edge, 'source') else edge['source']
            tgt = edge.target if hasattr(edge, 'target') else edge['target']
            if src in adj and tgt in in_degree:
                adj[src].append(tgt)
                in_degree[tgt] += 1

        queue = deque([nid for nid, deg in in_degree.items() if deg == 0])
        order = []
        while queue:
            nid = queue.popleft()
            order.append(nid)
            for neighbor in adj[nid]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        return order

    async def execute_campaign(self):
        async with AsyncSessionLocal() as session:
            if not await self.load_workflow(session):
                print(f"[Executor] ❌ Campaign {self.campaign_id} not found or no workflow")
                return
            res = await session.execute(select(CampaignLead).where(CampaignLead.campaign_id == self.campaign_id))
            cleads = res.scalars().all()
            print(f"[Executor] Processing {len(cleads)} leads for campaign {self.campaign_id}")
            
            for cl in cleads:
                if cl.status in ("completed", "blocked"):
                    continue
                # Execute leads sequentially for demo visibility
                await self.execute_for_lead_task(cl.lead_id, cl.current_node_id)
            
            # Mark campaign completed
            camp = await session.get(Campaign, self.campaign_id)
            if camp:
                camp.status = "completed"
                await session.commit()
            
            # Publish completion event
            event_bus.publish({
                "campaign_id": self.campaign_id,
                "event_type": "campaign_completed",
                "payload": {"message": "All leads processed"},
                "created_at": datetime.utcnow().isoformat()
            })
                
    async def execute_for_lead_task(self, lead_id: int, start_node_id: str):
        async with AsyncSessionLocal() as session:
            try:
                await self.execute_for_lead(lead_id, start_node_id, session)
            except Exception as e:
                print(f"[Executor] ❌ Error executing lead {lead_id}: {e}")
                import traceback
                traceback.print_exc()

    async def execute_for_lead(self, lead_id: int, start_node_id: str, session: AsyncSession):
        if not self.nodes:
            await self.load_workflow(session)
        order = self.get_topological_order()
        
        if start_node_id:
            try:
                start_idx = order.index(start_node_id)
                order = order[start_idx:]
            except ValueError:
                pass
                
        lead = await session.get(Lead, lead_id)
        if not lead:
            print(f"[Executor] Lead {lead_id} not found, skipping")
            return
        
        print(f"[Executor] ▸ Processing lead: {lead.first_name} {lead.last_name} <{lead.email}>")
        
        for node_id in order:
            node = self.nodes.get(node_id)
            if not node:
                continue
            node_type = node["node_type"]
            
            # Small delay between each node for demo visibility
            if DEMO_MODE:
                await asyncio.sleep(1)
            
            if node_type == "trigger":
                await self._handle_trigger(node, lead, session)
            elif node_type == "blocklist":
                if await self._handle_blocklist(node, lead, session):
                    return
            elif node_type == "ai_message":
                await self._handle_ai_message(node, lead, session)
            elif node_type == "delay":
                if DEMO_MODE:
                    # Demo mode: short sleep instead of scheduling
                    await self._log_event(lead.id, node["id"], "delay_started",
                        {"demo_mode": True, "delay_seconds": DEMO_DELAY_SECS}, session)
                    await asyncio.sleep(DEMO_DELAY_SECS)
                    await self._log_event(lead.id, node["id"], "delay_completed", {}, session)
                else:
                    await self._handle_delay(node, lead, session)
                    return  # Paused for real scheduling
            elif node_type == "send_email":
                await self._handle_send_email(node, lead, session)
                # After sending the email, STOP the pipeline.
                # Post-send nodes (condition, clawbot, meeting) are handled
                # by the Demo Controls / simulation endpoints, not the executor.
                cl_stmt = select(CampaignLead).where(CampaignLead.campaign_id==self.campaign_id, CampaignLead.lead_id==lead.id)
                cl = (await session.execute(cl_stmt)).scalar_one_or_none()
                if cl:
                    cl.status = "completed"
                    cl.current_node_id = node_id
                    await session.commit()
                await self._log_event(lead.id, "done", "lead_completed",
                    {"lead_name": f"{lead.first_name} {lead.last_name}", "email": lead.email}, session)
                return
            elif node_type == "condition":
                next_node_id = await self._handle_condition(node, lead, session)
                if next_node_id:
                    await self.execute_for_lead(lead_id, next_node_id, session)
                return
            elif node_type == "clawbot":
                if await self._handle_clawbot(node, lead, session):
                    return
                
            cl_stmt = select(CampaignLead).where(CampaignLead.campaign_id==self.campaign_id, CampaignLead.lead_id==lead.id)
            cl = (await session.execute(cl_stmt)).scalar_one_or_none()
            if cl:
                cl.current_node_id = node_id
                await session.commit()
                
        cl_stmt = select(CampaignLead).where(CampaignLead.campaign_id==self.campaign_id, CampaignLead.lead_id==lead.id)
        cl = (await session.execute(cl_stmt)).scalar_one_or_none()
        if cl:
            cl.status = "completed"
            await session.commit()
            
        await self._log_event(lead.id, "done", "lead_completed",
            {"lead_name": f"{lead.first_name} {lead.last_name}", "email": lead.email}, session)

    async def _handle_trigger(self, node, lead, session):
        await self._log_event(lead.id, node["id"], "trigger_started",
            {"lead_name": f"{lead.first_name} {lead.last_name}", "company": lead.company}, session)

    async def _handle_blocklist(self, node, lead, session):
        domains = ["zoho.com", "salesforce.com", "hubspot.com", "freshworks.com", "pipedrive.com"]
        if any(d in (lead.email or "").lower() for d in domains):
            await self._log_event(lead.id, node["id"], "blocked",
                {"reason": "competitor domain", "domain": lead.email.split("@")[-1],
                 "lead_name": f"{lead.first_name} {lead.last_name}"}, session)
            cl_stmt = select(CampaignLead).where(CampaignLead.campaign_id==self.campaign_id, CampaignLead.lead_id==lead.id)
            cl = (await session.execute(cl_stmt)).scalar_one_or_none()
            if cl:
                cl.status = "blocked"
                await session.commit()
            return True
        
        await self._log_event(lead.id, node["id"], "blocklist_passed",
            {"lead_name": f"{lead.first_name} {lead.last_name}"}, session)
        return False
        
    async def _handle_ai_message(self, node, lead, session):
        step_num = node["config"].get("step", node["config"].get("step_number", 1))
        ld_dict = {
            "first_name": lead.first_name, "last_name": lead.last_name,
            "company": lead.company, "title": lead.title,
            "insight": lead.insight, "linkedin_headline": lead.linkedin_headline,
            "custom_fields": lead.custom_fields
        }
        
        print(f"[Executor] 🤖 Generating AI message step {step_num} for {lead.first_name}")
        msg = await llm_service.generate_message(ld_dict, step_num, {"tone": "casual"})
        
        cl_stmt = select(CampaignLead).where(CampaignLead.campaign_id==self.campaign_id, CampaignLead.lead_id==lead.id)
        cl = (await session.execute(cl_stmt)).scalar_one_or_none()
        if cl:
            cl.current_message = json.dumps(msg)
            await session.commit()
            
        await self._log_event(lead.id, node["id"], "message_generated", {
            "subject": msg.get("subject", ""),
            "body_preview": msg.get("body", "")[:80],
            "hooks_used": msg.get("hooks_used", []),
            "language": msg.get("language", "en"),
            "word_count": msg.get("word_count", 0),
            "lead_name": f"{lead.first_name} {lead.last_name}",
            "company": lead.company
        }, session)

    async def _handle_delay(self, node, lead, session):
        """Real delay scheduling — used when DEMO_MODE is off."""
        from engine.timing import compute_next_send_time
        from apscheduler.triggers.date import DateTrigger
        
        send_at, jitter = compute_next_send_time(node["config"], sends_today=0, campaign_day=1)
        await self._log_event(lead.id, node["id"], "scheduled",
            {"scheduled_for": send_at.isoformat(), "jitter_applied": jitter}, session)
        
        next_node_id = None
        for edge in self.edges:
            src = edge.source if hasattr(edge, 'source') else edge['source']
            tgt = edge.target if hasattr(edge, 'target') else edge['target']
            if src == node["id"]:
                next_node_id = tgt
                break
                
        if next_node_id and self.scheduler:
            def resume_callback(camp_id, l_id, n_id):
                asyncio.run(self.execute_for_lead_task(l_id, n_id))
            self.scheduler.add_job(resume_callback, trigger=DateTrigger(run_date=send_at),
                                   args=[self.campaign_id, lead.id, next_node_id])

    async def _handle_send_email(self, node, lead, session):
        # Safety: check rate limits before sending
        allowed, reason = await is_send_allowed(self.campaign_id, session)
        if not allowed:
            await self._log_event(lead.id, node["id"], "send_rate_limited", {
                "reason": reason,
                "lead_name": f"{lead.first_name} {lead.last_name}",
                "company": lead.company
            }, session)
            print(f"[Executor] 🛑 Rate limited for {lead.email}: {reason}")
            return

        cl_stmt = select(CampaignLead).where(CampaignLead.campaign_id==self.campaign_id, CampaignLead.lead_id==lead.id)
        cl = (await session.execute(cl_stmt)).scalar_one_or_none()
        msg = {}
        if cl and cl.current_message:
            try:
                msg = json.loads(cl.current_message)
            except:
                pass
            
        subject = msg.get("subject", "Quick question")
        body = msg.get("body", f"Hi {lead.first_name}, wanted to connect about what you're building at {lead.company}.")
        
        print(f"[Executor] 📧 Sending email to {lead.email}: {subject}")
        success = await email_sender.send(lead.email, subject, body,
                                           campaign_id=self.campaign_id, lead_id=lead.id)
        
        if success:
            await self._log_event(lead.id, node["id"], "email_sent", {
                "subject": subject,
                "to": lead.email,
                "lead_name": f"{lead.first_name} {lead.last_name}",
                "company": lead.company,
                "hooks_used": msg.get("hooks_used", [])
            }, session)
        else:
            await self._log_event(lead.id, node["id"], "email_failed", {
                "to": lead.email,
                "lead_name": f"{lead.first_name} {lead.last_name}"
            }, session)
            
    async def _handle_condition(self, node, lead, session):
        check = node["config"].get("check", "reply_received")
        if check == "reply_received":
            stmt = select(func.count(Event.id)).where(
                Event.campaign_id==self.campaign_id,
                Event.lead_id==lead.id,
                Event.event_type=="reply_received"
            )
            cnt = await session.scalar(stmt)
            matched_label = "replied" if cnt > 0 else "no_reply"
        else:
            matched_label = "no_reply"
            
        await self._log_event(lead.id, node["id"], "condition_evaluated", {
            "check": check, "result": matched_label,
            "lead_name": f"{lead.first_name} {lead.last_name}"
        }, session)
        
        for edge in self.edges:
            src = edge.source if hasattr(edge, 'source') else edge['source']
            tgt = edge.target if hasattr(edge, 'target') else edge['target']
            cond = edge.condition_label if hasattr(edge, 'condition_label') else edge.get('condition_label')
            if src == node["id"] and cond == matched_label:
                return tgt
        return None

    async def _handle_clawbot(self, node, lead, session):
        """Create ClawBot alert AND send WhatsApp notification."""
        # In demo mode, always trigger ClawBot for the first lead
        threshold = node["config"].get("threshold", 3)
        
        # Create pending record
        cp = ClawbotPending(
            campaign_id=self.campaign_id,
            lead_id=lead.id,
            action_type="high_intent",
            draft_message=f"Hi {lead.first_name}, noticed you've been checking out our intro. Would love to continue the conversation.",
            user_phone=os.getenv("USER_PHONE", "")
        )
        session.add(cp)
        await session.commit()
        
        # Build and send WhatsApp alert
        try:
            from services.clawbot_service import send_whatsapp, build_hot_lead_alert
            lead_dict = {
                "first_name": lead.first_name, "last_name": lead.last_name,
                "title": lead.title, "company": lead.company
            }
            alert_msg = build_hot_lead_alert(lead_dict, cp.draft_message, threshold)
            user_phone = os.getenv("USER_PHONE", "")
            if user_phone:
                # Remove 'whatsapp:' prefix if present — send_whatsapp adds it
                phone = user_phone.replace("whatsapp:", "")
                success = send_whatsapp(phone, alert_msg)
                print(f"[ClawBot] WhatsApp {'✅ sent' if success else '❌ failed'} to {phone}")
            else:
                print("[ClawBot] No USER_PHONE set, skipping WhatsApp")
        except Exception as e:
            print(f"[ClawBot] WhatsApp error: {e}")
        
        await self._log_event(lead.id, node["id"], "clawbot_triggered", {
            "threshold_met": True,
            "lead_name": f"{lead.first_name} {lead.last_name}",
            "company": lead.company,
            "whatsapp_sent": True
        }, session)
        
        # Don't halt execution in demo mode — continue pipeline
        if DEMO_MODE:
            return False
        return True

    async def _log_event(self, lead_id: int, node_id: str, event_type: str, payload: dict, session: AsyncSession):
        ev = Event(campaign_id=self.campaign_id, lead_id=lead_id, node_id=node_id,
                   event_type=event_type, payload=payload)
        session.add(ev)
        await session.commit()
        await session.refresh(ev)
        
        msg = {
            "id": ev.id, "campaign_id": self.campaign_id, "lead_id": lead_id,
            "node_id": node_id, "event_type": event_type, "payload": payload,
            "created_at": ev.created_at.isoformat()
        }
        event_bus.publish(msg)
        print(f"  [{event_type}] lead={lead_id} node={node_id}")
