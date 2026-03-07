import datetime
from sqlalchemy import Column, Integer, String, Text, ForeignKey, JSON, Float, Boolean, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from database import Base

class Lead(Base):
    __tablename__ = "leads"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, nullable=True)
    company = Column(String, nullable=True)
    title = Column(String, nullable=True)
    linkedin_headline = Column(String, nullable=True)
    custom_fields = Column(JSON, nullable=True)
    insight = Column(Text, nullable=True)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Workflow(Base):
    __tablename__ = "workflows"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class WorkflowNode(Base):
    __tablename__ = "workflow_nodes"
    
    id = Column(String, primary_key=True, index=True) # UUID/Text ID
    workflow_id = Column(Integer, ForeignKey("workflows.id"), nullable=False)
    node_type = Column(String, nullable=False) # trigger, ai_message, send_email, delay, condition, blocklist, clawbot
    label = Column(String, nullable=True)
    config = Column(JSON, nullable=True)
    position_x = Column(Float, nullable=True)
    position_y = Column(Float, nullable=True)

class WorkflowEdge(Base):
    __tablename__ = "workflow_edges"
    
    id = Column(String, primary_key=True, index=True) # UUID/Text
    workflow_id = Column(Integer, ForeignKey("workflows.id"), nullable=False)
    source = Column(String, nullable=False)
    target = Column(String, nullable=False)
    condition_label = Column(String, nullable=True)

class Campaign(Base):
    __tablename__ = "campaigns"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id"), nullable=False)
    name = Column(String, nullable=False)
    persona_config = Column(JSON, nullable=True)
    cal_url = Column(String, nullable=True)
    user_phone = Column(String, nullable=True)
    status = Column(String, default="draft")
    safe_mode = Column(Boolean, default=True)
    daily_send_cap = Column(Integer, default=50)
    timezone = Column(String, default="Asia/Kolkata")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class CampaignLead(Base):
    __tablename__ = "campaign_leads"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)
    current_node_id = Column(String, ForeignKey("workflow_nodes.id"), nullable=True)
    status = Column(String, default="pending")
    current_message = Column(Text, nullable=True)
    
    __table_args__ = (UniqueConstraint('campaign_id', 'lead_id', name='_campaign_lead_uc'),)

class Event(Base):
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)
    node_id = Column(String, nullable=True)  # Can be workflow node ID or system ID like 'tracking_pixel'
    event_type = Column(String, nullable=False)
    payload = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class ClawbotPending(Base):
    __tablename__ = "clawbot_pending"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)
    action_type = Column(String, nullable=False)
    draft_message = Column(Text, nullable=True)
    user_phone = Column(String, nullable=True)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class BlandCall(Base):
    __tablename__ = "bland_calls"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    call_id = Column(String, unique=True, index=True, nullable=False)  # Bland's call_id
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=True)
    to_phone = Column(String, nullable=False)
    status = Column(String, default="initiated")  # initiated / completed / failed
    transcript = Column(Text, nullable=True)
    meeting_booked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
