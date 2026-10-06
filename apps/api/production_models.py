from __future__ import annotations
from datetime import datetime,timezone
from sqlalchemy import String,DateTime,JSON,Integer,Float,Text,UniqueConstraint
from sqlalchemy.orm import Mapped,mapped_column
from db import Base
def now(): return datetime.now(timezone.utc)

class StacCollection(Base):
    __tablename__="stac_collections"
    id:Mapped[str]=mapped_column(String,primary_key=True)
    org_id:Mapped[str]=mapped_column(String,index=True)
    payload:Mapped[dict]=mapped_column(JSON)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
    updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)

class StacItem(Base):
    __tablename__="stac_items"
    collection_id:Mapped[str]=mapped_column(String,primary_key=True)
    id:Mapped[str]=mapped_column(String,primary_key=True)
    org_id:Mapped[str]=mapped_column(String,index=True)
    datetime_text:Mapped[str|None]=mapped_column(String,index=True,nullable=True)
    bbox:Mapped[list]=mapped_column(JSON,default=list)
    payload:Mapped[dict]=mapped_column(JSON)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
    updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)

class SensorThing(Base):
    __tablename__="sensor_things"
    id:Mapped[str]=mapped_column(String,primary_key=True)
    org_id:Mapped[str]=mapped_column(String,index=True)
    name:Mapped[str]=mapped_column(String)
    description:Mapped[str]=mapped_column(Text,default="")
    properties:Mapped[dict]=mapped_column(JSON,default=dict)
    locations:Mapped[list]=mapped_column(JSON,default=list)

class SensorDatastream(Base):
    __tablename__="sensor_datastreams"
    id:Mapped[str]=mapped_column(String,primary_key=True)
    org_id:Mapped[str]=mapped_column(String,index=True)
    thing_id:Mapped[str]=mapped_column(String,index=True)
    name:Mapped[str]=mapped_column(String)
    description:Mapped[str]=mapped_column(Text,default="")
    observation_type:Mapped[str]=mapped_column(String,default="OM_Measurement")
    unit_of_measurement:Mapped[dict]=mapped_column(JSON,default=dict)
    observed_property:Mapped[dict]=mapped_column(JSON,default=dict)
    sensor:Mapped[dict]=mapped_column(JSON,default=dict)

class SensorObservation(Base):
    __tablename__="sensor_observations"
    id:Mapped[str]=mapped_column(String,primary_key=True)
    org_id:Mapped[str]=mapped_column(String,index=True)
    datastream_id:Mapped[str]=mapped_column(String,index=True)
    phenomenon_time:Mapped[datetime]=mapped_column(DateTime(timezone=True),index=True)
    result_time:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now,index=True)
    result:Mapped[dict]=mapped_column(JSON)
    parameters:Mapped[dict]=mapped_column(JSON,default=dict)

class SchemaRegistry(Base):
    __tablename__="schema_registry"
    id:Mapped[str]=mapped_column(String,primary_key=True)
    standard:Mapped[str]=mapped_column(String,index=True)
    version:Mapped[str]=mapped_column(String,index=True)
    schema_uri:Mapped[str]=mapped_column(String)
    sha256:Mapped[str|None]=mapped_column(String,nullable=True)
    active:Mapped[bool]=mapped_column(default=True)

class SignatureProvider(Base):
    __tablename__="signature_providers"
    id:Mapped[str]=mapped_column(String,primary_key=True)
    org_id:Mapped[str]=mapped_column(String,index=True)
    provider_type:Mapped[str]=mapped_column(String)
    name:Mapped[str]=mapped_column(String)
    config:Mapped[dict]=mapped_column(JSON,default=dict)
    enabled:Mapped[bool]=mapped_column(default=True)
