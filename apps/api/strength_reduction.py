from __future__ import annotations
import math
from elastoplastic_fem import solve_elastoplastic_2d

def reduce_strength(material:dict,factor:float)->dict:
    if factor<=0:raise ValueError("strength reduction factor must be positive")
    m=dict(material)
    c=float(m.get("cohesion_kpa",0))/factor
    phi=math.radians(float(m.get("friction_deg",0)))
    psi=math.radians(float(m.get("dilation_deg",0)))
    m["cohesion_kpa"]=c
    m["friction_deg"]=math.degrees(math.atan(math.tan(phi)/factor))
    m["dilation_deg"]=math.degrees(math.atan(math.tan(psi)/factor)) if abs(psi)>0 else 0.0
    return m

def strength_reduction_search(base:dict,min_factor:float=1.0,max_factor:float=5.0,tolerance:float=.02,max_iter:int=12,
                              displacement_limit_m:float|None=None)->dict:
    def stable(f):
        p=dict(base);p["material"]=reduce_strength(base["material"],f)
        out=solve_elastoplastic_2d(**p)
        conv=out["status"]=="solved"
        disp=float(out["max_displacement_m"])
        if displacement_limit_m is not None:conv=conv and disp<=displacement_limit_m
        return conv,out
    lo=min_factor;hi=max_factor;lo_ok,lo_out=stable(lo);hi_ok,hi_out=stable(hi)
    if not lo_ok:return {"factor_of_safety":lo,"bracket":[lo,lo],"status":"unstable_at_minimum","last_result":lo_out}
    if hi_ok:return {"factor_of_safety":hi,"bracket":[hi,hi],"status":"stable_above_maximum","last_result":hi_out}
    history=[]
    for _ in range(max_iter):
        mid=.5*(lo+hi);ok,out=stable(mid);history.append({"factor":mid,"stable":ok,"max_displacement_m":out["max_displacement_m"]})
        if ok:lo=mid;lo_out=out
        else:hi=mid;hi_out=out
        if hi-lo<=tolerance:break
    return {"factor_of_safety":lo,"bracket":[lo,hi],"history":history,"status":"bracketed","stable_result":lo_out,"unstable_result":hi_out,
      "method":"phi-c strength reduction with nonlinear equilibrium criterion"}
