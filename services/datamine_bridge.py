"""GeoTect local bridge for Datamine Studio products.

Run on Windows with Datamine installed. Datamine Studio exposes COM automation
through the DmApplication object and approved ActiveX automation interfaces.
"""
import json,os,time,urllib.request
try:import win32com.client
except ImportError:raise SystemExit("Install pywin32 in the Datamine workstation Python environment.")

BASE=os.environ["GEOTECT_URL"].rstrip("/");CONNECTION=os.environ["GEOTECT_CONNECTION_ID"];TOKEN=os.environ["GEOTECT_BRIDGE_TOKEN"]
PROGID=os.getenv("DATAMINE_PROGID","DatamineStudio.Application")
app=win32com.client.Dispatch(PROGID)

def handle(command,payload):
    if command=="health":return {"connected":True,"progid":PROGID}
    if command=="run_command":
        name=str(payload["command"]);args=payload.get("args",{})
        # DmApplication implementations differ across Studio products/versions.
        # Invoke only a named, explicitly requested command; do not eval arbitrary code.
        fn=getattr(app,name)
        result=fn(**args) if isinstance(args,dict) else fn(*args)
        return {"result":str(result)}
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
