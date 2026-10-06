"""Offline GeoTect edge gateway.

Stores telemetry locally in SQLite, evaluates simple rules without internet,
and can forward buffered readings to a configured cloud endpoint when online.
"""
import json,os,sqlite3,time,urllib.request
DB=os.getenv("EDGE_DB","geotect-edge.db");CLOUD=os.getenv("GEOTECT_EDGE_FORWARD_URL","")
RULES=json.loads(os.getenv("EDGE_RULES",'[]'))
con=sqlite3.connect(DB);con.execute("create table if not exists readings(id integer primary key,ts real,payload text,sent integer default 0)");con.commit()

def evaluate(payload):
    fired=[]
    for r in RULES:
        v=payload.get(r.get("field"));threshold=r.get("value")
        if v is not None and threshold is not None and ((r.get("op","gt")=="gt" and v>threshold) or (r.get("op")=="lt" and v<threshold)):
            fired.append(r)
    return fired

def ingest(payload):
    fired=evaluate(payload);con.execute("insert into readings(ts,payload,sent) values(?,?,0)",(time.time(),json.dumps(payload)));con.commit()
    if fired:print(json.dumps({"edge_alarm":fired,"payload":payload}),flush=True)
    return fired

def flush():
    if not CLOUD:return
    for rid,payload in con.execute("select id,payload from readings where sent=0 order by id limit 100"):
        try:
            req=urllib.request.Request(CLOUD,data=payload.encode(),headers={"Content-Type":"application/json"},method="POST")
            urllib.request.urlopen(req,timeout=5).read();con.execute("update readings set sent=1 where id=?",(rid,));con.commit()
        except Exception:return

if __name__=="__main__":
    print("GeoTect edge gateway ready; import ingest() from device adapter.",flush=True)
    while True:flush();time.sleep(10)
