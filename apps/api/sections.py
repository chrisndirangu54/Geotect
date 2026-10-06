from __future__ import annotations
import math

def _dist(a,b):
    # local geodesic approximation in metres
    lat=(a["lat"]+b["lat"])/2*math.pi/180
    dx=(b["lon"]-a["lon"])*111320*math.cos(lat);dy=(b["lat"]-a["lat"])*110540
    return math.hypot(dx,dy)

def _project_to_polyline(p,line):
    best=(float("inf"),0.0)
    running=0.0
    for a,b in zip(line,line[1:]):
        lat=(a["lat"]+b["lat"])/2*math.pi/180
        ax=a["lon"]*111320*math.cos(lat);ay=a["lat"]*110540
        bx=b["lon"]*111320*math.cos(lat);by=b["lat"]*110540
        px=p["lon"]*111320*math.cos(lat);py=p["lat"]*110540
        vx,vy=bx-ax,by-ay;den=vx*vx+vy*vy
        t=max(0,min(1,((px-ax)*vx+(py-ay)*vy)/den)) if den else 0
        qx,qy=ax+t*vx,ay+t*vy
        d=math.hypot(px-qx,py-qy);station=running+t*math.sqrt(den)
        if d<best[0]:best=(d,station)
        running+=math.sqrt(den)
    return best

def build_fence_section(line:list[dict],boreholes:list[dict],max_offset_m:float=300.0)->dict:
    if len(line)<2:raise ValueError("section line requires at least 2 points")
    columns=[]
    for bh in boreholes:
        d,station=_project_to_polyline(bh["collar"],line)
        if d<=max_offset_m:
            top=float(bh["collar"]["elevation_m"])
            columns.append({"id":bh["id"],"station_m":station,"offset_m":d,"top_elevation_m":top,
              "intervals":[{"top_m":top-float(i["from_m"]),"bottom_m":top-float(i["to_m"]),"lithology":i["lithology"],"confidence":i.get("confidence",1)} for i in bh.get("intervals",[])]})
    columns.sort(key=lambda x:x["station_m"])
    return {"columns":columns,"length_m":sum(_dist(a,b) for a,b in zip(line,line[1:])), "method":"nearest projection to section polyline"}

def correlate_boreholes(boreholes:list[dict],minimum_confidence:float=.5)->dict:
    correlations=[]
    for left,right in zip(boreholes,boreholes[1:]):
        for li in left.get("intervals",[]):
            best=None
            for ri in right.get("intervals",[]):
                if str(li.get("lithology","")).lower()==str(ri.get("lithology","")).lower():
                    score=min(float(li.get("confidence",1)),float(ri.get("confidence",1)))
                    thickness_similarity=1-abs((li["to_m"]-li["from_m"])-(ri["to_m"]-ri["from_m"]))/max(li["to_m"]-li["from_m"],ri["to_m"]-ri["from_m"],1e-9)
                    score=max(0,score*(.7+.3*thickness_similarity))
                    if best is None or score>best["confidence"]:
                        best={"from_borehole":left["id"],"to_borehole":right["id"],"lithology":li["lithology"],
                              "from_interval":[li["from_m"],li["to_m"]],"to_interval":[ri["from_m"],ri["to_m"]],"confidence":round(score,3)}
            if best and best["confidence"]>=minimum_confidence:correlations.append(best)
    return {"correlations":correlations,"status":"suggested_not_verified","method":"lithology + thickness heuristic"}
