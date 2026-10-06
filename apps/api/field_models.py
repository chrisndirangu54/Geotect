from __future__ import annotations
from datetime import datetime,timezone
from sqlalchemy import String,DateTime,JSON,Boolean,Float,Text
from sqlalchemy.orm import Mapped,mapped_column
from db import Base
def now(): return datetime.now(timezone.utc)

class FieldLog(Base):
    __tablename__="field_logs"
    id:Mapped[str]=mapped_column(String,primary_key=True)
    org_id:Mapped[str]=mapped_column(String,index=True)
    project_id:Mapped[str]=mapped_column(String,index=True)
    log_type:Mapped[str]=mapped_column(String,index=True)
    geometry:Mapped[dict]=mapped_column(JSON,default=dict)
    content:Mapped[dict]=mapped_column(JSON,default=dict)
    media:Mapped[list]=mapped_column(JSON,default=list)
    created_by:Mapped[str]=mapped_column(String)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)

class SampleRecord(Base):
    __tablename__="sample_records"
    id:Mapped[str]=mapped_column(String,primary_key=True)
    org_id:Mapped[str]=mapped_column(String,index=True)
    project_id:Mapped[str]=mapped_column(String,index=True)
    sample_code:Mapped[str]=mapped_column(String,index=True)
    sample_type:Mapped[str]=mapped_column(String)
    location:Mapped[dict]=mapped_column(JSON,default=dict)
    chain:Mapped[list]=mapped_column(JSON,default=list)
    status:Mapped[str]=mapped_column(String,default="collected")
    metadata_json:Mapped[dict]=mapped_column(JSON,default=dict)
    updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)

class InstrumentCalibration(Base):
    __tablename__="instrument_calibrations"
    id:Mapped[str]=mapped_column(String,primary_key=True)
    org_id:Mapped[str]=mapped_column(String,index=True)
    instrument_id:Mapped[str]=mapped_column(String,index=True)
    instrument_type:Mapped[str]=mapped_column(String)
    certificate_ref:Mapped[str|None]=mapped_column(String,nullable=True)
    calibrated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True))
    expires_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True),nullable=True)
    calibration_data:Mapped[dict]=mapped_column(JSON,default=dict)
    created_by:Mapped[str]=mapped_column(String)
