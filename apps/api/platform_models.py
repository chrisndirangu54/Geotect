from __future__ import annotations
from datetime import datetime,timezone
from sqlalchemy import String,DateTime,JSON,Boolean,Integer,Float,Text
from sqlalchemy.orm import Mapped,mapped_column
from db import Base
def now(): return datetime.now(timezone.utc)

class Organization(Base):
    __tablename__="organizations"
    id:Mapped[str]=mapped_column(String,primary_key=True)
    name:Mapped[str]=mapped_column(String,index=True)
    plan:Mapped[str]=mapped_column(String,default="free")
    settings:Mapped[dict]=mapped_column(JSON,default=dict)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)

class Membership(Base):
    __tablename__="memberships"
    org_id:Mapped[str]=mapped_column(String,primary_key=True)
    uid:Mapped[str]=mapped_column(String,primary_key=True)
    role:Mapped[str]=mapped_column(String,default="member")
    permissions:Mapped[list]=mapped_column(JSON,default=list)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)

class Asset(Base):
    __tablename__="assets"
    id:Mapped[str]=mapped_column(String,primary_key=True)
    org_id:Mapped[str]=mapped_column(String,index=True)
    project_id:Mapped[str|None]=mapped_column(String,index=True,nullable=True)
    name:Mapped[str]=mapped_column(String)
    asset_type:Mapped[str]=mapped_column(String,index=True)
    geometry:Mapped[dict]=mapped_column(JSON,default=dict)
    properties:Mapped[dict]=mapped_column(JSON,default=dict)
    health_score:Mapped[float]=mapped_column(Float,default=1.0)
    status:Mapped[str]=mapped_column(String,default="normal")
    updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)

class WorkflowItem(Base):
    __tablename__="workflow_items"
    id:Mapped[str]=mapped_column(String,primary_key=True)
    org_id:Mapped[str]=mapped_column(String,index=True)
    project_id:Mapped[str|None]=mapped_column(String,index=True,nullable=True)
    item_type:Mapped[str]=mapped_column(String,index=True)
    title:Mapped[str]=mapped_column(String)
    state:Mapped[str]=mapped_column(String,default="draft")
    assigned_to:Mapped[str|None]=mapped_column(String,nullable=True)
    payload:Mapped[dict]=mapped_column(JSON,default=dict)
    history:Mapped[list]=mapped_column(JSON,default=list)
    updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)

class EventRecord(Base):
    __tablename__="event_records"
    id:Mapped[str]=mapped_column(String,primary_key=True)
    org_id:Mapped[str]=mapped_column(String,index=True)
    project_id:Mapped[str|None]=mapped_column(String,index=True,nullable=True)
    event_type:Mapped[str]=mapped_column(String,index=True)
    severity:Mapped[str]=mapped_column(String,default="info")
    payload:Mapped[dict]=mapped_column(JSON,default=dict)
    acknowledged:Mapped[bool]=mapped_column(Boolean,default=False)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now,index=True)

class ComputeJob(Base):
    __tablename__="compute_jobs"
    id:Mapped[str]=mapped_column(String,primary_key=True)
    org_id:Mapped[str]=mapped_column(String,index=True)
    project_id:Mapped[str|None]=mapped_column(String,index=True,nullable=True)
    job_type:Mapped[str]=mapped_column(String,index=True)
    status:Mapped[str]=mapped_column(String,default="queued",index=True)
    input:Mapped[dict]=mapped_column(JSON,default=dict)
    output:Mapped[dict]=mapped_column(JSON,default=dict)
    progress:Mapped[float]=mapped_column(Float,default=0.0)
    created_by:Mapped[str]=mapped_column(String)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
    updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)

class PluginRegistration(Base):
    __tablename__="plugin_registrations"
    id:Mapped[str]=mapped_column(String,primary_key=True)
    name:Mapped[str]=mapped_column(String,index=True)
    version:Mapped[str]=mapped_column(String)
    category:Mapped[str]=mapped_column(String,index=True)
    endpoint:Mapped[str|None]=mapped_column(String,nullable=True)
    capabilities:Mapped[list]=mapped_column(JSON,default=list)
    enabled:Mapped[bool]=mapped_column(Boolean,default=True)
    config:Mapped[dict]=mapped_column(JSON,default=dict)

class UsageLedger(Base):
    __tablename__="usage_ledger"
    id:Mapped[int]=mapped_column(Integer,primary_key=True,autoincrement=True)
    org_id:Mapped[str]=mapped_column(String,index=True)
    meter:Mapped[str]=mapped_column(String,index=True)
    quantity:Mapped[float]=mapped_column(Float)
    meta:Mapped[dict]=mapped_column(JSON,default=dict)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now,index=True)
