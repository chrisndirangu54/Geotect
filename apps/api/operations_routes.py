from __future__ import annotations
from datetime import datetime,timezone
from uuid import uuid4
from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy import select
from db import SessionLocal
from auth import current_user,require_permission
from field_models import FieldLog,SampleRecord,InstrumentCalibration
from enterprise_models import EnterprisePolicy,MarketplaceItem
from admin_models import AppUser

router=APIRouter(prefix="/api/v1/operations",tags=["field-enterprise"])

@router.post("/field/logs")
async def field_log(payload:dict,user:dict=Depends(current_user)):
    rid=str(uuid4())
    async with SessionLocal() as s:
        s.add(FieldLog(id=rid,org_id=str(payload["org_id"]),project_id=str(payload["project_id"]),log_type=str(payload.get("log_type","observation")),
          geometry=payload.get("geometry",{}),content=payload.get("content",{}),media=payload.get("media",[]),created_by=user["uid"]))
        await s.commit()
    return {"id":rid,"offline_sync_key":rid}

@router.post("/samples")
async def create_sample(payload:dict,user:dict=Depends(current_user)):
    rid=str(uuid4());code=str(payload.get("sample_code") or f"GT-{rid[:8].upper()}")
    event={"action":"collected","by":user["email"],"at":datetime.now(timezone.utc).isoformat(),"location":payload.get("location",{})}
    async with SessionLocal() as s:
        s.add(SampleRecord(id=rid,org_id=str(payload["org_id"]),project_id=str(payload["project_id"]),sample_code=code,sample_type=str(payload.get("sample_type","soil")),
          location=payload.get("location",{}),chain=[event],metadata_json=payload.get("metadata",{})))
        await s.commit()
    return {"id":rid,"sample_code":code,"qr_payload":f"geotect://sample/{rid}","rfid_key":rid}

@router.post("/samples/{sample_id}/transfer")
async def transfer_sample(sample_id:str,payload:dict,user:dict=Depends(current_user)):
    async with SessionLocal() as s:
        row=await s.get(SampleRecord,sample_id)
        if not row:raise HTTPException(404,"sample not found")
        event={"action":"transfer","by":user["email"],"to":payload.get("to"),"at":datetime.now(timezone.utc).isoformat(),"note":payload.get("note","")}
        row.chain=[*row.chain,event];row.status=str(payload.get("status","in_transit"));row.updated_at=datetime.now(timezone.utc);await s.commit()
        return {"sample_code":row.sample_code,"status":row.status,"chain":row.chain}

@router.post("/instruments/calibration")
async def calibration(payload:dict,user:dict=Depends(current_user)):
    rid=str(uuid4())
    calibrated=datetime.fromisoformat(str(payload["calibrated_at"]).replace("Z","+00:00"));expires=datetime.fromisoformat(str(payload["expires_at"]).replace("Z","+00:00")) if payload.get("expires_at") else None
    async with SessionLocal() as s:
        s.add(InstrumentCalibration(id=rid,org_id=str(payload["org_id"]),instrument_id=str(payload["instrument_id"]),instrument_type=str(payload["instrument_type"]),
          certificate_ref=payload.get("certificate_ref"),calibrated_at=calibrated,expires_at=expires,calibration_data=payload.get("calibration_data",{}),created_by=user["uid"]))
        await s.commit()
    return {"id":rid}

@router.get("/instruments/{instrument_id}/calibration-status")
async def calibration_status(instrument_id:str,user:dict=Depends(current_user)):
    async with SessionLocal() as s:
        q=await s.execute(select(InstrumentCalibration).where(InstrumentCalibration.instrument_id==instrument_id).order_by(InstrumentCalibration.calibrated_at.desc()).limit(1))
        row=q.scalar_one_or_none()
        if not row:return {"instrument_id":instrument_id,"status":"unknown"}
        now=datetime.now(timezone.utc);expired=bool(row.expires_at and row.expires_at<now)
        return {"instrument_id":instrument_id,"status":"expired" if expired else "valid","calibrated_at":row.calibrated_at.isoformat(),"expires_at":row.expires_at.isoformat() if row.expires_at else None}

@router.put("/enterprise/{org_id}/policy")
async def policy(org_id:str,payload:dict,user:dict=Depends(require_permission("system.manage"))):
    async with SessionLocal() as s:
        row=await s.get(EnterprisePolicy,org_id)
        if not row:
            row=EnterprisePolicy(org_id=org_id);s.add(row)
        for key in ["sso_mode","saml_metadata","scim_enabled","data_residency","cmek_provider","cmek_key_ref","rate_limits","retention"]:
            if key in payload:setattr(row,key,payload[key])
        row.updated_at=datetime.now(timezone.utc);await s.commit()
    return {"org_id":org_id,"configured":True}

@router.get("/enterprise/{org_id}/policy")
async def get_policy(org_id:str,user:dict=Depends(current_user)):
    async with SessionLocal() as s:
        row=await s.get(EnterprisePolicy,org_id)
        if not row:return {"org_id":org_id,"sso_mode":"firebase","scim_enabled":False,"data_residency":"default","rate_limits":{}}
        return {"org_id":org_id,"sso_mode":row.sso_mode,"saml_metadata":row.saml_metadata,"scim_enabled":row.scim_enabled,"data_residency":row.data_residency,
          "cmek_provider":row.cmek_provider,"cmek_key_ref":row.cmek_key_ref,"rate_limits":row.rate_limits,"retention":row.retention}

@router.get("/scim/v2/Users")
async def scim_users(org_id:str,user:dict=Depends(require_permission("users.read"))):
    async with SessionLocal() as s:
        rows=(await s.execute(select(AppUser))).scalars().all()
        resources=[{"schemas":["urn:ietf:params:scim:schemas:core:2.0:User"],"id":x.uid,"userName":x.email,"displayName":x.display_name,"active":not x.disabled} for x in rows]
        return {"schemas":["urn:ietf:params:scim:api:messages:2.0:ListResponse"],"totalResults":len(resources),"Resources":resources,"startIndex":1,"itemsPerPage":len(resources)}

@router.post("/marketplace")
async def marketplace_create(payload:dict,user:dict=Depends(require_permission("system.manage"))):
    rid=str(uuid4())
    async with SessionLocal() as s:
        s.add(MarketplaceItem(id=rid,publisher_org_id=str(payload["publisher_org_id"]),name=str(payload["name"]),item_type=str(payload.get("item_type","plugin")),
          version=str(payload.get("version","0.1.0")),manifest=payload.get("manifest",{}),pricing=payload.get("pricing",{}),published=bool(payload.get("published",False))))
        await s.commit()
    return {"id":rid}

@router.get("/marketplace")
async def marketplace(user:dict=Depends(current_user)):
    async with SessionLocal() as s:
        rows=(await s.execute(select(MarketplaceItem).where(MarketplaceItem.published.is_(True)).order_by(MarketplaceItem.name))).scalars().all()
        return [{"id":x.id,"name":x.name,"item_type":x.item_type,"version":x.version,"manifest":x.manifest,"pricing":x.pricing} for x in rows]


@router.post("/scim/v2/Users")
async def scim_create_user(payload:dict,user:dict=Depends(require_permission("users.write"))):
    uid=str(payload.get("id") or uuid4());email=str(payload.get("userName","")).lower()
    if not email:raise HTTPException(422,"userName/email required")
    async with SessionLocal() as s:
        row=await s.get(AppUser,uid)
        if row:raise HTTPException(409,"user exists")
        row=AppUser(uid=uid,email=email,display_name=payload.get("displayName"),role="user",permissions=[],disabled=not bool(payload.get("active",True)))
        s.add(row);await s.commit()
    return {"schemas":["urn:ietf:params:scim:schemas:core:2.0:User"],"id":uid,"userName":email,"displayName":row.display_name,"active":not row.disabled}

@router.patch("/scim/v2/Users/{uid}")
async def scim_patch_user(uid:str,payload:dict,user:dict=Depends(require_permission("users.write"))):
    async with SessionLocal() as s:
        row=await s.get(AppUser,uid)
        if not row:raise HTTPException(404,"user not found")
        for op in payload.get("Operations",[]):
            path=str(op.get("path","")).lower();value=op.get("value")
            if path=="active":row.disabled=not bool(value)
            elif path in {"displayname","display_name"}:row.display_name=str(value)
        await s.commit()
    return {"id":uid,"userName":row.email,"displayName":row.display_name,"active":not row.disabled}
