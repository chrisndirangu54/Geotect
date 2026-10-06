from __future__ import annotations
from uuid import uuid4
from hashlib import sha256
import json,os,tempfile,shutil
from fastapi import APIRouter,Depends,HTTPException,UploadFile,File,BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy import select,desc
from db import SessionLocal
from auth import current_user,require_permission
from governance_models import DesignBasis,AssumptionRecord,RiskRecord,EngineeringIssue,ReleasedRevision,SignatureRecord
from open_standards import diggs_export,ags_crosswalk,ifc43_geotechnical_manifest,ids_validate,stac_item,stac_catalog,sensorthings_observation,bcf_issue,opencde_container
from advanced_engineering import *
from engineering_agents import route_agent,evidence_answer,anomaly_zscore,rank_root_causes,select_models
from calibration import calibrate_scalar
from data_formats import write_geoparquet,write_zarr,inspect_copc,e57_exchange_manifest

router=APIRouter(prefix="/api/v1/standards",tags=["standards-governance"])

@router.post("/diggs/export")
async def diggs(payload:dict,user:dict=Depends(current_user)): return diggs_export(payload.get("project",{}),payload.get("boreholes",[]),payload.get("tests",[]),payload.get("geophysics",[]))
@router.post("/ags/crosswalk")
async def ags(payload:dict,user:dict=Depends(current_user)): return ags_crosswalk(payload.get("records",[]))
@router.post("/ifc43/manifest")
async def ifc43(payload:dict,user:dict=Depends(current_user)): return ifc43_geotechnical_manifest(payload.get("project",{}),payload.get("boreholes",[]),payload.get("strata",[]),payload.get("cuts",[]),payload.get("fills",[]))
@router.post("/ifc/ids/validate")
async def ids(payload:dict,user:dict=Depends(current_user)): return ids_validate(payload.get("objects",[]),payload.get("requirements",[]))
@router.post("/stac/item")
async def stacitem(payload:dict,user:dict=Depends(current_user)): return stac_item(str(payload["id"]),payload["bbox"],payload["geometry"],payload.get("assets",{}),payload.get("properties"))
@router.post("/stac/catalog")
async def staccatalog(payload:dict,user:dict=Depends(current_user)): return stac_catalog(str(payload["id"]),payload.get("items",[]))
@router.post("/sensorthings/observation")
async def sensorobs(payload:dict,user:dict=Depends(current_user)): return sensorthings_observation(str(payload["sensor_id"]),str(payload["datastream_id"]),payload.get("result"),str(payload.get("unit","")),payload.get("phenomenon_time"))
@router.post("/bcf/issue")
async def bcf(payload:dict,user:dict=Depends(current_user)): return bcf_issue(payload)
@router.post("/opencde/container")
async def cde(payload:dict,user:dict=Depends(current_user)): return opencde_container(str(payload["project_id"]),payload.get("documents",[]))

@router.post("/engineering/{tool}")
async def engineering(tool:str,payload:dict,user:dict=Depends(current_user)):
    funcs={
      "mohr_coulomb":mohr_coulomb_strength,"hoek_brown":hoek_brown_strength,"hardening_soil":hardening_soil_stiffness,
      "cam_clay":modified_cam_clay_yield,"hydro_mechanical":coupled_hydro_mechanical,"transient_groundwater":transient_diffusion,
      "unsaturated":richards_bucket,"consolidation":consolidation_time,"newmark":newmark_sliding,"rock_wedges":stereonet_wedge_sets,
      "rock_mass":rock_mass_classification,"convergence_confinement":convergence_confinement,"tailings_freeboard":tailings_freeboard,
      "inverse_velocity":inverse_velocity_failure,"pile_group":pile_group_efficiency}
    if tool not in funcs:raise HTTPException(404,"unknown engineering tool")
    try:return funcs[tool](**payload)
    except Exception as e:raise HTTPException(422,str(e))

@router.post("/agents/route")
async def agent_route(payload:dict,user:dict=Depends(current_user)): return route_agent(str(payload.get("task","")))
@router.post("/agents/evidence-answer")
async def agent_answer(payload:dict,user:dict=Depends(current_user)): return evidence_answer(str(payload.get("question","")),payload.get("evidence",[]),str(payload.get("recommendation","")),float(payload.get("confidence",0)))
@router.post("/agents/anomaly")
async def agent_anomaly(payload:dict,user:dict=Depends(current_user)): return anomaly_zscore(payload.get("series",[]),float(payload.get("threshold",3)))
@router.post("/agents/root-causes")
async def causes(payload:dict,user:dict=Depends(current_user)): return rank_root_causes(payload.get("observed",{}),payload.get("candidates",[]))
@router.post("/agents/select-models")
async def models(payload:dict,user:dict=Depends(current_user)): return select_models(payload)
@router.post("/calibrate/scalar")
async def calibrate(payload:dict,user:dict=Depends(current_user)): return calibrate_scalar(payload["observed"],payload["simulated"],float(payload["parameter_value"]),float(payload.get("elasticity",1)),payload.get("bounds"))

@router.post("/governance/design-basis")
async def create_design_basis(payload:dict,user:dict=Depends(current_user)):
    rid=str(uuid4())
    async with SessionLocal() as s:
        s.add(DesignBasis(id=rid,org_id=str(payload["org_id"]),project_id=str(payload["project_id"]),title=str(payload["title"]),content=payload.get("content",{}),updated_by=user["email"]))
        await s.commit()
    return {"id":rid,"status":"draft"}

@router.post("/governance/assumptions")
async def assumption(payload:dict,user:dict=Depends(current_user)):
    rid=str(uuid4())
    async with SessionLocal() as s:
        s.add(AssumptionRecord(id=rid,org_id=str(payload["org_id"]),project_id=str(payload["project_id"]),statement=str(payload["statement"]),basis=str(payload.get("basis","")),confidence=float(payload.get("confidence",1)),evidence_refs=payload.get("evidence_refs",[]),owner_uid=payload.get("owner_uid")))
        await s.commit()
    return {"id":rid}

@router.post("/governance/risks")
async def risk(payload:dict,user:dict=Depends(current_user)):
    rid=str(uuid4())
    async with SessionLocal() as s:
        s.add(RiskRecord(id=rid,org_id=str(payload["org_id"]),project_id=str(payload["project_id"]),title=str(payload["title"]),category=str(payload.get("category","engineering")),likelihood=float(payload.get("likelihood",0)),consequence=float(payload.get("consequence",0)),linked_objects=payload.get("linked_objects",[]),controls=payload.get("controls",[])))
        await s.commit()
    return {"id":rid,"risk_score":float(payload.get("likelihood",0))*float(payload.get("consequence",0))}

@router.post("/governance/issues")
async def issue(payload:dict,user:dict=Depends(current_user)):
    rid=str(uuid4())
    async with SessionLocal() as s:
        s.add(EngineeringIssue(id=rid,org_id=str(payload["org_id"]),project_id=str(payload["project_id"]),issue_type=str(payload.get("issue_type","issue")),title=str(payload["title"]),priority=str(payload.get("priority","normal")),viewpoint=payload.get("viewpoint",{}),linked_objects=payload.get("linked_objects",[])))
        await s.commit()
    return {"id":rid}

@router.post("/governance/releases")
async def release(payload:dict,user:dict=Depends(require_permission("projects.write_all"))):
    canonical=json.dumps(payload.get("manifest",{}),sort_keys=True,separators=(",",":")).encode();digest=sha256(canonical).hexdigest();rid=str(uuid4())
    async with SessionLocal() as s:
        s.add(ReleasedRevision(id=rid,project_id=str(payload["project_id"]),source_version=int(payload["source_version"]),digest_sha256=digest,release_state=str(payload.get("release_state","issued")),manifest=payload.get("manifest",{})))
        await s.commit()
    return {"id":rid,"digest_sha256":digest,"immutable":True}

@router.post("/governance/releases/{revision_id}/sign")
async def sign(revision_id:str,payload:dict,user:dict=Depends(current_user)):
    async with SessionLocal() as s:
        rev=await s.get(ReleasedRevision,revision_id)
        if not rev:raise HTTPException(404,"revision not found")
        sid=str(uuid4());sig=SignatureRecord(id=sid,revision_id=revision_id,signer_uid=user["uid"],signer_email=user["email"],meaning=str(payload.get("meaning","reviewed")),payload_digest=rev.digest_sha256)
        s.add(sig);rev.signed_by=[*rev.signed_by,{"signature_id":sid,"email":user["email"],"meaning":sig.meaning}];await s.commit()
    return {"signature_id":sid,"revision_id":revision_id,"digest":rev.digest_sha256,"type":"account_attestation"}

@router.get("/governance/project/{project_id}")
async def governance(project_id:str,user:dict=Depends(current_user)):
    async with SessionLocal() as s:
        assumptions=(await s.execute(select(AssumptionRecord).where(AssumptionRecord.project_id==project_id))).scalars().all()
        risks=(await s.execute(select(RiskRecord).where(RiskRecord.project_id==project_id))).scalars().all()
        issues=(await s.execute(select(EngineeringIssue).where(EngineeringIssue.project_id==project_id))).scalars().all()
        releases=(await s.execute(select(ReleasedRevision).where(ReleasedRevision.project_id==project_id).order_by(desc(ReleasedRevision.created_at)))).scalars().all()
        return {"assumptions":[{"id":x.id,"statement":x.statement,"confidence":x.confidence,"status":x.status,"evidence_refs":x.evidence_refs} for x in assumptions],
          "risks":[{"id":x.id,"title":x.title,"category":x.category,"score":x.likelihood*x.consequence,"status":x.status,"linked_objects":x.linked_objects} for x in risks],
          "issues":[{"id":x.id,"title":x.title,"type":x.issue_type,"status":x.status,"priority":x.priority} for x in issues],
          "releases":[{"id":x.id,"source_version":x.source_version,"digest":x.digest_sha256,"state":x.release_state,"signed_by":x.signed_by} for x in releases]}


@router.post("/formats/geoparquet")
async def geoparquet_export(background_tasks:BackgroundTasks,payload:dict,user:dict=Depends(current_user)):
    fd,path=tempfile.mkstemp(suffix=".parquet",prefix="geotect-");os.close(fd)
    try:
        meta=write_geoparquet(payload.get("records",[]),path)
        background_tasks.add_task(lambda: os.path.exists(path) and os.unlink(path))
        return FileResponse(path,media_type="application/vnd.apache.parquet",filename="geotect.parquet",background=background_tasks,headers={"X-GeoTect-Rows":str(meta["rows"])})
    except Exception as exc:
        if os.path.exists(path):os.unlink(path)
        raise HTTPException(422,str(exc))

@router.post("/formats/zarr")
async def zarr_export(background_tasks:BackgroundTasks,payload:dict,user:dict=Depends(current_user)):
    root=tempfile.mkdtemp(prefix="geotect-zarr-");path=os.path.join(root,"dataset.zarr")
    try:
        write_zarr(payload.get("array",[]),path,str(payload.get("name","data")),payload.get("attrs",{}))
        archive=shutil.make_archive(root,"zip",root)
        background_tasks.add_task(lambda:(shutil.rmtree(root,ignore_errors=True),os.path.exists(archive) and os.unlink(archive)))
        return FileResponse(archive,media_type="application/zip",filename="geotect-zarr.zip",background=background_tasks)
    except Exception as exc:
        shutil.rmtree(root,ignore_errors=True)
        raise HTTPException(422,str(exc))

@router.post("/formats/copc/inspect")
async def copc_inspect(file:UploadFile=File(...),user:dict=Depends(current_user)):
    suffix=os.path.splitext(file.filename or "")[1].lower()
    if suffix not in {".laz",".copc",".las"}:raise HTTPException(400,"Expected COPC/LAZ/LAS")
    tmp=tempfile.NamedTemporaryFile(suffix=suffix,delete=False)
    try:
        while chunk:=await file.read(1024*1024):tmp.write(chunk)
        tmp.close();return inspect_copc(tmp.name)
    except Exception as exc:raise HTTPException(422,str(exc))
    finally:
        try:os.unlink(tmp.name)
        except OSError:pass

@router.post("/formats/e57/manifest")
async def e57_manifest(payload:dict,user:dict=Depends(current_user)): return e57_exchange_manifest(payload.get("scans",[]))
