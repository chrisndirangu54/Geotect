from __future__ import annotations
from datetime import datetime,timezone
from uuid import uuid4
from fastapi import APIRouter,Depends,HTTPException,UploadFile,File,Query
from sqlalchemy import select,desc
from db import SessionLocal
from auth import current_user,require_permission
from production_models import StacCollection,StacItem,SensorThing,SensorDatastream,SensorObservation,SchemaRegistry,SignatureProvider
from diggs_validation import validate_with_registry,validate_official_diggs3
from object_store import presigned_get,presigned_put,range_get
from pki import digest_payload,verify_x509_signature,external_sign_request
from model_registry import get_provider_secret

router=APIRouter(prefix="/api/v1/production",tags=["production"])

@router.post("/schemas")
async def register_schema(payload:dict,user:dict=Depends(require_permission("system.manage"))):
    sid=str(payload.get("id") or uuid4())
    async with SessionLocal() as s:
        s.add(SchemaRegistry(id=sid,standard=str(payload["standard"]),version=str(payload["version"]),schema_uri=str(payload["schema_uri"]),sha256=payload.get("sha256"),active=bool(payload.get("active",True))))
        await s.commit()
    return {"id":sid}

@router.post("/diggs/validate")
async def validate_diggs(file:UploadFile=File(...),schema_id:str=Query(...),user:dict=Depends(current_user)):
    xml=await file.read()
    async with SessionLocal() as s:
        schema=await s.get(SchemaRegistry,schema_id)
        if not schema or not schema.active:raise HTTPException(404,"active schema not found")
        if schema.standard.lower()!="diggs":raise HTTPException(400,"schema is not registered for DIGGS")
    try:return validate_with_registry(xml,schema.schema_uri,schema.sha256)
    except Exception as exc:raise HTTPException(422,str(exc))

@router.get("/stac")
async def stac_root(user:dict=Depends(current_user)):
    return {"stac_version":"1.0.0","type":"Catalog","id":"geotect","description":"GeoTect STAC API","links":[{"rel":"data","href":"/api/v1/production/stac/collections"},{"rel":"search","href":"/api/v1/production/stac/search"}]}

@router.post("/stac/collections")
async def create_collection(payload:dict,user:dict=Depends(current_user)):
    cid=str(payload["id"])
    async with SessionLocal() as s:
        row=await s.get(StacCollection,cid)
        if row:raise HTTPException(409,"collection exists")
        data={**payload,"type":"Collection","stac_version":payload.get("stac_version","1.0.0")}
        s.add(StacCollection(id=cid,org_id=str(payload["org_id"]),payload=data));await s.commit()
    return data

@router.get("/stac/collections")
async def list_collections(org_id:str,user:dict=Depends(current_user)):
    async with SessionLocal() as s:
        rows=(await s.execute(select(StacCollection).where(StacCollection.org_id==org_id).order_by(StacCollection.id))).scalars().all()
        return {"collections":[r.payload for r in rows],"links":[]}

@router.post("/stac/collections/{collection_id}/items")
async def create_item(collection_id:str,payload:dict,user:dict=Depends(current_user)):
    iid=str(payload["id"]);dt=(payload.get("properties") or {}).get("datetime")
    data={**payload,"type":"Feature","stac_version":payload.get("stac_version","1.0.0"),"collection":collection_id}
    async with SessionLocal() as s:
        if not await s.get(StacCollection,collection_id):raise HTTPException(404,"collection not found")
        existing=await s.get(StacItem,{"collection_id":collection_id,"id":iid})
        if existing:raise HTTPException(409,"item exists")
        s.add(StacItem(collection_id=collection_id,id=iid,org_id=str(payload["org_id"]),datetime_text=dt,bbox=payload.get("bbox",[]),payload=data));await s.commit()
    return data

@router.get("/stac/collections/{collection_id}/items")
async def list_items(collection_id:str,limit:int=100,offset:int=0,user:dict=Depends(current_user)):
    limit=max(1,min(limit,1000))
    async with SessionLocal() as s:
        rows=(await s.execute(select(StacItem).where(StacItem.collection_id==collection_id).order_by(desc(StacItem.datetime_text)).offset(max(offset,0)).limit(limit))).scalars().all()
        return {"type":"FeatureCollection","features":[r.payload for r in rows],"links":[],"context":{"returned":len(rows),"limit":limit,"offset":offset}}

@router.post("/stac/search")
async def search_stac(payload:dict,user:dict=Depends(current_user)):
    collections=payload.get("collections",[]);limit=max(1,min(int(payload.get("limit",100)),1000))
    async with SessionLocal() as s:
        q=select(StacItem)
        if collections:q=q.where(StacItem.collection_id.in_(collections))
        if payload.get("datetime"):q=q.where(StacItem.datetime_text>=str(payload["datetime"]).split("/")[0])
        rows=(await s.execute(q.order_by(desc(StacItem.datetime_text)).limit(limit))).scalars().all()
        return {"type":"FeatureCollection","features":[r.payload for r in rows],"links":[]}

@router.post("/sensorthings/Things")
async def create_thing(payload:dict,user:dict=Depends(current_user)):
    tid=str(payload.get("@iot.id") or uuid4())
    async with SessionLocal() as s:
        s.add(SensorThing(id=tid,org_id=str(payload["org_id"]),name=str(payload.get("name",tid)),description=str(payload.get("description","")),properties=payload.get("properties",{}),locations=payload.get("Locations",[])));await s.commit()
    return {"@iot.id":tid,"name":payload.get("name",tid)}

@router.get("/sensorthings/Things")
async def list_things(org_id:str,top:int=100,skip:int=0,user:dict=Depends(current_user)):
    async with SessionLocal() as s:
        rows=(await s.execute(select(SensorThing).where(SensorThing.org_id==org_id).offset(max(skip,0)).limit(max(1,min(top,1000))))).scalars().all()
        return {"value":[{"@iot.id":r.id,"name":r.name,"description":r.description,"properties":r.properties,"Locations":r.locations} for r in rows]}

@router.post("/sensorthings/Datastreams")
async def create_datastream(payload:dict,user:dict=Depends(current_user)):
    did=str(payload.get("@iot.id") or uuid4())
    thing_id=str((payload.get("Thing") or {}).get("@iot.id") or payload.get("thing_id"))
    async with SessionLocal() as s:
        if not await s.get(SensorThing,thing_id):raise HTTPException(404,"Thing not found")
        s.add(SensorDatastream(id=did,org_id=str(payload["org_id"]),thing_id=thing_id,name=str(payload.get("name",did)),description=str(payload.get("description","")),
          observation_type=str(payload.get("observationType","OM_Measurement")),unit_of_measurement=payload.get("unitOfMeasurement",{}),observed_property=payload.get("ObservedProperty",{}),sensor=payload.get("Sensor",{})));await s.commit()
    return {"@iot.id":did}

@router.post("/sensorthings/Observations")
async def create_observation(payload:dict,user:dict=Depends(current_user)):
    oid=str(payload.get("@iot.id") or uuid4());did=str((payload.get("Datastream") or {}).get("@iot.id") or payload.get("datastream_id"))
    when=datetime.fromisoformat(str(payload.get("phenomenonTime") or datetime.now(timezone.utc).isoformat()).replace("Z","+00:00"))
    async with SessionLocal() as s:
        ds=await s.get(SensorDatastream,did)
        if not ds:raise HTTPException(404,"Datastream not found")
        s.add(SensorObservation(id=oid,org_id=ds.org_id,datastream_id=did,phenomenon_time=when,result=payload.get("result"),parameters=payload.get("parameters",{})));await s.commit()
    return {"@iot.id":oid}

@router.get("/sensorthings/Datastreams/{datastream_id}/Observations")
async def observations(datastream_id:str,top:int=100,skip:int=0,user:dict=Depends(current_user)):
    async with SessionLocal() as s:
        rows=(await s.execute(select(SensorObservation).where(SensorObservation.datastream_id==datastream_id).order_by(desc(SensorObservation.phenomenon_time)).offset(max(skip,0)).limit(max(1,min(top,10000))))).scalars().all()
        return {"value":[{"@iot.id":r.id,"phenomenonTime":r.phenomenon_time.isoformat(),"resultTime":r.result_time.isoformat(),"result":r.result,"parameters":r.parameters} for r in rows]}

@router.post("/objects/presign-put")
async def object_put(payload:dict,user:dict=Depends(current_user)): return presigned_put(str(payload["key"]),str(payload.get("content_type","application/octet-stream")),int(payload.get("expires",900)))
@router.post("/objects/presign-get")
async def object_get(payload:dict,user:dict=Depends(current_user)): return presigned_get(str(payload["key"]),int(payload.get("expires",900)))
@router.get("/objects/range")
async def object_range(key:str,start:int,end:int,user:dict=Depends(current_user)):
    if start<0 or end<start or end-start>20*1024*1024:raise HTTPException(400,"invalid or excessive range")
    from fastapi.responses import Response
    return Response(range_get(key,start,end),status_code=206,media_type="application/octet-stream",headers={"Content-Range":f"bytes {start}-{end}/*","Accept-Ranges":"bytes"})

@router.post("/pki/providers")
async def pki_provider(payload:dict,user:dict=Depends(require_permission("system.manage"))):
    pid=str(payload.get("id") or uuid4())
    async with SessionLocal() as s:
        s.add(SignatureProvider(id=pid,org_id=str(payload["org_id"]),provider_type=str(payload["provider_type"]),name=str(payload["name"]),config=payload.get("config",{}),enabled=bool(payload.get("enabled",True))));await s.commit()
    return {"id":pid}

@router.post("/pki/verify-x509")
async def pki_verify(payload:dict,user:dict=Depends(current_user)):
    try:return verify_x509_signature(payload["payload"],str(payload["signature_b64"]),str(payload["certificate_pem"]))
    except Exception as exc:raise HTTPException(422,str(exc))

@router.post("/pki/sign/{provider_id}")
async def pki_sign(provider_id:str,payload:dict,user:dict=Depends(current_user)):
    async with SessionLocal() as s:
        p=await s.get(SignatureProvider,provider_id)
        if not p or not p.enabled:raise HTTPException(404,"signature provider not found")
    if p.provider_type!="external_https":raise HTTPException(400,"provider type is not an external signing service")
    token=await get_provider_secret("pki",str(p.config.get("secret_name",provider_id)))
    if not token:raise HTTPException(400,"PKI provider credential is not configured")
    return await external_sign_request(str(p.config["url"]),token,digest_payload(payload.get("payload",{})),payload.get("metadata"))


@router.post("/diggs/validate-official-3")
async def validate_official_diggs(file:UploadFile=File(...),user:dict=Depends(current_user)):
    xml=await file.read()
    try:return validate_official_diggs3(xml)
    except Exception as exc:raise HTTPException(422,str(exc))

@router.post("/solvers/nonlinear-hm")
async def nonlinear_hm(payload:dict,user:dict=Depends(require_permission("jobs.execute"))):
    from nonlinear_coupled import solve_staggered_hm
    try:return solve_staggered_hm(**payload)
    except Exception as exc:raise HTTPException(422,str(exc))

@router.get("/solvers/benchmarks")
async def solver_benchmarks(user:dict=Depends(current_user)):
    from nonlinear_coupled import benchmark_suite
    return benchmark_suite()
