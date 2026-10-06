from __future__ import annotations
import os
from functools import lru_cache
from fastapi import Header,HTTPException,Depends
from sqlalchemy import select
from db import SessionLocal
from admin_models import AppUser

BOOTSTRAP_SUPER_ADMIN=os.getenv("GEOTECT_SUPER_ADMIN_EMAIL","chrisndirangu54@gmail.com").strip().lower()
DEV_AUTH=os.getenv("GEOTECT_DEV_AUTH","false").lower()=="true"

ALL_PERMISSIONS=[
 "users.read","users.write","users.disable","roles.manage",
 "settings.read","settings.write","secrets.read_metadata","secrets.write",
 "models.read","models.write","audit.read","projects.read_all","projects.write_all",
 "jobs.execute","jobs.cancel","system.manage"
]

@lru_cache
def _firebase_app():
    try:
        import firebase_admin
        from firebase_admin import credentials
        if not firebase_admin._apps:
            cred_path=os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
            if cred_path: firebase_admin.initialize_app(credentials.Certificate(cred_path))
            else: firebase_admin.initialize_app()
        return firebase_admin.get_app()
    except Exception as exc:
        raise RuntimeError("Firebase Admin is not configured") from exc

def verify_token(token:str)->dict:
    if DEV_AUTH and token=="dev-super-admin":
        return {"uid":"dev-super-admin","email":BOOTSTRAP_SUPER_ADMIN,"name":"GeoTect Super Admin","email_verified":True}
    try:
        _firebase_app()
        from firebase_admin import auth
        decoded=auth.verify_id_token(token,check_revoked=True)
        if not decoded.get("email"): raise ValueError("Token has no email")
        return decoded
    except Exception as exc:
        raise HTTPException(status_code=401,detail="Invalid or expired authentication token") from exc

async def current_user(authorization:str|None=Header(default=None))->dict:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(401,"Bearer token required")
    token=authorization.split(" ",1)[1].strip()
    claims=verify_token(token)
    uid=str(claims["uid"]);email=str(claims["email"]).lower()
    async with SessionLocal() as s:
        user=await s.get(AppUser,uid)
        if not user:
            role="super_admin" if email==BOOTSTRAP_SUPER_ADMIN else "user"
            perms=ALL_PERMISSIONS if role=="super_admin" else []
            user=AppUser(uid=uid,email=email,display_name=claims.get("name"),role=role,permissions=perms)
            s.add(user);await s.commit();await s.refresh(user)
        elif email==BOOTSTRAP_SUPER_ADMIN and user.role!="super_admin":
            user.role="super_admin";user.permissions=ALL_PERMISSIONS;await s.commit()
        if user.disabled: raise HTTPException(403,"Account disabled")
        return {"uid":user.uid,"email":user.email,"display_name":user.display_name,"role":user.role,"permissions":user.permissions}

def require_permission(permission:str):
    async def dependency(user:dict=Depends(current_user)):
        if user["role"]=="super_admin" or permission in user["permissions"]: return user
        raise HTTPException(403,f"Missing permission: {permission}")
    return dependency
