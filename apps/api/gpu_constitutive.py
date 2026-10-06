from __future__ import annotations
import numpy as np

def cuda_mohr_coulomb_batch(stress,deps,E_kpa:float,nu:float,cohesion_kpa:float,friction_deg:float):
    """Vectorized CUDA elastic-predictor / MC projection for batched integration."""
    try:
        import cupy as cp
    except Exception as exc:raise RuntimeError("CuPy is required for GPU constitutive integration") from exc
    s=cp.asarray(stress,dtype=cp.float64);de=cp.asarray(deps,dtype=cp.float64)
    if s.ndim!=2 or s.shape[1]!=3 or de.shape!=s.shape:raise ValueError("stress/deps must be [n,3]")
    lam=E_kpa*nu/((1+nu)*(1-2*nu));mu=E_kpa/(2*(1+nu))
    D=cp.asarray([[lam+2*mu,lam,0],[lam,lam+2*mu,0],[0,0,mu]],dtype=cp.float64)
    trial=s+de@D.T
    sx,sy,t=trial[:,0],trial[:,1],trial[:,2]
    mean=.5*(sx+sy);rad=cp.sqrt((.5*(sx-sy))**2+t*t)
    smax=mean+rad;smin=mean-rad;p=.5*(-smin-smax);q=(-smin)-(-smax)
    phi=np.deg2rad(friction_deg);M=2*np.sin(phi);k=2*cohesion_kpa*np.cos(phi)
    f=q-M*p-k;yielded=f>0
    qnew=cp.where(yielded,M*p+k,q);ratio=cp.where(q>1e-12,qnew/q,1.0)
    devx=sx-mean;devy=sy-mean
    out=trial.copy();out[:,0]=mean+ratio*devx;out[:,1]=mean+ratio*devy;out[:,2]=ratio*t
    return cp.asnumpy(out),cp.asnumpy(yielded),cp.asnumpy(f)

def cuda_hex_linear_stiffness_stub(element_count:int)->dict:
    """Execution marker for future full HEX8 CUDA kernel; allocates device-side work arrays."""
    try:
        import cupy as cp
    except Exception as exc:raise RuntimeError("CuPy is required") from exc
    buf=cp.zeros((int(element_count),24,24),dtype=cp.float64)
    return {"elements":int(element_count),"device_bytes":int(buf.nbytes),"kernel":"HEX8 stiffness workspace allocated"}
