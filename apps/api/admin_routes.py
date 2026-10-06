from __future__ import annotations
from datetime import datetime,timezone
from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy import select,desc
from sqlalchemy.exc import IntegrityError
from db import SessionLocal
from auth import current_user,require_permission,ALL_PERMISSIONS,BOOTSTRAP_SUPER_ADMIN
from admin_models import AppUser,SystemSetting,ApiSecret,ModelConfig,AuditEvent
from secret_crypto import encrypt_secret,masked_secret

router=APIRouter(prefix="/api/v1/admin",tags=["admin"])

async def audit(actor:dict,action:str,target:str,detail:dict|None=None):
    async with SessionLocal() as s:
        s.add(AuditEvent(actor_uid=actor["uid"],actor_email=actor["email"],action=action,target=target,detail=detail or {}))
        await s.commit()

@router.get("/me")
async def me(user:dict=Depends(current_user)):
    return {**user,"bootstrap_super_admin":user["email"].lower()==BOOTSTRAP_SUPER_ADMIN}

@router.get("/overview")
async def overview(user:dict=Depends(require_permission("settings.read"))):
    async with SessionLocal() as s:
        users=(await s.execute(select(AppUser))).scalars().all()
        secrets=(await s.execute(select(ApiSecret))).scalars().all()
        models=(await s.execute(select(ModelConfig))).scalars().all()
        settings=(await s.execute(select(SystemSetting))).scalars().all()
        return {
          "counts":{"users":len(users),"api_keys":len(secrets),"model_tasks":len(models),"settings":len(settings)},
          "super_admin":user["email"],"role":user["role"],"permissions":user["permissions"],
          "security":{"secrets_encrypted":True,"bootstrap_super_admin":BOOTSTRAP_SUPER_ADMIN,"dev_auth_enabled":False}
        }

@router.get("/users")
async def users(user:dict=Depends(require_permission("users.read"))):
    async with SessionLocal() as s:
        rows=(await s.execute(select(AppUser).order_by(AppUser.email))).scalars().all()
        return [{"uid":x.uid,"email":x.email,"display_name":x.display_name,"role":x.role,"disabled":x.disabled,"permissions":x.permissions} for x in rows]

@router.patch("/users/{uid}")
async def update_user(uid:str,payload:dict,actor:dict=Depends(require_permission("users.write"))):
    async with SessionLocal() as s:
        target=await s.get(AppUser,uid)
        if not target: raise HTTPException(404,"user not found")
        if target.email.lower()==BOOTSTRAP_SUPER_ADMIN and payload.get("disabled") is True:
            raise HTTPException(400,"Bootstrap super admin cannot be disabled here")
        if "role" in payload:
            role=str(payload["role"])
            if role not in {"user","admin","super_admin"}: raise HTTPException(400,"invalid role")
            if role=="super_admin" and actor["role"]!="super_admin": raise HTTPException(403,"Only super admins can grant super_admin")
            target.role=role
            if role=="super_admin": target.permissions=ALL_PERMISSIONS
        if "disabled" in payload: target.disabled=bool(payload["disabled"])
        if "permissions" in payload:
            requested=[p for p in payload["permissions"] if p in ALL_PERMISSIONS]
            target.permissions=requested
        target.updated_at=datetime.now(timezone.utc)
        await s.commit()
    await audit(actor,"user.update",uid,{"fields":list(payload.keys())})
    return {"ok":True}

@router.get("/settings")
async def settings(actor:dict=Depends(require_permission("settings.read"))):
    async with SessionLocal() as s:
        rows=(await s.execute(select(SystemSetting).order_by(SystemSetting.key))).scalars().all()
        return [{"key":x.key,"value":x.value,"secret":x.secret,"updated_by":x.updated_by,"updated_at":x.updated_at.isoformat()} for x in rows if not x.secret]

@router.put("/settings/{key}")
async def put_setting(key:str,payload:dict,actor:dict=Depends(require_permission("settings.write"))):
    if not key or len(key)>120: raise HTTPException(400,"invalid setting key")
    async with SessionLocal() as s:
        row=await s.get(SystemSetting,key)
        if row is None:
            row=SystemSetting(key=key,value=payload.get("value",{}),secret=False,updated_by=actor["email"])
            s.add(row)
        else:
            row.value=payload.get("value",{});row.secret=False;row.updated_by=actor["email"];row.updated_at=datetime.now(timezone.utc)
        await s.commit()
    await audit(actor,"setting.write",key,{"value_type":type(payload.get("value")).__name__})
    return {"ok":True,"key":key}

@router.get("/secrets")
async def secrets(actor:dict=Depends(require_permission("secrets.read_metadata"))):
    async with SessionLocal() as s:
        rows=(await s.execute(select(ApiSecret).order_by(ApiSecret.provider,ApiSecret.name))).scalars().all()
        return [{"id":x.id,"provider":x.provider,"name":x.name,"value":masked_secret(x.last4),"enabled":x.enabled,"updated_by":x.updated_by,"updated_at":x.updated_at.isoformat()} for x in rows]

@router.put("/secrets/{provider}/{name}")
async def put_secret(provider:str,name:str,payload:dict,actor:dict=Depends(require_permission("secrets.write"))):
    value=str(payload.get("value","")).strip()
    if len(value)<4: raise HTTPException(400,"API secret is too short")
    enc=encrypt_secret(value);last4=value[-4:]
    async with SessionLocal() as s:
        q=await s.execute(select(ApiSecret).where(ApiSecret.provider==provider,ApiSecret.name==name))
        row=q.scalar_one_or_none()
        if row is None:
            row=ApiSecret(provider=provider,name=name,encrypted_value=enc,last4=last4,enabled=bool(payload.get("enabled",True)),updated_by=actor["email"])
            s.add(row)
        else:
            row.encrypted_value=enc;row.last4=last4;row.enabled=bool(payload.get("enabled",True));row.updated_by=actor["email"];row.updated_at=datetime.now(timezone.utc)
        await s.commit()
    await audit(actor,"secret.write",f"{provider}/{name}",{"enabled":bool(payload.get("enabled",True))})
    return {"ok":True,"provider":provider,"name":name,"value":masked_secret(last4)}

@router.delete("/secrets/{secret_id}")
async def delete_secret(secret_id:int,actor:dict=Depends(require_permission("secrets.write"))):
    async with SessionLocal() as s:
        row=await s.get(ApiSecret,secret_id)
        if not row: raise HTTPException(404,"secret not found")
        target=f"{row.provider}/{row.name}"
        await s.delete(row);await s.commit()
    await audit(actor,"secret.delete",target,{})
    return {"ok":True}

@router.get("/models")
async def models(actor:dict=Depends(require_permission("models.read"))):
    async with SessionLocal() as s:
        rows=(await s.execute(select(ModelConfig).order_by(ModelConfig.task))).scalars().all()
        return [{"task":x.task,"provider":x.provider,"model":x.model,"parameters":x.parameters,"enabled":x.enabled,"updated_by":x.updated_by,"updated_at":x.updated_at.isoformat()} for x in rows]

@router.put("/models/{task}")
async def put_model(task:str,payload:dict,actor:dict=Depends(require_permission("models.write"))):
    provider=str(payload.get("provider","")).strip();model=str(payload.get("model","")).strip()
    if not provider or not model: raise HTTPException(400,"provider and model are required")
    async with SessionLocal() as s:
        row=await s.get(ModelConfig,task)
        if row is None:
            row=ModelConfig(task=task,provider=provider,model=model,parameters=payload.get("parameters",{}),enabled=bool(payload.get("enabled",True)),updated_by=actor["email"])
            s.add(row)
        else:
            row.provider=provider;row.model=model;row.parameters=payload.get("parameters",{});row.enabled=bool(payload.get("enabled",True));row.updated_by=actor["email"];row.updated_at=datetime.now(timezone.utc)
        await s.commit()
    await audit(actor,"model.write",task,{"provider":provider,"model":model,"enabled":bool(payload.get("enabled",True))})
    return {"ok":True,"task":task,"provider":provider,"model":model}

@router.get("/audit")
async def audit_log(limit:int=100,actor:dict=Depends(require_permission("audit.read"))):
    limit=max(1,min(limit,500))
    async with SessionLocal() as s:
        rows=(await s.execute(select(AuditEvent).order_by(desc(AuditEvent.created_at)).limit(limit))).scalars().all()
        return [{"id":x.id,"actor_email":x.actor_email,"action":x.action,"target":x.target,"detail":x.detail,"created_at":x.created_at.isoformat()} for x in rows]
