from __future__ import annotations
import json,urllib.request
def dispatch(channel:str,target:str,message:str,config:dict|None=None)->dict:
    cfg=config or {}
    if channel=="webhook":
        req=urllib.request.Request(target,data=json.dumps({"message":message}).encode(),headers={"Content-Type":"application/json"},method="POST")
        with urllib.request.urlopen(req,timeout=float(cfg.get("timeout",5))) as r:return {"channel":channel,"status":r.status}
    if channel in {"email","sms","whatsapp","slack","teams"}:
        return {"channel":channel,"status":"connector_required","target":target,"payload":{"message":message},
                "note":"Configure the provider connector/API credential in GeoTect Admin."}
    return {"channel":channel,"status":"unsupported"}
