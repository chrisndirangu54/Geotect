"""GeoTect ↔ Micromine Origin & Beyond local bridge.

Run from Micromine's Python environment (or compatible configured Python).
The bridge intentionally limits commands to explicit MMpy operations.
"""
import json,os,time,urllib.request
import MMpy

BASE=os.environ["GEOTECT_URL"].rstrip("/")
CONNECTION=os.environ["GEOTECT_CONNECTION_ID"]
TOKEN=os.environ["GEOTECT_BRIDGE_TOKEN"]

def handle(command,payload):
    if command=="health":return {"connected":True,"mmpy":True}
    if command=="run_command":
        cmd=MMpy.Command(str(payload["command"]))
        result=cmd.run()
        return {"result":str(result)}
    if command=="block_model_info":
        bm=MMpy.BlockModel();bm.open(str(payload["path"]))
        try:return {"records_count":bm.records_count(),"structure":str(bm.structure())}
        finally:bm.close()
    raise ValueError(f"Unsupported bridge command: {command}")

def request(path,method="GET",data=None):
    headers={"X-GeoTect-Bridge-Token":TOKEN,"Content-Type":"application/json"}
    req=urllib.request.Request(BASE+path,data=json.dumps(data).encode() if data is not None else None,headers=headers,method=method)
    with urllib.request.urlopen(req,timeout=30) as r:return json.loads(r.read().decode())

while True:
    try:
        item=request(f"/api/v1/integrations/bridge/{CONNECTION}/poll")
        if not item.get("command"):time.sleep(2);continue
        try:body={"ok":True,"result":handle(item["command"],item.get("payload",{}))}
        except Exception as exc:body={"ok":False,"error":str(exc)}
        request(f"/api/v1/integrations/bridge/{CONNECTION}/result/{item['id']}","POST",body)
    except Exception as exc:
        print("bridge error:",exc,flush=True);time.sleep(5)
