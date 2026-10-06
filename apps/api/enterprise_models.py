from __future__ import annotations
from datetime import datetime,timezone
from sqlalchemy import String,DateTime,JSON,Boolean
from sqlalchemy.orm import Mapped,mapped_column
from db import Base
def now():return datetime.now(timezone.utc)

class EnterprisePolicy(Base):
    __tablename__="enterprise_policies"
    org_id:Mapped[str]=mapped_column(String,primary_key=True)
    sso_mode:Mapped[str]=mapped_column(String,default="firebase")
    saml_metadata:Mapped[dict]=mapped_column(JSON,default=dict)
    scim_enabled:Mapped[bool]=mapped_column(Boolean,default=False)
    data_residency:Mapped[str]=mapped_column(String,default="default")
    cmek_provider:Mapped[str|None]=mapped_column(String,nullable=True)
    cmek_key_ref:Mapped[str|None]=mapped_column(String,nullable=True)
    rate_limits:Mapped[dict]=mapped_column(JSON,default=dict)
    retention:Mapped[dict]=mapped_column(JSON,default=dict)
    updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)

class MarketplaceItem(Base):
    __tablename__="marketplace_items"
    id:Mapped[str]=mapped_column(String,primary_key=True)
    publisher_org_id:Mapped[str]=mapped_column(String,index=True)
    name:Mapped[str]=mapped_column(String,index=True)
    item_type:Mapped[str]=mapped_column(String,index=True)
    version:Mapped[str]=mapped_column(String)
    manifest:Mapped[dict]=mapped_column(JSON,default=dict)
    pricing:Mapped[dict]=mapped_column(JSON,default=dict)
    published:Mapped[bool]=mapped_column(Boolean,default=False)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
