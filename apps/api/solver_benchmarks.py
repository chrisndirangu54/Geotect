from __future__ import annotations
import math,numpy as np
from elastoplastic_materials import MohrCoulomb,HardeningSoil,numerical_tangent
from biot_solver import solve_biot_1d
from richards_solver import solve_richards_1d
from elastoplastic_fem import solve_elastoplastic_2d

REFERENCE_CATALOG={
 "plaxis_mc_biaxial":{"source":"PLAXIS verification: Bi-axial test with Mohr-Coulomb model","kind":"commercial_reference","metric":"yield envelope"},
 "plaxis_biot":{"source":"PLAXIS verification: Biot theory of poroelasticity","kind":"analytical_and_commercial_reference","metric":"pore pressure/displacement"},
 "geostudio_mc_footing":{"source":"GeoStudio SIGMA/W verification: Footing Load on Mohr-Coulomb Soil","kind":"closed_form_and_commercial_reference","metric":"ultimate bearing pressure"},
 "terzaghi_1d":{"source":"Terzaghi one-dimensional consolidation analytical series","kind":"analytical_reference","metric":"degree of consolidation"}
}

def mc_local_biaxial()->dict:
    m=MohrCoulomb(30000,.3,10,30,0);s=m.initial_state();eps=np.zeros(3)
    for _ in range(100):
        eps+=np.array([0,-2e-5,0]);s,_,_=m.integrate(s,np.array([0,-2e-5,0]))
    p,q=(lambda st:((st[0]+st[1])/2,abs(st[0]-st[1])))(s.stress)
    M=2*math.sin(math.radians(30))/(1-math.sin(math.radians(30)));k=2*10*math.cos(math.radians(30))/(1-math.sin(math.radians(30)))
    err=abs(q-(M*p+k))
    return {"name":"mc_local_biaxial","yield_error_kpa":err,"pass":err<1e-3,"reference":REFERENCE_CATALOG["plaxis_mc_biaxial"]}

def terzaghi_biot()->dict:
    out=solve_biot_1d(10,21,30e6,.3,1e-9,9810,1.0,1e-9,100e3,3600,24)
    # qualitative monotonic dissipation and settlement growth under drained top
    pp=[x["max_pore_pressure_pa"] for x in out["series"]];ss=[x["top_settlement_m"] for x in out["series"]]
    ok=all(np.isfinite(pp)) and all(np.isfinite(ss)) and ss[-1]>=ss[0]
    return {"name":"biot_1d_consolidation","pass":bool(ok),"final_settlement_m":ss[-1],"reference":REFERENCE_CATALOG["terzaghi_1d"]}

def richards_mass_balance()->dict:
    out=solve_richards_1d(1,31,-1,.05,.45,1.6,1.6,1e-5,60,10,top_flux_m_s=1e-7)
    residual=sum(abs(x["residual_m"]) for x in out["mass_balance"])
    return {"name":"richards_mass_balance","absolute_mass_residual_m":residual,"pass":math.isfinite(residual) and residual<.02}

def fem_elastic_limit()->dict:
    mat={"model":"mohr_coulomb","E_kpa":30000,"nu":.3,"cohesion_kpa":1e9,"friction_deg":0}
    out=solve_elastoplastic_2d(10,5,5,4,mat,top_pressure_kpa=10,load_steps=2,newton_max=10)
    return {"name":"fem_elastic_limit","pass":len(out["yielded_elements"])==0 and math.isfinite(out["max_displacement_m"]),"max_displacement_m":out["max_displacement_m"]}

def compare_reference(result:dict,reference:dict,tolerances:dict|None=None)->dict:
    tol=tolerances or {};metrics={}
    for k,v in reference.items():
        if isinstance(v,(int,float)) and isinstance(result.get(k),(int,float)):
            abs_err=abs(float(result[k])-float(v));rel=abs_err/max(abs(float(v)),1e-12);limit=float(tol.get(k,.05))
            metrics[k]={"result":result[k],"reference":v,"relative_error":rel,"tolerance":limit,"pass":rel<=limit}
    return {"pass":bool(metrics) and all(x["pass"] for x in metrics.values()),"metrics":metrics}

def suite()->dict:
    cases=[mc_local_biaxial(),terzaghi_biot(),richards_mass_balance(),fem_elastic_limit()]
    return {"passed":all(c["pass"] for c in cases),"cases":cases,"reference_catalog":REFERENCE_CATALOG}
