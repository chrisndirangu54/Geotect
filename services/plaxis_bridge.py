"""GeoTect local bridge for PLAXIS 2D/3D Remote Scripting."""
import json,os,time,urllib.request
from plxscripting.easy import new_server

BASE=os.environ["GEOTECT_URL"].rstrip("/");CONNECTION=os.environ["GEOTECT_CONNECTION_ID"];TOKEN=os.environ["GEOTECT_BRIDGE_TOKEN"]
HOST=os.getenv("PLAXIS_HOST","localhost");PORT=int(os.getenv("PLAXIS_PORT","10000"));PASSWORD=os.environ["PLAXIS_PASSWORD"]
server,g=new_server(HOST,PORT,password=PASSWORD)

def handle(command,payload):
    if command=="health":return {"connected":True,"host":HOST,"port":PORT}
    if command=="calculate":
        result=g.calculate()
        return {"result":str(result)}
    if command=="get_phases":
        return {"phases":[str(x) for x in g.Phases[:]]}
    if command=="get_project_title":
        return {"title":str(g.Project.Title.value)}
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
