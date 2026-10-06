from __future__ import annotations
import math,numpy as np
from elastoplastic_fem import solve_elastoplastic_2d
from biot_solver import solve_biot_1d
from richards_solver import solve_richards_1d
from coupled_up_fem import solve_monolithic_up_2d

def observed_order(errors:list[float],hs:list[float])->dict:
    pairs=[]
    for i in range(len(errors)-1):
        if errors[i]>0 and errors[i+1]>0 and hs[i]!=hs[i+1]:
            p=math.log(errors[i]/errors[i+1])/math.log(hs[i]/hs[i+1]);pairs.append(float(p))
    return {"pairwise_order":pairs,"mean_order":float(np.mean(pairs)) if pairs else None}

def elastic_mesh_convergence(levels:list[int]|None=None)->dict:
    levels=levels or [4,6,9,13];vals=[]
    mat={"model":"mohr_coulomb","E_kpa":30000,"nu":.3,"cohesion_kpa":1e9,"friction_deg":0}
    for n in levels:
        out=solve_elastoplastic_2d(10,5,n,max(3,n//2+1),mat,density_kg_m3=0,top_pressure_kpa=10,load_steps=1,newton_max=12)
        vals.append({"n":n,"h":10/(n-1),"value":out["max_displacement_m"],"status":out["status"]})
    ref=vals[-1]["value"];errors=[abs(x["value"]-ref) for x in vals[:-1]]
    hs=[x["h"] for x in vals[:-1]]
    return {"study":"elastic_mesh","levels":vals,"reference":ref,"errors":errors,"order":observed_order(errors,hs)}

def biot_spatial_convergence(levels:list[int]|None=None)->dict:
    levels=levels or [11,21,41,81];vals=[]
    for n in levels:
        out=solve_biot_1d(10,n,30e6,.3,1e-9,9810,1,1e-9,100e3,1800,12)
        vals.append({"n":n,"h":10/(n-1),"value":out["series"][-1]["top_settlement_m"]})
    ref=vals[-1]["value"];errors=[abs(x["value"]-ref) for x in vals[:-1]];hs=[x["h"] for x in vals[:-1]]
    return {"study":"biot_spatial","levels":vals,"reference":ref,"errors":errors,"order":observed_order(errors,hs)}

def richards_time_convergence(dts:list[float]|None=None)->dict:
    dts=dts or [240,120,60,30];T=3600;vals=[]
    for dt in dts:
        out=solve_richards_1d(1,31,-1,.05,.45,1.6,1.6,1e-5,dt,int(T/dt),top_flux_m_s=1e-7)
        vals.append({"dt":dt,"value":float(np.mean(out["theta"]))})
    ref=vals[-1]["value"];errors=[abs(x["value"]-ref) for x in vals[:-1]];hs=[x["dt"] for x in vals[:-1]]
    return {"study":"richards_time","levels":vals,"reference":ref,"errors":errors,"order":observed_order(errors,hs)}

def coupled_smoke_matrix()->dict:
    cases=[]
    for backend in ["auto"]:
        out=solve_monolithic_up_2d(4,2,3,3,
          {"model":"mohr_coulomb","E_kpa":50000,"nu":.3,"cohesion_kpa":1e6,"friction_deg":0},
          {"ks_m_s":1e-6,"theta_r":.05,"theta_s":.45,"alpha_1_m":1.6,"n_vg":1.6,"specific_storage_1_kpa":1e-7},
          dt_s=60,steps=1,density_kg_m3=0,top_pressure_kpa=1,initial_pore_pressure_kpa=0,backend=backend,newton_max=8,tolerance=1e-5,parallel_assembly=False)
        cases.append({"backend":backend,"status":out["status"],"finite":bool(np.isfinite(out["max_displacement_m"] if "max_displacement_m" in out else np.max(np.linalg.norm(np.asarray(out["displacement_m"]),axis=1))))})
    return {"study":"coupled_backend_matrix","cases":cases,"passed":all(x["finite"] for x in cases)}

def full_matrix()->dict:
    studies=[elastic_mesh_convergence(),biot_spatial_convergence(),richards_time_convergence(),coupled_smoke_matrix()]
    return {"studies":studies,"passed":studies[-1]["passed"]}
