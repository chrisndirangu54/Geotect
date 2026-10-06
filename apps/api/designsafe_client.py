from __future__ import annotations
import os,hashlib
import httpx

DEFAULT_BASE=os.getenv("DESIGNSAFE_TAPIS_BASE","https://designsafe.tapis.io")

class DesignSafeClient:
    def __init__(self,token:str,base_url:str=DEFAULT_BASE):
        self.token=token;self.base=base_url.rstrip("/")
        if not self.base.startswith("https://"):raise ValueError("DesignSafe/Tapis base URL must use HTTPS")
    def _headers(self):
        return {"X-Tapis-Token":self.token,"Authorization":f"Bearer {self.token}","Accept":"application/json"}
    async def list_files(self,system_id:str,path:str="")->dict:
        safe=path.replace("..","").lstrip("/")
        url=f"{self.base}/v3/files/ops/{system_id}/{safe}"
        async with httpx.AsyncClient(timeout=60) as client:
            r=await client.get(url,headers=self._headers());r.raise_for_status();return r.json()
    async def download(self,system_id:str,path:str,dest:str)->dict:
        safe=path.replace("..","").lstrip("/")
        url=f"{self.base}/v3/files/content/{system_id}/{safe}"
        h=hashlib.sha256();size=0
        async with httpx.AsyncClient(timeout=None,follow_redirects=True) as client:
            async with client.stream("GET",url,headers=self._headers()) as r:
                r.raise_for_status()
                with open(dest,"wb") as f:
                    async for chunk in r.aiter_bytes(1024*1024):
                        f.write(chunk);h.update(chunk);size+=len(chunk)
        return {"path":dest,"bytes":size,"sha256":h.hexdigest(),"system_id":system_id,"source_path":path}

def published_corral_path(project_id:str)->str:
    if not project_id.startswith("PRJ-"):raise ValueError("expected DesignSafe published project id")
    return f"/corral/projects/NHERI/published/{project_id}/"

def nees_corral_path(project_id:str)->str:
    return f"/corral/projects/NHERI/public/projects/{project_id}/"
