from __future__ import annotations
def compute_health(asset:dict,observations:list[dict])->dict:
    score=1.0;reasons=[]
    weights={"critical":.35,"warning":.12,"maintenance_due":.10,"accelerating":.18,"out_of_range":.15}
    for o in observations:
        flag=str(o.get("flag",o.get("status",""))).lower()
        if flag in weights:score-=weights[flag]*float(o.get("weight",1));reasons.append({"flag":flag,"impact":weights[flag]*float(o.get("weight",1))})
    score=max(0,min(score,1));status="critical" if score<.35 else "degraded" if score<.7 else "normal"
    return {"asset_id":asset.get("id"),"health_score":score,"status":status,"reasons":reasons}

def failure_modes(asset_type:str)->list[str]:
    return {"dam":["overtopping","internal_erosion","slope_instability","foundation_failure"],
            "slope":["sliding","rockfall","erosion"],"bridge":["settlement","scour","fatigue","bearing_failure"],
            "tunnel":["convergence","lining_distress","water_ingress"],"pipeline":["settlement","leak","buckling"],
            "road":["settlement","slope_failure","washout"]}.get(asset_type,["condition_degradation"])
