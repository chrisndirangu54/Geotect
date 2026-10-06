from __future__ import annotations
AGENTS={
 "geology":{"skills":["stratigraphy","faults","borehole_correlation","uncertainty"]},
 "hydrogeology":{"skills":["groundwater","seepage","pore_pressure","modflow"]},
 "geophysics":{"skills":["ert","seismic","masw","gravity","magnetics"]},
 "geotechnical":{"skills":["soil_rock","foundations","slopes","tunnels","constitutive_models"]},
 "monitoring":{"skills":["iot","insar","slope_radar","anomaly_detection"]},
 "reporting":{"skills":["evidence","approvals","reports","standards"]}
}
def route_agent(task:str)->dict:
    low=task.lower();scores={}
    for name,a in AGENTS.items():
        scores[name]=sum(1 for s in a["skills"] if s.replace("_"," ") in low or s in low)
    best=max(scores,key=scores.get)
    return {"agent":best,"scores":scores,"capabilities":AGENTS[best]["skills"]}

def evidence_answer(question:str,evidence:list[dict],recommendation:str,confidence:float)->dict:
    refs=[{"id":e.get("id"),"type":e.get("type"),"source":e.get("source"),"version":e.get("version"),"observed_at":e.get("observed_at")} for e in evidence]
    return {"question":question,"recommendation":recommendation,"confidence":max(0,min(confidence,1)),"evidence_refs":refs,
      "evidence_count":len(refs),"warning":None if refs else "No evidence was attached; recommendation must not be treated as grounded."}

def anomaly_zscore(series:list[float],threshold:float=3)->dict:
    import numpy as np
    a=np.asarray(series,dtype=float)
    if len(a)<3:return {"anomalies":[]}
    mean=float(a.mean());sd=float(a.std()) or 1.0;z=(a-mean)/sd
    return {"mean":mean,"std":sd,"anomalies":[{"index":i,"value":float(a[i]),"z":float(z[i])} for i in range(len(a)) if abs(z[i])>=threshold]}

def rank_root_causes(observed:dict,candidates:list[dict])->dict:
    ranked=[]
    for c in candidates:
        score=0.0;matched=[]
        for k,w in c.get("signals",{}).items():
            if k in observed:
                val=float(observed[k]);target=float(w.get("target",0));tol=max(float(w.get("tolerance",1)),1e-9)
                contribution=max(0,1-abs(val-target)/tol)*float(w.get("weight",1));score+=contribution
                if contribution>0:matched.append(k)
        ranked.append({"cause":c.get("cause"),"score":score,"matched_signals":matched})
    ranked.sort(key=lambda x:x["score"],reverse=True)
    return {"ranked_causes":ranked}

def select_models(context:dict)->dict:
    soil=str(context.get("soil","")).lower();rock=bool(context.get("rock"));staged=bool(context.get("staged_construction"));groundwater=bool(context.get("groundwater"))
    constitutive="Hoek-Brown" if rock else "Modified Cam Clay" if "clay" in soil else "Hardening Soil" if staged else "Mohr-Coulomb"
    flow="MODFLOW 6" if groundwater and context.get("regional_scale") else "coupled seepage FEM" if groundwater else "none"
    return {"constitutive_model":constitutive,"groundwater_model":flow,"dynamic":bool(context.get("seismic"))}
