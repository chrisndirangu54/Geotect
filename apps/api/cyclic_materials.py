from __future__ import annotations
from dataclasses import dataclass
import math

@dataclass
class CyclicState:
    strain:float=0.0
    stress_kpa:float=0.0
    reversal_strain:float=0.0
    reversal_stress_kpa:float=0.0
    direction:int=0
    dissipated_energy_kpa:float=0.0

def hardin_drnevich_backbone(gamma:float,gmax_kpa:float,gamma_ref:float)->float:
    return gmax_kpa*gamma/(1+abs(gamma)/max(gamma_ref,1e-12))

def masing_step(state:CyclicState,strain:float,gmax_kpa:float,gamma_ref:float)->CyclicState:
    ds=strain-state.strain;direction=1 if ds>0 else -1 if ds<0 else state.direction
    rev=state.direction!=0 and direction!=0 and direction!=state.direction
    rs=state.reversal_strain if not rev else state.strain
    rt=state.reversal_stress_kpa if not rev else state.stress_kpa
    if state.direction==0 or rev:
        rs=state.strain;rt=state.stress_kpa
    local=(strain-rs)/2
    stress=rt+2*hardin_drnevich_backbone(local,gmax_kpa,gamma_ref)
    energy=state.dissipated_energy_kpa+.5*(state.stress_kpa+stress)*(strain-state.strain)
    return CyclicState(strain,stress,rs,rt,direction,energy)

def cyclic_series(strains:list[float],gmax_kpa:float,gamma_ref:float)->dict:
    s=CyclicState();hist=[]
    for e in strains:
        s=masing_step(s,float(e),gmax_kpa,gamma_ref);hist.append(s.__dict__.copy())
    return {"history":hist,"final_state":s.__dict__,"model":"Hardin-Drnevich backbone with Masing unloading/reloading"}

def newmark_beta_sdof(accel_m_s2:list[float],dt_s:float,mass:float,stiffness:float,damping_ratio:float=.05,beta:float=.25,gamma:float=.5)->dict:
    wn=math.sqrt(stiffness/mass);c=2*damping_ratio*mass*wn
    u=v=a=0.0;hist=[]
    a0=1/(beta*dt_s**2);a1=gamma/(beta*dt_s);keff=stiffness+a0*mass+a1*c
    for i,ag in enumerate(accel_m_s2):
        p=-mass*float(ag)
        rhs=p+mass*(a0*u+v/(beta*dt_s)+(1/(2*beta)-1)*a)+c*(a1*u+(gamma/beta-1)*v+dt_s*(gamma/(2*beta)-1)*a)
        un=rhs/keff
        an=a0*(un-u)-v/(beta*dt_s)-(1/(2*beta)-1)*a
        vn=v+dt_s*((1-gamma)*a+gamma*an)
        u,v,a=un,vn,an;hist.append({"time_s":(i+1)*dt_s,"u_m":u,"v_m_s":v,"a_m_s2":a})
    return {"history":hist,"max_abs_displacement_m":max((abs(x["u_m"]) for x in hist),default=0),"method":"Newmark-beta average acceleration"}
