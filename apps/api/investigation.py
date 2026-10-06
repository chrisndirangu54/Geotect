from __future__ import annotations
import math

def recommend_locations(candidates:list[dict],observations:list[dict],count:int=5,min_spacing_m:float=50)->dict:
    """Greedy information-gain proxy: uncertainty * remoteness * hazard/importance."""
    selected=[];pool=[]
    for c in candidates:
        nearest=min([math.hypot(float(c["x"])-float(o["x"]),float(c["y"])-float(o["y"])) for o in observations] or [1e9])
        score=float(c.get("uncertainty",1))*math.log1p(nearest)*float(c.get("importance",1))*float(c.get("hazard_weight",1))
        pool.append({**c,"information_gain_score":score,"nearest_observation_m":nearest})
    for c in sorted(pool,key=lambda x:x["information_gain_score"],reverse=True):
        if all(math.hypot(float(c["x"])-float(s["x"]),float(c["y"])-float(s["y"]))>=min_spacing_m for s in selected):
            selected.append(c)
            if len(selected)>=count: break
    return {"recommendations":selected,"method":"greedy uncertainty-distance-importance information-gain proxy","status":"planning_support"}

def choose_method(context:dict)->dict:
    targets=[]
    if context.get("depth_m",0)<=10: targets+=["GPR","test pits"]
    if context.get("groundwater"): targets+=["piezometer","ERT"]
    if context.get("stiffness_contrast"): targets+=["seismic refraction","MASW"]
    if context.get("conductivity_contrast"): targets+=["ERT","IP"]
    if context.get("foundation"): targets+=["CPT","borehole","SPT"]
    if context.get("slope"): targets+=["inclinometer","piezometer","borehole"]
    return {"recommended_methods":list(dict.fromkeys(targets or ["borehole","CPT"]))}
