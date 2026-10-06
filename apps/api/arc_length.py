from __future__ import annotations
import math,numpy as np
from solver_backend import solve_sparse

def crisfield_arc_length(residual_tangent,ndof:int,steps:int=20,arc_length:float=.05,alpha:float=1.0,
                         newton_max:int=30,tol:float=1e-6,linear_method:str="auto",backend:str="auto")->dict:
    """Crisfield-style spherical arc-length continuation.

    residual_tangent(u,lambda) -> (R,K,f_ref,metadata)
    with equilibrium R = lambda*f_ref - fint.
    """
    u=np.zeros(ndof);lam=0.0;du_prev=None;dl_prev=1.0;history=[];path=[]
    for step in range(steps):
        R,K,fref,meta=residual_tangent(u,lam)
        du_t,linfo=solve_sparse(K,fref,linear_method,backend=backend)
        denom=math.sqrt(float(du_t@du_t)+alpha*alpha)
        dl=arc_length/max(denom,1e-12)
        if du_prev is not None and float(du_t@du_prev)+alpha*alpha*dl_prev<0:dl=-dl
        u_trial=u+dl*du_t;lam_trial=lam+dl
        du_total=u_trial-u;dl_total=lam_trial-lam
        converged=False
        for it in range(newton_max):
            R,K,fref,meta=residual_tangent(u_trial,lam_trial)
            nr=float(np.linalg.norm(R))
            g=float(du_total@du_total+(alpha*dl_total)**2-arc_length**2)
            if nr<tol and abs(g)<tol:
                converged=True;break
            du_r,_=solve_sparse(K,R,linear_method,backend=backend)
            du_f,_=solve_sparse(K,fref,linear_method,backend=backend)
            a=2*float(du_total@du_f)+2*alpha*alpha*dl_total
            b=-g-2*float(du_total@du_r)
            ddl=b/max(a,1e-14)
            corr=du_r+ddl*du_f
            u_trial+=corr;lam_trial+=ddl;du_total=u_trial-u;dl_total=lam_trial-lam
        u=u_trial;lam=lam_trial;du_prev=du_total.copy();dl_prev=dl_total
        history.append({"step":step+1,"load_factor":lam,"iterations":it+1,"converged":converged,"residual":nr,"constraint":g})
        path.append({"load_factor":lam,"displacement_norm":float(np.linalg.norm(u)),**(meta or {})})
        if not converged:break
    return {"displacement":u.tolist(),"load_factor":lam,"history":history,"path":path,
      "method":"Crisfield spherical arc-length continuation","status":"solved" if all(x["converged"] for x in history) else "continuation_warning"}
