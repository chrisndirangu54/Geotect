from __future__ import annotations
from datetime import datetime,timezone
from sqlalchemy import String,DateTime,JSON,Boolean,Integer,Text,UniqueConstraint
from sqlalchemy.orm import Mapped,mapped_column
from db import Base

def now(): return datetime.now(timezone.utc)

class AppUser(Base):
    __tablename__="app_users"
    uid:Mapped[str]=mapped_column(String,primary_key=True)
    email:Mapped[str]=mapped_column(String,index=True)
    display_name:Mapped[str|None]=mapped_column(String,nullable=True)
    role:Mapped[str]=mapped_column(String,default="user",index=True)
    disabled:Mapped[bool]=mapped_column(Boolean,default=False)
    permissions:Mapped[list]=mapped_column(JSON,default=list)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
    updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)

class SystemSetting(Base):
    __tablename__="system_settings"
    key:Mapped[str]=mapped_column(String,primary_key=True)
    value:Mapped[dict]=mapped_column(JSON,default=dict)
    secret:Mapped[bool]=mapped_column(Boolean,default=False)
    updated_by:Mapped[str]=mapped_column(String,default="system")
    updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)

class ApiSecret(Base):
    __tablename__="api_secrets"
    id:Mapped[int]=mapped_column(Integer,primary_key=True,autoincrement=True)
    provider:Mapped[str]=mapped_column(String,index=True)
    name:Mapped[str]=mapped_column(String)
    encrypted_value:Mapped[str]=mapped_column(Text)
    last4:Mapped[str]=mapped_column(String)
    enabled:Mapped[bool]=mapped_column(Boolean,default=True)
    updated_by:Mapped[str]=mapped_column(String)
    updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
    __table_args__=(UniqueConstraint("provider","name",name="uq_api_secret_provider_name"),)

class ModelConfig(Base):
    __tablename__="model_configs"
    task:Mapped[str]=mapped_column(String,primary_key=True)
    provider:Mapped[str]=mapped_column(String)
    model:Mapped[str]=mapped_column(String)
    parameters:Mapped[dict]=mapped_column(JSON,default=dict)
    enabled:Mapped[bool]=mapped_column(Boolean,default=True)
    updated_by:Mapped[str]=mapped_column(String)
    updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)

class AuditEvent(Base):
    __tablename__="audit_events"
    id:Mapped[int]=mapped_column(Integer,primary_key=True,autoincrement=True)
    actor_uid:Mapped[str]=mapped_column(String,index=True)
    actor_email:Mapped[str]=mapped_column(String,index=True)
    action:Mapped[str]=mapped_column(String,index=True)
    target:Mapped[str]=mapped_column(String)
    detail:Mapped[dict]=mapped_column(JSON,default=dict)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now,index=True)
