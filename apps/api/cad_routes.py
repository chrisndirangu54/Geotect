from fastapi import APIRouter,HTTPException
from project_store import create_project,save_version,get_project,history
from geology_solids import extrude_stratum
from sections import build_fence_section,correlate_boreholes

router=APIRouter(prefix="/api/v1/cad")

@router.post("/projects")
async def create(payload:dict):
    return await create_project(str(payload.get("name","Untitled GeoTect Project")),str(payload.get("crs","EPSG:4326")),payload.get("scene"))

@router.get("/projects/{project_id}")
async def get(project_id:str,version:int|None=None):
    try:return await get_project(project_id,version)
    except KeyError:raise HTTPException(404,"project not found")

@router.post("/projects/{project_id}/versions")
async def version(project_id:str,payload:dict):
    try:return await save_version(project_id,payload.get("scene",{}),str(payload.get("message","CAD edit")),str(payload.get("author","local-user")))
    except KeyError:raise HTTPException(404,"project not found")

@router.get("/projects/{project_id}/history")
async def project_history(project_id:str):
    return await history(project_id)

@router.post("/solids/extrude")
def solid(payload:dict):
    return extrude_stratum(str(payload.get("name","Stratum")),payload["footprint"],float(payload["top_elevation_m"]),float(payload["bottom_elevation_m"]),float(payload.get("confidence",1)))

@router.post("/sections/fence")
def fence(payload:dict):
    return build_fence_section(payload["line"],payload.get("boreholes",[]))

@router.post("/boreholes/correlate")
def correlate(payload:dict):
    return correlate_boreholes(payload.get("boreholes",[]),float(payload.get("minimum_confidence",0.5)))
