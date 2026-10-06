from __future__ import annotations
import numpy as np, math

def monte_carlo_slope(samples:int,slope_deg:float,friction_mean:float,friction_sd:float,cohesion_mean_kpa:float,cohesion_sd_kpa:float,
                      gamma_mean:float=18,gamma_sd:float=1.0,depth_m:float=3,saturation_mean:float=.5,saturation_sd:float=.15,seed:int=42)->dict:
    rng=np.random.default_rng(seed);n=max(100,min(int(samples),200000));beta=math.radians(slope_deg)
    phi=np.radians(rng.normal(friction_mean,friction_sd,n));c=np.maximum(rng.normal(cohesion_mean_kpa,cohesion_sd_kpa,n),0)
    gamma=np.maximum(rng.normal(gamma_mean,gamma_sd,n),1);sat=np.clip(rng.normal(saturation_mean,saturation_sd,n),0,1)
    normal=gamma*depth_m*np.cos(beta)**2;effective=normal*(1-.65*sat)
    resisting=c+effective*np.tan(phi);driving=np.maximum(gamma*depth_m*np.sin(beta)*np.cos(beta),1e-6)
    fos=resisting/driving;pf=float(np.mean(fos<1))
    return {"samples":n,"probability_of_failure":pf,"reliability_index_approx":float(-np.log10(max(pf,1/n))),
      "fos":{"p05":float(np.quantile(fos,.05)),"p50":float(np.quantile(fos,.5)),"p95":float(np.quantile(fos,.95))},
      "method":"Monte Carlo infinite-slope screening","status":"probabilistic_screening"}

def conditional_idw(samples:list[dict],targets:list[dict],power:float=2)->dict:
    out=[]
    for t in targets:
        x,y=float(t["x"]),float(t["y"]);weights=[];vals=[]
        for s in samples:
            d=max(math.hypot(x-float(s["x"]),y-float(s["y"])),1e-9);w=1/d**power;weights.append(w);vals.append(float(s["value"]))
        if not weights: out.append({**t,"estimate":None,"variance":None});continue
        w=np.asarray(weights);v=np.asarray(vals);est=float((w*v).sum()/w.sum());var=float((w*(v-est)**2).sum()/w.sum())
        out.append({**t,"estimate":est,"variance":var,"confidence":float(1/(1+math.sqrt(var)/(abs(est)+1e-9)))})
    return {"targets":out,"method":"conditional IDW baseline"}
