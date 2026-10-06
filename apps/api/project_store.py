from __future__ import annotations
from datetime import datetime,timezone
from uuid import uuid4
from sqlalchemy import String,DateTime,JSON,Integer,select,desc
from sqlalchemy.orm import Mapped,mapped_column
from db import Base,SessionLocal

class Project(Base):
    __tablename__="projects"
    id:Mapped[str]=mapped_column(String,primary_key=True)
    name:Mapped[str]=mapped_column(String,index=True)
    crs:Mapped[str]=mapped_column(String,default="EPSG:4326")
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))
    updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))

class ProjectVersion(Base):
    __tablename__="project_versions"
    project_id:Mapped[str]=mapped_column(String,primary_key=True)
    version:Mapped[int]=mapped_column(Integer,primary_key=True)
    message:Mapped[str]=mapped_column(String,default="")
    author:Mapped[str]=mapped_column(String,default="local-user")
    scene:Mapped[dict]=mapped_column(JSON)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc))

async def create_project(name:str,crs:str="EPSG:4326",scene:dict|None=None)->dict:
    pid=str(uuid4())
    async with SessionLocal() as s:
        p=Project(id=pid,name=name,crs=crs)
        s.add(p)
        s.add(ProjectVersion(project_id=pid,version=1,message="Initial project",scene=scene or {}))
        await s.commit()
    return {"id":pid,"name":name,"crs":crs,"version":1}

async def save_version(project_id:str,scene:dict,message:str="",author:str="local-user")->dict:
    async with SessionLocal() as s:
        p=await s.get(Project,project_id)
        if not p: raise KeyError(project_id)
        q=await s.execute(select(ProjectVersion.version).where(ProjectVersion.project_id==project_id).order_by(desc(ProjectVersion.version)).limit(1))
        current=q.scalar_one_or_none() or 0
        v=current+1
        s.add(ProjectVersion(project_id=project_id,version=v,message=message,author=author,scene=scene))
        p.updated_at=datetime.now(timezone.utc)
        await s.commit()
        return {"project_id":project_id,"version":v,"message":message}

async def get_project(project_id:str,version:int|None=None)->dict:
    async with SessionLocal() as s:
        p=await s.get(Project,project_id)
        if not p: raise KeyError(project_id)
        if version is None:
            q=await s.execute(select(ProjectVersion).where(ProjectVersion.project_id==project_id).order_by(desc(ProjectVersion.version)).limit(1))
        else:
            q=await s.execute(select(ProjectVersion).where(ProjectVersion.project_id==project_id,ProjectVersion.version==version))
        v=q.scalar_one_or_none()
        return {"id":p.id,"name":p.name,"crs":p.crs,"version":v.version if v else None,"scene":v.scene if v else {},"message":v.message if v else ""}

async def history(project_id:str)->list[dict]:
    async with SessionLocal() as s:
        q=await s.execute(select(ProjectVersion).where(ProjectVersion.project_id==project_id).order_by(desc(ProjectVersion.version)))
        return [{"version":v.version,"message":v.message,"author":v.author,"created_at":v.created_at.isoformat()} for v in q.scalars().all()]
