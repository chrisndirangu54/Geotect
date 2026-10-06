from __future__ import annotations
import numpy as np

def solve_steady_groundwater(nx:int,ny:int,dx_m:float,dy_m:float,k:list[list[float]]|float,
                             left_head_m:float,right_head_m:float,top_no_flow:bool=True,bottom_no_flow:bool=True,
                             tolerance:float=1e-5,max_iterations:int=20000)->dict:
    """Finite-difference solution of div(K grad h)=0 with fixed left/right heads."""
    nx=max(3,int(nx));ny=max(3,int(ny));dx=float(dx_m);dy=float(dy_m)
    K=np.full((ny,nx),float(k)) if isinstance(k,(int,float)) else np.asarray(k,dtype=float)
    if K.shape!=(ny,nx): raise ValueError("k grid shape must be [ny,nx]")
    if np.any(K<=0): raise ValueError("hydraulic conductivity must be positive")
    h=np.tile(np.linspace(float(left_head_m),float(right_head_m),nx),(ny,1))
    converged=False
    for it in range(int(max_iterations)):
        old=h.copy()
        for j in range(1,ny-1):
            for i in range(1,nx-1):
                ke=(K[j,i]+K[j,i+1])/2;kw=(K[j,i]+K[j,i-1])/2
                kn=(K[j,i]+K[j-1,i])/2;ks=(K[j,i]+K[j+1,i])/2
                ae=ke/dx**2;aw=kw/dx**2;an=kn/dy**2;ass=ks/dy**2
                h[j,i]=(ae*h[j,i+1]+aw*h[j,i-1]+an*h[j-1,i]+ass*h[j+1,i])/(ae+aw+an+ass)
        h[:,0]=left_head_m;h[:,-1]=right_head_m
        if top_no_flow:h[0,:]=h[1,:]
        if bottom_no_flow:h[-1,:]=h[-2,:]
        err=float(np.max(np.abs(h-old)))
        if err<tolerance:
            converged=True;break
    qx=np.zeros_like(h);qy=np.zeros_like(h)
    qx[:,1:-1]=-K[:,1:-1]*(h[:,2:]-h[:,:-2])/(2*dx)
    qy[1:-1,:]=-K[1:-1,:]*(h[2:,:]-h[:-2,:])/(2*dy)
    return {"head_m":h.tolist(),"qx_m_s":qx.tolist(),"qy_m_s":qy.tolist(),
            "iterations":it+1,"converged":converged,"residual_max_m":err,
            "method":"finite-difference steady heterogeneous groundwater PDE"}
