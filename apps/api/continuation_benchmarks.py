from __future__ import annotations
import numpy as np
from arc_length import crisfield_arc_length

def snap_through_scalar(k1:float=1.0,k3:float=-1.0,steps:int=30,arc_length:float=.08)->dict:
    """One-DOF nonlinear equilibrium f_int=k1*u+k3*u^3 for continuation verification."""
    def rt(u,lam):
        x=float(u[0]);fint=k1*x+k3*x**3;K=np.array([[k1+3*k3*x*x]],dtype=float);fref=np.array([1.0])
        R=lam*fref-np.array([fint])
        return R,K,fref,{"u":x}
    return crisfield_arc_length(rt,1,steps,arc_length,alpha=1.0,newton_max=30,tol=1e-8)
