from __future__ import annotations
import math,numpy as np
from groundwater_pde import solve_steady_groundwater
from fem_solver import solve_linear_elasticity

def solve_staggered_hm(width_m:float=100,height_m:float=50,nx:int=21,ny:int=11,
                       young_ref_pa:float=50e6,poisson:float=.3,density_kg_m3:float=2000,
                       k_ref_m_s:float=1e-5,left_head_m:float=50,right_head_m:float=40,
                       stress_exponent:float=.25,permeability_exponent:float=.5,
                       biot_alpha:float=1.0,iterations:int=8,tolerance:float=1e-4)->dict:
    if nx<3 or ny<3:raise ValueError("nx and ny must be >= 3")
    E=float(young_ref_pa);k=float(k_ref_m_s);history=[];last=None
    head=None;fem=None
    for i in range(max(1,iterations)):
        gw=solve_steady_groundwater(nx=nx,ny=ny,dx_m=width_m/(nx-1),dy_m=height_m/(ny-1),k=k,left_head_m=left_head_m,right_head_m=right_head_m)
        head=np.asarray(gw["head_m"],dtype=float)
        pore=float(np.mean(head)-right_head_m)*9.81
        effective=max(density_kg_m3*9.81*height_m/2/1000-biot_alpha*pore,1.0)
        E_new=young_ref_pa*(effective/max(density_kg_m3*9.81*height_m/2/1000,1.0))**stress_exponent
        k_new=k_ref_m_s*(max(E_new/young_ref_pa,1e-6))**(-permeability_exponent)
        fem=solve_linear_elasticity(width_m,height_m,nx,ny,E_new,poisson,density_kg_m3)
        metric=max(abs(E_new-E)/max(E,1),abs(k_new-k)/max(k,1e-20))
        history.append({"iteration":i+1,"E_pa":E_new,"k_m_s":k_new,"mean_pore_pressure_kpa":pore,"max_displacement_m":fem["max_displacement_m"],"relative_change":metric})
        E=.5*E+.5*E_new;k=.5*k+.5*k_new
        if metric<tolerance:break
    return {"status":"converged" if history[-1]["relative_change"]<tolerance else "iteration_limit","iterations":len(history),
      "history":history,"head_m":head.tolist() if head is not None else None,"fem":fem,
      "method":"staggered nonlinear hydro-mechanical coupling: FD groundwater + stress-dependent stiffness/permeability + FEM",
      "assumptions":["2D","small strain","isotropic elasticity each Picard step","steady saturated groundwater","empirical E/k stress update"]}

def benchmark_suite()->dict:
    cases=[]
    # groundwater: linear head field should approximate analytical mid-head
    gw=solve_steady_groundwater(nx=21,ny=11,dx_m=5,dy_m=5,k=1e-5,left_head_m=100,right_head_m=90,tolerance=1e-8,max_iterations=20000)
    h=np.asarray(gw["head_m"]);mid=float(h[h.shape[0]//2,h.shape[1]//2]);cases.append({"name":"linear_head","expected":95.0,"actual":mid,"abs_error":abs(mid-95),"pass":abs(mid-95)<.1})
    # FEM: displacement should scale inversely with E in the linear limit
    a=solve_linear_elasticity(10,10,8,8,20e6,.3,2000);b=solve_linear_elasticity(10,10,8,8,40e6,.3,2000)
    ratio=a["max_displacement_m"]/max(b["max_displacement_m"],1e-18);cases.append({"name":"elastic_E_scaling","expected_ratio":2.0,"actual_ratio":ratio,"abs_error":abs(ratio-2),"pass":abs(ratio-2)<.15})
    # coupled solver: finite and positive outputs
    hm=solve_staggered_hm(width_m=20,height_m=10,nx=7,ny=5,iterations=3)
    ok=math.isfinite(hm["fem"]["max_displacement_m"]) and hm["fem"]["max_displacement_m"]>=0
    cases.append({"name":"coupled_smoke","pass":bool(ok),"iterations":hm["iterations"]})
    return {"passed":all(c["pass"] for c in cases),"cases":cases,"suite":"GeoTect HM regression benchmarks"}
