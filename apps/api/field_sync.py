from __future__ import annotations
from hashlib import sha256
def merge_offline_records(server:list[dict],incoming:list[dict])->dict:
    by_id={str(x["id"]):x for x in server};conflicts=[]
    for row in incoming:
        rid=str(row["id"]);local=dict(row);remote=by_id.get(rid)
        if not remote:by_id[rid]=local;continue
        lv=str(local.get("updated_at",""));rv=str(remote.get("updated_at",""))
        if local.get("base_version") is not None and local.get("base_version")!=remote.get("version"):
            conflicts.append({"id":rid,"server":remote,"incoming":local});continue
        if lv>=rv:by_id[rid]=local
    return {"records":list(by_id.values()),"conflicts":conflicts,"strategy":"version-aware last-write-wins with conflict capture"}

def media_manifest(filename:str,data:bytes,metadata:dict)->dict:
    return {"filename":filename,"sha256":sha256(data).hexdigest(),"bytes":len(data),"metadata":metadata}
