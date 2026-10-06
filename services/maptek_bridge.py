"""GeoTect local bridge for Maptek Python SDK compatible applications."""
import json,os,time,urllib.request
from mapteksdk.project import Project

BASE=os.environ["GEOTECT_URL"].rstrip("/");CONNECTION=os.environ["GEOTECT_CONNECTION_ID"];TOKEN=os.environ["GEOTECT_BRIDGE_TOKEN"]
project=Project()

def handle(command,payload):
    if command=="health":return {"connected":True,"maptek_project":True}
    if command=="find_object":
        oid=project.find_object(str(payload["path"]))
        return {"object_id":str(oid)}
    if command=="list_children":
        oid=project.find_object(str(payload["path"]))
        return {"children":[str(x) for x in project.get_children(oid)]}
    raise ValueError(f"Unsupported command {command}")

def req(path,method="GET",data=None):
    h={"X-GeoTect-Bridge-Token":TOKEN,"Content-Type":"application/json"}
    q=urllib.request.Request(BASE+path,data=json.dumps(data).encode() if data is not None else None,headers=h,method=method)
    with urllib.request.urlopen(q,timeout=30) as r:return json.loads(r.read().decode())

while True:
    try:
        item=req(f"/api/v1/integrations/bridge/{CONNECTION}/poll")
        if not item.get("command"):time.sleep(2);continue
        try:body={"ok":True,"result":handle(item["command"],item.get("payload",{}))}
        except Exception as exc:body={"ok":False,"error":str(exc)}
        req(f"/api/v1/integrations/bridge/{CONNECTION}/result/{item['id']}","POST",body)
    except Exception as exc:print("bridge error:",exc,flush=True);time.sleep(5)
