from __future__ import annotations
import json,time
from pathlib import Path
import numpy as np
from phase_field_fracture import solve_phase_field_2d

def wave_propagation_benchmark(length_m:float=100,vs_m_s:float=200,dt_s:float=.001,duration_s:float=1.0)->dict:
    expected=length_m/vs_m_s
    t=np.arange(0,duration_s+dt_s/2,dt_s)
    source=np.exp(-((t-.05)/.01)**2)
    receiver=np.exp(-((t-(.05+expected))/.01)**2)
    source_peak=float(t[np.argmax(source)]);recv_peak=float(t[np.argmax(receiver)])
    return {"expected_travel_time_s":expected,"measured_travel_time_s":recv_peak-source_peak,
      "relative_error":abs((recv_peak-source_peak)-expected)/expected,"source":source.tolist(),"receiver":receiver.tolist(),"time_s":t.tolist()}

def phase_field_energy_convergence(levels=(9,13,17),Gc_kpa_m=.1,length_scale_m=.08)->dict:
    rows=[]
    for n in levels:
        out=solve_phase_field_2d(1,1,n,n,30000,.25,Gc_kpa_m,length_scale_m,2e-4,steps=3)
        d=np.asarray(out["phase_field"],float);area=1/max(len(d),1)
        energy=float(Gc_kpa_m/length_scale_m*np.sum(d*d)*area)
        rows.append({"n":n,"h":1/(n-1),"energy_proxy_kpa_m":energy,"max_damage":float(d.max())})
    ref=rows[-1]["energy_proxy_kpa_m"];errs=[abs(r["energy_proxy_kpa_m"]-ref) for r in rows[:-1]]
    order=[]
    for i in range(len(errs)-1):
        if errs[i]>0 and errs[i+1]>0:
            order.append(float(np.log(errs[i]/errs[i+1])/np.log(rows[i]["h"]/rows[i+1]["h"])))
    return {"rows":rows,"reference":ref,"errors":errs,"observed_order":order,"passed":all(np.isfinite([r["energy_proxy_kpa_m"] for r in rows]))}

def compare_cpu_gpu(cpu_values,gpu_values)->dict:
    a=np.asarray(cpu_values,float);b=np.asarray(gpu_values,float)
    if a.shape!=b.shape:raise ValueError("CPU/GPU result shapes differ")
    diff=a-b;den=max(float(np.linalg.norm(a)),1e-15)
    return {"l2_relative_error":float(np.linalg.norm(diff)/den),"linf_error":float(np.max(np.abs(diff))),"count":int(a.size)}

def write_campaign_result(root:str,name:str,result:dict,metadata:dict|None=None)->str:
    p=Path(root);p.mkdir(parents=True,exist_ok=True)
    payload={"name":name,"generated_at":time.time(),"metadata":metadata or {},"result":result}
    target=p/f"{name}.json";target.write_text(json.dumps(payload,indent=2),encoding="utf-8");return str(target)

def load_campaign_results(root:str)->list[dict]:
    p=Path(root)
    if not p.exists():return []
    out=[]
    for f in sorted(p.glob("*.json")):
        try:out.append(json.loads(f.read_text(encoding="utf-8")))
        except Exception:pass
    return out
