from __future__ import annotations
from datetime import datetime,timezone
from hashlib import sha256
from secrets import token_urlsafe
from urllib.parse import urlparse,urljoin
from uuid import uuid4
from fastapi import APIRouter,Depends,HTTPException,Header
from sqlalchemy import select
from db import SessionLocal
from auth import current_user,require_permission
from integration_models import IntegrationConnection,BridgeCommand
from vendor_connectors import integration_catalog,esri_service_info,esri_query,esri_apply_edits,seequent_discovery,seequent_request,ogc_features
import httpx
from model_registry import get_provider_secret

router=APIRouter(prefix="/api/v1/integrations",tags=["integrations"])

def _safe_url(url:str,allowed_hosts:list[str]|None=None)->str:
    p=urlparse(url)
    if p.scheme!="https": raise HTTPException(400,"Only HTTPS integration URLs are allowed")
    host=(p.hostname or "").lower()
    if not host: raise HTTPException(400,"Invalid integration URL")
    if host in {"localhost","127.0.0.1","::1"} or host.startswith("169.254.") or host.startswith("10.") or host.startswith("192.168."):
        raise HTTPException(400,"Private/local addresses are not allowed for cloud connectors")
    if allowed_hosts and not any(host==h or host.endswith("."+h) for h in allowed_hosts):
        raise HTTPException(400,"URL host is not approved for this connector")
    return url

@router.get("/catalog")
async def catalog(user:dict=Depends(current_user)): return integration_catalog()

@router.post("/connections")
async def create_connection(payload:dict,user:dict=Depends(current_user)):
    provider=str(payload["provider"])
    cat=integration_catalog()
    if provider not in cat: raise HTTPException(400,"Unknown integration provider")
    cid=str(uuid4());mode=cat[provider]["mode"];raw_bridge=None
    config=dict(payload.get("config",{}))
    if mode=="local_bridge":
        raw_bridge=token_urlsafe(32);config["bridge_token_hash"]=sha256(raw_bridge.encode()).hexdigest()
    base_url=payload.get("base_url")
    if base_url and mode=="rest": _safe_url(str(base_url))
    async with SessionLocal() as s:
        s.add(IntegrationConnection(id=cid,org_id=str(payload["org_id"]),provider=provider,name=str(payload.get("name",provider)),mode=mode,base_url=base_url,config=config,created_by=user["uid"]))
        await s.commit()
    out={"id":cid,"provider":provider,"mode":mode,"name":payload.get("name",provider)}
    if raw_bridge:out["bridge_token"]=raw_bridge;out["bridge_token_note"]="Shown once. Store it securely on the desktop bridge."
    return out

@router.get("/connections")
async def connections(org_id:str,user:dict=Depends(current_user)):
    async with SessionLocal() as s:
        rows=(await s.execute(select(IntegrationConnection).where(IntegrationConnection.org_id==org_id).order_by(IntegrationConnection.provider,IntegrationConnection.name))).scalars().all()
        return [{"id":r.id,"provider":r.provider,"name":r.name,"mode":r.mode,"base_url":r.base_url,"enabled":r.enabled,
                 "config":{k:v for k,v in r.config.items() if k!="bridge_token_hash"},"updated_at":r.updated_at.isoformat()} for r in rows]

@router.patch("/connections/{connection_id}")
async def update_connection(connection_id:str,payload:dict,user:dict=Depends(current_user)):
    async with SessionLocal() as s:
        row=await s.get(IntegrationConnection,connection_id)
        if not row:raise HTTPException(404,"connection not found")
        if "name" in payload:row.name=str(payload["name"])
        if "enabled" in payload:row.enabled=bool(payload["enabled"])
        if "base_url" in payload:
            if row.mode=="rest":_safe_url(str(payload["base_url"]))
            row.base_url=str(payload["base_url"])
        if "config" in payload:
            secret_hash=row.config.get("bridge_token_hash");row.config=dict(payload["config"])
            if secret_hash:row.config["bridge_token_hash"]=secret_hash
        row.updated_at=datetime.now(timezone.utc);await s.commit()
    return {"ok":True}

async def _connection(connection_id:str)->IntegrationConnection:
    async with SessionLocal() as s:
        row=await s.get(IntegrationConnection,connection_id)
        if not row or not row.enabled:raise HTTPException(404,"enabled connection not found")
        s.expunge(row);return row

@router.post("/esri/{connection_id}/info")
async def esri_info(connection_id:str,user:dict=Depends(current_user)):
    row=await _connection(connection_id)
    if row.provider!="esri_arcgis" or not row.base_url:raise HTTPException(400,"not an Esri REST connection")
    token=await get_provider_secret("esri_arcgis",str(row.config.get("secret_name","access_token")))
    return await esri_service_info(_safe_url(row.base_url,["arcgis.com","esri.com"] if "arcgis.com" in row.base_url else None),token)

@router.post("/esri/{connection_id}/query")
async def esri_layer_query(connection_id:str,payload:dict,user:dict=Depends(current_user)):
    row=await _connection(connection_id)
    if row.provider!="esri_arcgis":raise HTTPException(400,"not an Esri connection")
    url=_safe_url(str(payload.get("layer_url") or row.base_url))
    token=await get_provider_secret("esri_arcgis",str(row.config.get("secret_name","access_token")))
    return await esri_query(url,str(payload.get("where","1=1")),str(payload.get("out_fields","*")),token,int(payload.get("offset",0)),int(payload.get("limit",2000)))

@router.post("/esri/{connection_id}/apply-edits")
async def esri_edits(connection_id:str,payload:dict,user:dict=Depends(require_permission("projects.write_all"))):
    row=await _connection(connection_id)
    if row.provider!="esri_arcgis":raise HTTPException(400,"not an Esri connection")
    url=_safe_url(str(payload.get("layer_url") or row.base_url))
    token=await get_provider_secret("esri_arcgis",str(row.config.get("secret_name","access_token")))
    return await esri_apply_edits(url,payload.get("adds"),payload.get("updates"),payload.get("deletes"),token)

@router.post("/seequent/{connection_id}/discovery")
async def seequent_discover(connection_id:str,payload:dict,user:dict=Depends(current_user)):
    row=await _connection(connection_id)
    if row.provider!="seequent_evo":raise HTTPException(400,"not a Seequent Evo connection")
    token=await get_provider_secret("seequent_evo",str(row.config.get("secret_name","access_token")))
    if not token:raise HTTPException(400,"Seequent Evo access token is not configured")
    return await seequent_discovery(token,payload.get("services"))

@router.post("/seequent/{connection_id}/request")
async def seequent_api(connection_id:str,payload:dict,user:dict=Depends(current_user)):
    row=await _connection(connection_id)
    if row.provider!="seequent_evo":raise HTTPException(400,"not a Seequent Evo connection")
    token=await get_provider_secret("seequent_evo",str(row.config.get("secret_name","access_token")))
    if not token:raise HTTPException(400,"Seequent Evo access token is not configured")
    url=_safe_url(str(payload["url"]),["seequent.com"])
    method=str(payload.get("method","GET")).upper()
    if method not in {"GET","POST","PUT","PATCH","DELETE"}:raise HTTPException(400,"unsupported method")
    return await seequent_request(url,token,method,payload.get("payload"))

@router.post("/ogc/{connection_id}/features")
async def ogc(connection_id:str,payload:dict,user:dict=Depends(current_user)):
    row=await _connection(connection_id)
    if row.provider not in {"ogc_api_features","geoserver"} or not row.base_url:raise HTTPException(400,"not an OGC/GeoServer connection")
    return await ogc_features(_safe_url(row.base_url),payload.get("collection"),int(payload.get("limit",1000)))

@router.post("/bridge/{connection_id}/commands")
async def queue_bridge_command(connection_id:str,payload:dict,user:dict=Depends(current_user)):
    row=await _connection(connection_id)
    if row.mode!="local_bridge":raise HTTPException(400,"connection does not use a desktop bridge")
    cid=str(uuid4())
    async with SessionLocal() as s:
        s.add(BridgeCommand(id=cid,connection_id=connection_id,command=str(payload["command"]),payload=payload.get("payload",{})))
        await s.commit()
    return {"id":cid,"status":"queued"}

async def _verify_bridge(connection_id:str,token:str|None):
    row=await _connection(connection_id)
    expected=row.config.get("bridge_token_hash")
    if not token or not expected or sha256(token.encode()).hexdigest()!=expected:raise HTTPException(401,"invalid bridge token")
    return row

@router.get("/bridge/{connection_id}/poll")
async def bridge_poll(connection_id:str,x_geotect_bridge_token:str|None=Header(default=None)):
    await _verify_bridge(connection_id,x_geotect_bridge_token)
    async with SessionLocal() as s:
        q=await s.execute(select(BridgeCommand).where(BridgeCommand.connection_id==connection_id,BridgeCommand.status=="queued").order_by(BridgeCommand.created_at).limit(1))
        row=q.scalar_one_or_none()
        if not row:return {"command":None}
        row.status="claimed";row.updated_at=datetime.now(timezone.utc);await s.commit()
        return {"id":row.id,"command":row.command,"payload":row.payload}

@router.post("/bridge/{connection_id}/result/{command_id}")
async def bridge_result(connection_id:str,command_id:str,payload:dict,x_geotect_bridge_token:str|None=Header(default=None)):
    await _verify_bridge(connection_id,x_geotect_bridge_token)
    async with SessionLocal() as s:
        row=await s.get(BridgeCommand,command_id)
        if not row or row.connection_id!=connection_id:raise HTTPException(404,"command not found")
        row.status="completed" if payload.get("ok",True) else "failed";row.result=payload.get("result",{});row.error=payload.get("error");row.updated_at=datetime.now(timezone.utc);await s.commit()
    return {"ok":True}


@router.get("/bridge/{connection_id}/commands/{command_id}")
async def bridge_command_status(connection_id:str,command_id:str,user:dict=Depends(current_user)):
    async with SessionLocal() as s:
        row=await s.get(BridgeCommand,command_id)
        if not row or row.connection_id!=connection_id:raise HTTPException(404,"command not found")
        return {"id":row.id,"command":row.command,"status":row.status,"result":row.result,"error":row.error,"updated_at":row.updated_at.isoformat()}

@router.post("/micromine-nexus/{connection_id}/request")
async def micromine_nexus_request(connection_id:str,payload:dict,user:dict=Depends(current_user)):
    row=await _connection(connection_id)
    if row.provider!="micromine_nexus" or not row.base_url:raise HTTPException(400,"not a Micromine Nexus connection")
    base=_safe_url(row.base_url,["micromine.com"])
    rel=str(payload.get("path","")).lstrip("/")
    target=urljoin(base.rstrip("/")+"/",rel)
    parsed_base=urlparse(base);parsed_target=urlparse(target)
    if parsed_target.hostname!=parsed_base.hostname:raise HTTPException(400,"Nexus request must remain on the configured tenant host")
    token=await get_provider_secret("micromine_nexus",str(row.config.get("secret_name","access_token")))
    headers={"Accept":"application/json"}
    if token:headers["Authorization"]=f"Bearer {token}"
    method=str(payload.get("method","GET")).upper()
    if method not in {"GET","POST","PUT","PATCH","DELETE"}:raise HTTPException(400,"unsupported method")
    async with httpx.AsyncClient(timeout=60) as client:
        resp=await client.request(method,target,headers=headers,json=payload.get("payload"),params=payload.get("params"))
        resp.raise_for_status()
        if not resp.content:return {"status":resp.status_code}
        try:return resp.json()
        except Exception:return {"status":resp.status_code,"text":resp.text[:2000]}
