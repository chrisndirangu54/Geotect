import os
from sqlalchemy.ext.asyncio import create_async_engine,async_sessionmaker,AsyncSession
from sqlalchemy.orm import DeclarativeBase,Mapped,mapped_column
from sqlalchemy import String,Float,DateTime,JSON,func
from geoalchemy2 import Geometry

DATABASE_URL=os.getenv("DATABASE_URL","postgresql+asyncpg://geotect:geotect@db:5432/geotect")
engine=create_async_engine(DATABASE_URL,pool_pre_ping=True)
SessionLocal=async_sessionmaker(engine,expire_on_commit=False,class_=AsyncSession)

class Base(DeclarativeBase): pass

class SpatialObject(Base):
    __tablename__="spatial_objects"
    id:Mapped[str]=mapped_column(String,primary_key=True)
    site_id:Mapped[str]=mapped_column(String,index=True)
    object_type:Mapped[str]=mapped_column(String,index=True)
    state:Mapped[str]=mapped_column(String,default="measured")
    confidence:Mapped[float]=mapped_column(Float,default=1.0)
    properties:Mapped[dict]=mapped_column(JSON,default=dict)
    geom=mapped_column(Geometry(geometry_type="GEOMETRYZ",srid=4326))
    created_at=mapped_column(DateTime(timezone=True),server_default=func.now())

class TelemetryPoint(Base):
    __tablename__="telemetry_points"
    sensor_id:Mapped[str]=mapped_column(String,primary_key=True)
    observed_at=mapped_column(DateTime(timezone=True),primary_key=True)
    value:Mapped[float]=mapped_column(Float)
    unit:Mapped[str]=mapped_column(String)
    quality:Mapped[float]=mapped_column(Float,default=1.0)
    meta:Mapped[dict]=mapped_column(JSON,default=dict)

async def init_db():
    # Import mapped classes before metadata creation.
    import project_store,admin_models,platform_models,integration_models,governance_models,field_models,enterprise_models,production_models
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
