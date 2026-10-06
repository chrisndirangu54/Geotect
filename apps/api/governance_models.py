from __future__ import annotations
from datetime import datetime,timezone
from sqlalchemy import String,DateTime,JSON,Boolean,Integer,Text
from sqlalchemy.orm import Mapped,mapped_column
from db import Base
def now(): return datetime.now(timezone.utc)

class DesignBasis(Base):
    __tablename__="design_basis"
    id:Mapped[str]=mapped_column(String,primary_key=True)
    org_id:Mapped[str]=mapped_column(String,index=True)
    project_id:Mapped[str]=mapped_column(String,index=True)
    title:Mapped[str]=mapped_column(String)
    content:Mapped[dict]=mapped_column(JSON,default=dict)
    status:Mapped[str]=mapped_column(String,default="draft")
    version:Mapped[int]=mapped_column(Integer,default=1)
    updated_by:Mapped[str]=mapped_column(String)
    updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)

class AssumptionRecord(Base):
    __tablename__="assumption_records"
    id:Mapped[str]=mapped_column(String,primary_key=True)
    org_id:Mapped[str]=mapped_column(String,index=True)
    project_id:Mapped[str]=mapped_column(String,index=True)
    statement:Mapped[str]=mapped_column(Text)
    basis:Mapped[str]=mapped_column(Text,default="")
    confidence:Mapped[float]=mapped_column(default=1.0)
    status:Mapped[str]=mapped_column(String,default="open")
    evidence_refs:Mapped[list]=mapped_column(JSON,default=list)
    owner_uid:Mapped[str|None]=mapped_column(String,nullable=True)
    updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)

class RiskRecord(Base):
    __tablename__="risk_records"
    id:Mapped[str]=mapped_column(String,primary_key=True)
    org_id:Mapped[str]=mapped_column(String,index=True)
    project_id:Mapped[str]=mapped_column(String,index=True)
    title:Mapped[str]=mapped_column(String)
    category:Mapped[str]=mapped_column(String,index=True)
    likelihood:Mapped[float]=mapped_column(default=0.0)
    consequence:Mapped[float]=mapped_column(default=0.0)
    status:Mapped[str]=mapped_column(String,default="open")
    linked_objects:Mapped[list]=mapped_column(JSON,default=list)
    controls:Mapped[list]=mapped_column(JSON,default=list)
    updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)

class EngineeringIssue(Base):
    __tablename__="engineering_issues"
    id:Mapped[str]=mapped_column(String,primary_key=True)
    org_id:Mapped[str]=mapped_column(String,index=True)
    project_id:Mapped[str]=mapped_column(String,index=True)
    issue_type:Mapped[str]=mapped_column(String,index=True,default="issue")
    title:Mapped[str]=mapped_column(String)
    status:Mapped[str]=mapped_column(String,default="open")
    priority:Mapped[str]=mapped_column(String,default="normal")
    viewpoint:Mapped[dict]=mapped_column(JSON,default=dict)
    linked_objects:Mapped[list]=mapped_column(JSON,default=list)
    comments:Mapped[list]=mapped_column(JSON,default=list)
    updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)

class ReleasedRevision(Base):
    __tablename__="released_revisions"
    id:Mapped[str]=mapped_column(String,primary_key=True)
    project_id:Mapped[str]=mapped_column(String,index=True)
    source_version:Mapped[int]=mapped_column(Integer)
    digest_sha256:Mapped[str]=mapped_column(String,index=True)
    release_state:Mapped[str]=mapped_column(String,default="issued")
    signed_by:Mapped[list]=mapped_column(JSON,default=list)
    manifest:Mapped[dict]=mapped_column(JSON,default=dict)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)

class SignatureRecord(Base):
    __tablename__="signature_records"
    id:Mapped[str]=mapped_column(String,primary_key=True)
    revision_id:Mapped[str]=mapped_column(String,index=True)
    signer_uid:Mapped[str]=mapped_column(String,index=True)
    signer_email:Mapped[str]=mapped_column(String)
    meaning:Mapped[str]=mapped_column(String,default="reviewed")
    payload_digest:Mapped[str]=mapped_column(String)
    signature_type:Mapped[str]=mapped_column(String,default="account_attestation")
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
