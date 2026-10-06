from __future__ import annotations
import csv,io
import numpy as np

VALIDATION_DATASETS={
 "censeis":{"name":"CENSEIS: Centrifuge and Full-scale Modeling of Seismic Pore Pressures in Sands","doi":"10.4231/D3GF0MX4F","kind":"centrifuge/full-scale liquefaction","provider":"DesignSafe/datacenterhub"},
 "fliq":{"name":"FLIQ: Foundation and Ground Performance in Liquefaction Experiments","doi":"10.4231/D3M61BQ73","kind":"liquefaction experiments","provider":"datacenterhub"},
 "preshake":{"name":"PRESHAKE: centrifuge preshaking and liquefaction resistance","doi":"10.4231/D38K74X78","kind":"centrifuge liquefaction","provider":"datacenterhub"},
 "leap":{"name":"LEAP Centrifuge Test and Numerical Simulation Specifications","doi":"10.17603/DS2159T","kind":"centrifuge benchmark","provider":"datacenterhub"},
 "ngl":{"name":"Next Generation Liquefaction Database","kind":"field case histories","provider":"DesignSafe/NGL"}
}
def dataset_catalog():return VALIDATION_DATASETS
def parse_series_csv(text:str,time_col:str,value_cols:list[str])->dict:
    r=csv.DictReader(io.StringIO(text));times=[];values={k:[] for k in value_cols}
    for row in r:
        times.append(float(row[time_col]))
        for k in value_cols:values[k].append(float(row[k]))
    return {"time":times,"values":values}
def align_series(obs_t,obs_y,sim_t,sim_y):
    ot=np.asarray(obs_t,float);oy=np.asarray(obs_y,float);st=np.asarray(sim_t,float);sy=np.asarray(sim_y,float)
    if len(ot)<2 or len(st)<2:raise ValueError("need at least two points")
    return ot,oy,np.interp(ot,st,sy)
def validation_metrics(obs_t,obs_y,sim_t,sim_y)->dict:
    t,o,s=align_series(obs_t,obs_y,sim_t,sim_y);err=s-o
    rmse=float(np.sqrt(np.mean(err**2)));mae=float(np.mean(np.abs(err)));bias=float(np.mean(err))
    denom=float(np.sum((o-o.mean())**2));r2=1-float(np.sum(err**2))/denom if denom>0 else None
    peak_obs=float(np.max(np.abs(o)));peak_sim=float(np.max(np.abs(s)));peak_rel=abs(peak_sim-peak_obs)/max(peak_obs,1e-12)
    return {"rmse":rmse,"mae":mae,"bias":bias,"r2":r2,"peak_observed":peak_obs,"peak_simulated":peak_sim,"peak_relative_error":peak_rel,"n":len(t)}
def validate_channels(observed:dict,simulated:dict,channel_map:dict)->dict:
    results={};passes=[]
    for name,spec in channel_map.items():
        m=validation_metrics(observed["time"],observed[spec["observed"]],simulated["time"],simulated[spec["simulated"]]);tol=spec.get("tolerances",{})
        ok=(m["peak_relative_error"]<=float(tol.get("peak_relative_error",.2)) and (m["r2"] is None or m["r2"]>=float(tol.get("r2",.7))))
        m["pass"]=ok;results[name]=m;passes.append(ok)
    return {"passed":all(passes) if passes else False,"channels":results}
def shake_table_objective(observed_accel,sim_accel,observed_pressure=None,sim_pressure=None)->dict:
    out={"acceleration":validation_metrics(range(len(observed_accel)),observed_accel,range(len(sim_accel)),sim_accel)}
    if observed_pressure is not None and sim_pressure is not None:out["pore_pressure"]=validation_metrics(range(len(observed_pressure)),observed_pressure,range(len(sim_pressure)),sim_pressure)
    return {"score":sum(v["rmse"] for v in out.values())/len(out),"metrics":out}
