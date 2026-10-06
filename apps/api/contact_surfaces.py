from __future__ import annotations
import math,numpy as np
from dataclasses import dataclass

@dataclass
class SurfaceContactState:
    tangential_slip_1:float=0.0
    tangential_slip_2:float=0.0
    sticking:bool=True

def closest_point_triangle(p,a,b,c):
    p=np.asarray(p,float);a=np.asarray(a,float);b=np.asarray(b,float);c=np.asarray(c,float)
    ab=b-a;ac=c-a;ap=p-a
    d1=ab@ap;d2=ac@ap
    if d1<=0 and d2<=0:return a
    bp=p-b;d3=ab@bp;d4=ac@bp
    if d3>=0 and d4<=d3:return b
    vc=d1*d4-d3*d2
    if vc<=0 and d1>=0 and d3<=0:
        v=d1/(d1-d3);return a+v*ab
    cp=p-c;d5=ab@cp;d6=ac@cp
    if d6>=0 and d5<=d6:return c
    vb=d5*d2-d1*d6
    if vb<=0 and d2>=0 and d6<=0:
        w=d2/(d2-d6);return a+w*ac
    va=d3*d6-d5*d4
    if va<=0 and d4-d3>=0 and d5-d6>=0:
        w=(d4-d3)/((d4-d3)+(d5-d6));return b+w*(c-b)
    denom=1/(va+vb+vc);v=vb*denom;w=vc*denom
    return a+ab*v+ac*w

def coulomb_surface_contact(point,displacement,triangle,state:SurfaceContactState,normal_stiffness_kpa_m:float,
                            shear_stiffness_kpa_m:float,friction_deg:float,cohesion_kpa:float=0)->dict:
    tri=np.asarray(triangle,float);x=np.asarray(point,float)+np.asarray(displacement,float)
    q=closest_point_triangle(x,*tri);e1=tri[1]-tri[0];e1=e1/max(np.linalg.norm(e1),1e-12)
    n=np.cross(tri[1]-tri[0],tri[2]-tri[0]);n=n/max(np.linalg.norm(n),1e-12);e2=np.cross(n,e1)
    rel=x-q;gap=float(rel@n);t1=float(rel@e1);t2=float(rel@e2)
    tn=max(-normal_stiffness_kpa_m*gap,0.0);trial=np.array([t1-state.tangential_slip_1,t2-state.tangential_slip_2])*shear_stiffness_kpa_m
    strength=max(cohesion_kpa+tn*math.tan(math.radians(friction_deg)),0.0);mag=float(np.linalg.norm(trial))
    ns=SurfaceContactState(**state.__dict__)
    if mag<=strength+1e-12:
        tt=trial;ns.sticking=True
    else:
        direction=trial/max(mag,1e-12);tt=direction*strength;dslip=(mag-strength)/max(shear_stiffness_kpa_m,1e-12)
        ns.tangential_slip_1+=float(direction[0]*dslip);ns.tangential_slip_2+=float(direction[1]*dslip);ns.sticking=False
    force=tn*n+tt[0]*e1+tt[1]*e2
    return {"state":ns.__dict__,"gap_m":gap,"normal_traction_kpa":tn,"tangential_traction_kpa":tt.tolist(),"force_directional_kpa":force.tolist(),"closest_point":q.tolist()}
