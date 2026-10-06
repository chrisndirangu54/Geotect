from __future__ import annotations
import math,numpy as np
from dataclasses import dataclass

@dataclass
class InterfaceState:
    plastic_slip_m:float=0.0
    normal_gap_m:float=0.0
    sticking:bool=True
    traction_n_kpa:float=0.0
    traction_t_kpa:float=0.0

def coulomb_interface_response(relative_disp_m:list[float],state:InterfaceState,normal_stiffness_kpa_m:float,
                               shear_stiffness_kpa_m:float,friction_deg:float,cohesion_kpa:float=0,
                               dilation_deg:float=0,tension_cutoff_kpa:float=0)->tuple[InterfaceState,np.ndarray,dict]:
    """Two-DOF local interface law: [normal opening, tangential slip].

    Compression traction is positive. Opening beyond tensile cutoff releases contact.
    Coulomb return mapping limits tangential traction to c + sigma_n tan(phi).
    """
    dn,dt=map(float,relative_disp_m);phi=math.radians(friction_deg);psi=math.radians(dilation_deg)
    ns=InterfaceState(**state.__dict__)
    # dn > 0 is opening, dn < 0 compression.
    tn=max(-normal_stiffness_kpa_m*dn,0.0)
    if dn>0 and tension_cutoff_kpa<=0:
        tn=0.0
    tt_trial=shear_stiffness_kpa_m*(dt-state.plastic_slip_m)
    strength=max(cohesion_kpa+tn*math.tan(phi),0.0)
    if abs(tt_trial)<=strength+1e-12:
        tt=tt_trial;Kt=np.diag([normal_stiffness_kpa_m if tn>0 else 0.0,shear_stiffness_kpa_m]);stick=True;dl=0.0
    else:
        sign=1.0 if tt_trial>=0 else -1.0;tt=sign*strength
        dl=(abs(tt_trial)-strength)/max(shear_stiffness_kpa_m,1e-12)
        ns.plastic_slip_m=state.plastic_slip_m+sign*dl
        # dilation converts plastic slip into closure/opening contribution.
        ns.normal_gap_m=dn+dl*math.tan(psi)
        kn=normal_stiffness_kpa_m if tn>0 else 0.0
        Kt=np.array([[kn,0.0],[sign*kn*math.tan(phi),0.0]])
        stick=False
    ns.sticking=stick;ns.traction_n_kpa=tn;ns.traction_t_kpa=tt
    return ns,Kt,{"normal_traction_kpa":tn,"shear_traction_kpa":tt,"strength_kpa":strength,"plastic_multiplier_m":dl,"sticking":stick}

def interface_global_force_tangent(node_a:list[float],node_b:list[float],u_a:list[float],u_b:list[float],state:InterfaceState,
                                   normal_stiffness_kpa_m:float,shear_stiffness_kpa_m:float,friction_deg:float,
                                   cohesion_kpa:float=0,dilation_deg:float=0):
    a=np.asarray(node_a,dtype=float);b=np.asarray(node_b,dtype=float);d=b-a;L=float(np.linalg.norm(d))
    if L<=0:raise ValueError("interface nodes must be distinct")
    t=d/L;n=np.array([-t[1],t[0]]);R=np.vstack([n,t])
    rel=R@(np.asarray(u_b)-np.asarray(u_a))
    ns,Kloc,info=coulomb_interface_response(rel.tolist(),state,normal_stiffness_kpa_m,shear_stiffness_kpa_m,friction_deg,cohesion_kpa,dilation_deg)
    traction=np.array([ns.traction_n_kpa,ns.traction_t_kpa]);fg=R.T@traction*L
    # Force vector [a_x,a_y,b_x,b_y].
    f=np.r_[-fg,fg]
    T=np.block([[-R,R]])
    K=T.T@Kloc@T*L
    return ns,f,K,info
