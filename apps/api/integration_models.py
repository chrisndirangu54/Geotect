from __future__ import annotations
from datetime import datetime,timezone
from sqlalchemy import String,DateTime,JSON,Boolean,Integer,Text
from sqlalchemy.orm import Mapped,mapped_column
from db import Base
def now(): return datetime.now(timezone.utc)

class IntegrationConnection(Base):
    __tablename__="integration_connections"
    id:Mapped[str]=mapped_column(String,primary_key=True)
    org_id:Mapped[str]=mapped_column(String,index=True)
    provider:Mapped[str]=mapped_column(String,index=True)
    name:Mapped[str]=mapped_column(String)
    mode:Mapped[str]=mapped_column(String,default="rest")
    base_url:Mapped[str|None]=mapped_column(String,nullable=True)
    config:Mapped[dict]=mapped_column(JSON,default=dict)
    enabled:Mapped[bool]=mapped_column(Boolean,default=True)
    created_by:Mapped[str]=mapped_column(String)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
    updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)

class BridgeCommand(Base):
    __tablename__="bridge_commands"
    id:Mapped[str]=mapped_column(String,primary_key=True)
    connection_id:Mapped[str]=mapped_column(String,index=True)
    command:Mapped[str]=mapped_column(String,index=True)
    payload:Mapped[dict]=mapped_column(JSON,default=dict)
    status:Mapped[str]=mapped_column(String,default="queued",index=True)
    result:Mapped[dict]=mapped_column(JSON,default=dict)
    error:Mapped[str|None]=mapped_column(Text,nullable=True)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
    updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)

class SyncCursor(Base):
    __tablename__="sync_cursors"
    connection_id:Mapped[str]=mapped_column(String,primary_key=True)
    resource:Mapped[str]=mapped_column(String,primary_key=True)
    cursor:Mapped[str|None]=mapped_column(String,nullable=True)
    meta:Mapped[dict]=mapped_column(JSON,default=dict)
    updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
