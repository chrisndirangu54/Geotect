"""GeoTect ↔ Archicad local bridge.

Runs on the workstation where Archicad is open. Uses Graphisoft's official
Archicad-Python Connection package, which communicates with Archicad via the
Automation API's HTTP/JSON channel.
"""
import json,os,time,urllib.request
from archicad import ACConnection

BASE=os.environ["GEOTECT_URL"].rstrip("/")
CONNECTION=os.environ["GEOTECT_CONNECTION_ID"]
TOKEN=os.environ["GEOTECT_BRIDGE_TOKEN"]
conn=ACConnection.connect()
if not conn:raise SystemExit("Could not connect to Archicad. Start Archicad and enable the Automation API.")
acc=conn.commands;act=conn.types;acu=conn.utilities

def handle(command,payload):
    if command=="health":return {"connected":True,"archicad":True}
    if command=="get_all_elements":
        ids=acc.GetAllElements()
        return {"element_ids":[str(getattr(x,"elementId",x)) for x in ids]}
    if command=="get_selected_elements":
        ids=acc.GetSelectedElements()
        return {"element_ids":[str(getattr(x,"elementId",x)) for x in ids]}
    if command=="execute_addon_command":
        # Add-on command execution is deliberately explicit: command namespace/name and parameters
        # must be provided by an installed, trusted Archicad Add-On.
        cmd=act.AddOnCommandId(payload["namespace"],payload["name"])
        return {"result":acc.ExecuteAddOnCommand(cmd,payload.get("parameters"))}
    raise ValueError(f"Unsupported bridge command: {command}")

def request(path,method="GET",data=None):
    headers={"X-GeoTect-Bridge-Token":TOKEN,"Content-Type":"application/json"}
    req=urllib.request.Request(BASE+path,data=json.dumps(data).encode() if data is not None else None,headers=headers,method=method)
    with urllib.request.urlopen(req,timeout=30) as r:return json.loads(r.read().decode())

while True:
    try:
        item=request(f"/api/v1/integrations/bridge/{CONNECTION}/poll")
        if not item.get("command"):time.sleep(2);continue
        try:result=handle(item["command"],item.get("payload",{}));body={"ok":True,"result":result}
        except Exception as exc:body={"ok":False,"error":str(exc)}
        request(f"/api/v1/integrations/bridge/{CONNECTION}/result/{item['id']}","POST",body)
    except Exception as exc:
        print("bridge error:",exc,flush=True);time.sleep(5)
