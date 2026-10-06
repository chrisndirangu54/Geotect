from __future__ import annotations
from datetime import datetime,timezone
from uuid import uuid4
from fastapi import APIRouter,Depends,HTTPException,Response
from sqlalchemy import select,desc
from db import SessionLocal
from auth import current_user,require_permission
from platform_models import Organization,Membership,Asset,WorkflowItem,EventRecord,ComputeJob,PluginRegistration,UsageLedger
from probabilistic import monte_carlo_slope,conditional_idw
from investigation import recommend_locations,choose_method
from design_tools import bearing_capacity,elastic_settlement,retaining_wall,pile_capacity,liquefaction_screening
from risk_automation import evaluate_rules
from copilot import interpret_command,explain_risk
from asset_health import compute_health,failure_modes
from field_sync import merge_offline_records
from interoperability import export_geojson,export_landxml_alignment,ifc_manifest
from reporting import engineering_report,borehole_log
from notifications import dispatch
from domain_templates import TEMPLATES,template

router=APIRouter(prefix="/api/v1/platform",tags=["platform"])

@router.get("/capabilities")
async def capabilities(user:dict=Depends(current_user)):
    return {"ai":["cad_copilot","risk_explanation","investigation_planning"],"engineering":["bearing_capacity","settlement","retaining_wall","pile_capacity","liquefaction"],
      "probabilistic":["monte_carlo_slope","conditional_spatial_estimation"],"digital_twin":["4d_events","asset_health","automated_rules","emergency_mode"],
      "enterprise":["organizations","memberships","approvals","client_portals","usage_metering","plugins"],"field":["offline_sync","drone_manifest","satellite_manifest"],
      "domains":list(TEMPLATES),"interop":["GeoJSON","LandXML","IFC_manifest"],"notifications":["webhook","email","sms","whatsapp","slack","teams"]}

@router.post("/organizations")
async def create_org(payload:dict,user:dict=Depends(current_user)):
    oid=str(uuid4())
    async with SessionLocal() as s:
        s.add(Organization(id=oid,name=str(payload.get("name","GeoTect Organization")),plan=str(payload.get("plan","free")),settings=payload.get("settings",{})))
        s.add(Membership(org_id=oid,uid=user["uid"],role="owner",permissions=["*"]))
        await s.commit()
    return {"id":oid,"name":payload.get("name","GeoTect Organization"),"role":"owner"}

@router.get("/organizations")
async def list_orgs(user:dict=Depends(current_user)):
    async with SessionLocal() as s:
        memberships=(await s.execute(select(Membership).where(Membership.uid==user["uid"]))).scalars().all()
        ids=[m.org_id for m in memberships]
        rows=(await s.execute(select(Organization).where(Organization.id.in_(ids)))).scalars().all() if ids else []
        return [{"id":o.id,"name":o.name,"plan":o.plan,"settings":o.settings} for o in rows]

@router.post("/assets")
async def create_asset(payload:dict,user:dict=Depends(current_user)):
    aid=str(payload.get("id") or uuid4())
    async with SessionLocal() as s:
        s.add(Asset(id=aid,org_id=str(payload["org_id"]),project_id=payload.get("project_id"),name=str(payload["name"]),asset_type=str(payload["asset_type"]),
                    geometry=payload.get("geometry",{}),properties=payload.get("properties",{}),health_score=float(payload.get("health_score",1)),status=str(payload.get("status","normal"))))
        await s.commit()
    return {"id":aid}

@router.post("/assets/health")
async def health(payload:dict,user:dict=Depends(current_user)):
    return compute_health(payload.get("asset",{}),payload.get("observations",[]))

@router.get("/assets/failure-modes/{asset_type}")
async def modes(asset_type:str,user:dict=Depends(current_user)): return {"asset_type":asset_type,"failure_modes":failure_modes(asset_type)}

@router.post("/workflow")
async def create_workflow(payload:dict,user:dict=Depends(current_user)):
    wid=str(uuid4());now=datetime.now(timezone.utc).isoformat()
    history=[{"state":str(payload.get("state","draft")),"actor":user["email"],"at":now}]
    async with SessionLocal() as s:
        s.add(WorkflowItem(id=wid,org_id=str(payload["org_id"]),project_id=payload.get("project_id"),item_type=str(payload.get("item_type","review")),
                           title=str(payload.get("title","Engineering review")),state=str(payload.get("state","draft")),assigned_to=payload.get("assigned_to"),payload=payload.get("payload",{}),history=history))
        await s.commit()
    return {"id":wid,"state":payload.get("state","draft")}

@router.patch("/workflow/{item_id}/transition")
async def transition(item_id:str,payload:dict,user:dict=Depends(current_user)):
    allowed={"draft":["review"],"review":["approved","rejected"],"rejected":["draft"],"approved":["issued_for_construction"],"issued_for_construction":["superseded"],"superseded":[]}
    async with SessionLocal() as s:
        row=await s.get(WorkflowItem,item_id)
        if not row:raise HTTPException(404,"workflow item not found")
        target=str(payload["state"])
        if target not in allowed.get(row.state,[]):raise HTTPException(400,f"Invalid transition {row.state} -> {target}")
        row.history=[*row.history,{"state":target,"actor":user["email"],"at":datetime.now(timezone.utc).isoformat(),"comment":payload.get("comment","")}]
        row.state=target;row.updated_at=datetime.now(timezone.utc);await s.commit()
        return {"id":row.id,"state":row.state,"history":row.history}

@router.post("/events")
async def event(payload:dict,user:dict=Depends(current_user)):
    eid=str(uuid4())
    async with SessionLocal() as s:
        s.add(EventRecord(id=eid,org_id=str(payload["org_id"]),project_id=payload.get("project_id"),event_type=str(payload.get("event_type","event")),severity=str(payload.get("severity","info")),payload=payload.get("payload",{})))
        await s.commit()
    return {"id":eid}

@router.post("/risk/rules")
async def rules(payload:dict,user:dict=Depends(current_user)): return evaluate_rules(payload.get("context",{}),payload.get("rules",[]))
@router.post("/risk/monte-carlo-slope")
async def mc(payload:dict,user:dict=Depends(current_user)): return monte_carlo_slope(**payload)
@router.post("/spatial/conditional")
async def conditional(payload:dict,user:dict=Depends(current_user)): return conditional_idw(payload.get("samples",[]),payload.get("targets",[]),float(payload.get("power",2)))

@router.post("/investigation/recommend")
async def investigate(payload:dict,user:dict=Depends(current_user)): return recommend_locations(payload.get("candidates",[]),payload.get("observations",[]),int(payload.get("count",5)),float(payload.get("min_spacing_m",50)))
@router.post("/investigation/methods")
async def methods(payload:dict,user:dict=Depends(current_user)): return choose_method(payload)

@router.post("/design/{tool}")
async def design(tool:str,payload:dict,user:dict=Depends(current_user)):
    funcs={"bearing_capacity":bearing_capacity,"settlement":elastic_settlement,"retaining_wall":retaining_wall,"pile_capacity":pile_capacity,"liquefaction":liquefaction_screening}
    if tool not in funcs:raise HTTPException(404,"unknown design tool")
    try:return funcs[tool](**payload)
    except TypeError as e:raise HTTPException(422,str(e))

@router.post("/copilot/command")
async def copilot(payload:dict,user:dict=Depends(current_user)): return interpret_command(str(payload.get("text","")),payload.get("context"))
@router.post("/copilot/explain-risk")
async def risk_explain(payload:dict,user:dict=Depends(current_user)): return explain_risk(payload.get("current",{}),payload.get("previous",{}))

@router.post("/field/sync")
async def field_sync(payload:dict,user:dict=Depends(current_user)): return merge_offline_records(payload.get("server",[]),payload.get("incoming",[]))

@router.post("/reports/engineering")
async def report(payload:dict,user:dict=Depends(current_user)): return engineering_report(payload.get("project",{}),payload.get("sections",[]),payload.get("results",[]),payload.get("risks",[]),payload.get("approvals",[]))
@router.post("/reports/borehole")
async def bh_report(payload:dict,user:dict=Depends(current_user)): return borehole_log(payload)

@router.post("/interop/geojson")
async def geojson(payload:dict,user:dict=Depends(current_user)): return export_geojson(payload.get("features",[]))
@router.post("/interop/landxml")
async def landxml(payload:dict,user:dict=Depends(current_user)):
    return Response(export_landxml_alignment(str(payload.get("name","GeoTect Alignment")),payload.get("points",[])),media_type="application/xml")
@router.post("/interop/ifc-manifest")
async def ifc(payload:dict,user:dict=Depends(current_user)): return ifc_manifest(payload.get("objects",[]))

@router.get("/templates")
async def templates(user:dict=Depends(current_user)): return TEMPLATES
@router.get("/templates/{name}")
async def get_template(name:str,user:dict=Depends(current_user)):
    try:return template(name)
    except KeyError:raise HTTPException(404,"template not found")

@router.post("/notifications")
async def notify(payload:dict,user:dict=Depends(require_permission("system.manage"))):
    return dispatch(str(payload["channel"]),str(payload["target"]),str(payload["message"]),payload.get("config"))

@router.post("/plugins")
async def register_plugin(payload:dict,user:dict=Depends(require_permission("system.manage"))):
    pid=str(payload.get("id") or uuid4())
    async with SessionLocal() as s:
        row=PluginRegistration(id=pid,name=str(payload["name"]),version=str(payload.get("version","0.1.0")),category=str(payload.get("category","general")),
          endpoint=payload.get("endpoint"),capabilities=payload.get("capabilities",[]),enabled=bool(payload.get("enabled",True)),config=payload.get("config",{}))
        s.add(row);await s.commit()
    return {"id":pid}

@router.get("/plugins")
async def plugins(user:dict=Depends(current_user)):
    async with SessionLocal() as s:
        rows=(await s.execute(select(PluginRegistration).order_by(PluginRegistration.name))).scalars().all()
        return [{"id":r.id,"name":r.name,"version":r.version,"category":r.category,"endpoint":r.endpoint,"capabilities":r.capabilities,"enabled":r.enabled} for r in rows]

@router.post("/jobs")
async def job(payload:dict,user:dict=Depends(require_permission("jobs.execute"))):
    jid=str(uuid4())
    async with SessionLocal() as s:
        s.add(ComputeJob(id=jid,org_id=str(payload["org_id"]),project_id=payload.get("project_id"),job_type=str(payload["job_type"]),input=payload.get("input",{}),created_by=user["uid"]))
        s.add(UsageLedger(org_id=str(payload["org_id"]),meter="compute_job",quantity=1,meta={"job_type":payload["job_type"],"job_id":jid}))
        await s.commit()
    return {"id":jid,"status":"queued"}

@router.get("/usage/{org_id}")
async def usage(org_id:str,user:dict=Depends(current_user)):
    async with SessionLocal() as s:
        rows=(await s.execute(select(UsageLedger).where(UsageLedger.org_id==org_id).order_by(desc(UsageLedger.created_at)).limit(500))).scalars().all()
        totals={}
        for r in rows: totals[r.meter]=totals.get(r.meter,0)+r.quantity
        return {"org_id":org_id,"totals":totals,"entries":[{"meter":r.meter,"quantity":r.quantity,"created_at":r.created_at.isoformat(),"meta":r.meta} for r in rows]}

@router.get("/events")
async def list_events(org_id:str,project_id:str|None=None,limit:int=500,user:dict=Depends(current_user)):
    async with SessionLocal() as s:
        q=select(EventRecord).where(EventRecord.org_id==org_id)
        if project_id:q=q.where(EventRecord.project_id==project_id)
        rows=(await s.execute(q.order_by(desc(EventRecord.created_at)).limit(max(1,min(limit,2000))))).scalars().all()
        return [{"id":r.id,"project_id":r.project_id,"event_type":r.event_type,"severity":r.severity,"payload":r.payload,"acknowledged":r.acknowledged,"created_at":r.created_at.isoformat()} for r in rows]

@router.get("/assets")
async def list_assets(org_id:str,project_id:str|None=None,user:dict=Depends(current_user)):
    async with SessionLocal() as s:
        q=select(Asset).where(Asset.org_id==org_id)
        if project_id:q=q.where(Asset.project_id==project_id)
        rows=(await s.execute(q.order_by(Asset.name))).scalars().all()
        return [{"id":r.id,"project_id":r.project_id,"name":r.name,"asset_type":r.asset_type,"geometry":r.geometry,"properties":r.properties,"health_score":r.health_score,"status":r.status} for r in rows]

@router.get("/workflow")
async def list_workflow(org_id:str,project_id:str|None=None,user:dict=Depends(current_user)):
    async with SessionLocal() as s:
        q=select(WorkflowItem).where(WorkflowItem.org_id==org_id)
        if project_id:q=q.where(WorkflowItem.project_id==project_id)
        rows=(await s.execute(q.order_by(desc(WorkflowItem.updated_at)))).scalars().all()
        return [{"id":r.id,"item_type":r.item_type,"title":r.title,"state":r.state,"assigned_to":r.assigned_to,"payload":r.payload,"history":r.history,"updated_at":r.updated_at.isoformat()} for r in rows]

@router.get("/jobs")
async def list_jobs(org_id:str,user:dict=Depends(current_user)):
    async with SessionLocal() as s:
        rows=(await s.execute(select(ComputeJob).where(ComputeJob.org_id==org_id).order_by(desc(ComputeJob.created_at)).limit(200))).scalars().all()
        return [{"id":r.id,"project_id":r.project_id,"job_type":r.job_type,"status":r.status,"progress":r.progress,"output":r.output,"created_at":r.created_at.isoformat(),"updated_at":r.updated_at.isoformat()} for r in rows]

@router.post("/jobs/{job_id}/cancel")
async def cancel_job(job_id:str,user:dict=Depends(require_permission("jobs.cancel"))):
    async with SessionLocal() as s:
        row=await s.get(ComputeJob,job_id)
        if not row:raise HTTPException(404,"job not found")
        if row.status in {"completed","failed"}:return {"id":job_id,"status":row.status}
        row.status="cancelled";row.updated_at=datetime.now(timezone.utc);await s.commit()
        return {"id":job_id,"status":"cancelled"}

@router.post("/ingest/drone-manifest")
async def drone_manifest(payload:dict,user:dict=Depends(current_user)):
    required=["survey_id","captured_at","crs","assets"]
    missing=[x for x in required if x not in payload]
    if missing:raise HTTPException(422,f"missing fields: {missing}")
    return {"accepted":True,"kind":"drone","survey_id":payload["survey_id"],"assets":len(payload["assets"]),
      "pipelines":["photogrammetry","point_cloud_change","volume_change","slope_change"],"status":"queued_for_processing"}

@router.post("/ingest/satellite-manifest")
async def satellite_manifest(payload:dict,user:dict=Depends(current_user)):
    return {"accepted":True,"kind":"satellite","source":payload.get("source","unknown"),"scene_id":payload.get("scene_id"),
      "pipelines":["coregistration","cloud_mask","insar_or_optical_change","timeseries"],"status":"queued_for_processing"}

@router.post("/portals/view")
async def portal_view(payload:dict,user:dict=Depends(current_user)):
    allowed=set(payload.get("allowed_layers",[]));scene=payload.get("scene",{});filtered={**scene}
    if "boreholes" not in allowed:filtered["boreholes"]=[]
    if "sensors" not in allowed:filtered["sensors"]=[]
    if "infrastructure" not in allowed:filtered["infrastructure"]=[]
    if "bodies" not in allowed:filtered["bodies"]=[]
    return {"mode":"read_only_client_portal","scene":filtered,"allowed_layers":sorted(allowed)}


@router.post("/remote-sensing/ndvi")
async def rs_ndvi(payload:dict,user:dict=Depends(current_user)):
    from remote_sensing import ndvi
    return ndvi(payload["red"],payload["nir"])

@router.post("/remote-sensing/change")
async def rs_change(payload:dict,user:dict=Depends(current_user)):
    from remote_sensing import raster_change
    return raster_change(payload["before"],payload["after"],float(payload.get("threshold",0)))

@router.post("/pointcloud/change")
async def pc_change(payload:dict,user:dict=Depends(current_user)):
    from remote_sensing import pointcloud_change
    return pointcloud_change(payload["before"],payload["after"],float(payload.get("tolerance_m",.1)))

@router.post("/geophysics/potential/invert")
async def potential(payload:dict,user:dict=Depends(current_user)):
    from advanced_geophysics import linear_potential_inversion
    return linear_potential_inversion(payload["kernel"],payload["observations"],float(payload.get("regularization",.1)))

@router.post("/geophysics/masw")
async def masw(payload:dict,user:dict=Depends(current_user)):
    from advanced_geophysics import masw_dispersion
    return masw_dispersion(payload["freq_hz"],payload["phase_velocity_m_s"])

@router.post("/construction/cut-fill")
async def cutfill(payload:dict,user:dict=Depends(current_user)):
    from construction_mining import cut_fill
    return cut_fill(payload["existing"],payload["design"],float(payload["cell_area_m2"]))

@router.post("/mine/bench")
async def bench(payload:dict,user:dict=Depends(current_user)):
    from construction_mining import bench_geometry
    return bench_geometry(float(payload["height_m"]),float(payload["width_m"]),float(payload["face_angle_deg"]),int(payload["bench_count"]))

@router.post("/tunnel/convergence")
async def tunnel_convergence(payload:dict,user:dict=Depends(current_user)):
    from construction_mining import convergence
    return convergence(float(payload["baseline_diameter_m"]),float(payload["current_diameter_m"]))

@router.post("/tiles/3dtiles-manifest")
async def tiles_manifest(payload:dict,user:dict=Depends(current_user)):
    from tiles3d import point_tiles_to_3dtiles
    return point_tiles_to_3dtiles(payload)

@router.post("/billing/quota")
async def billing_quota(payload:dict,user:dict=Depends(current_user)):
    from billing import quota
    return quota(str(payload.get("plan","free")),payload.get("usage",{}))
