from __future__ import annotations
import os,numpy as np
from dataclasses import dataclass

@dataclass
class LinearSolveInfo:
    backend:str
    method:str
    converged:bool
    iterations:int|None
    residual_norm:float

def solve_sparse(A,b,method:str="auto",tol:float=1e-9,maxiter:int=2000,backend:str="auto"):
    """Sparse linear solver with SciPy CPU default and optional CuPy GPU path."""
    if backend in {"auto","gpu"}:
        try:
            import cupy as cp
            import cupyx.scipy.sparse as csp
            import cupyx.scipy.sparse.linalg as csla
            if backend=="gpu" or (backend=="auto" and os.getenv("GEOTECT_GPU","0")=="1"):
                Ac=csp.csr_matrix(A);bc=cp.asarray(b)
                x,info=csla.cg(Ac,bc,tol=tol,maxiter=maxiter)
                xr=cp.asnumpy(x);res=float(np.linalg.norm(A@xr-b))
                return xr,LinearSolveInfo("cupy","cg",info==0,None,res)
        except Exception:
            if backend=="gpu":raise
    import scipy.sparse as sp
    import scipy.sparse.linalg as spla
    As=sp.csr_matrix(A)
    if method=="auto":
        method="spsolve" if As.shape[0]<5000 else "gmres"
    if method=="spsolve":
        x=spla.spsolve(As,b);res=float(np.linalg.norm(As@x-b))
        return np.asarray(x),LinearSolveInfo("scipy","spsolve",True,None,res)
    it=[0]
    def cb(_):it[0]+=1
    if method=="cg":
        x,info=spla.cg(As,b,rtol=tol,atol=0,maxiter=maxiter,callback=cb)
    elif method=="bicgstab":
        x,info=spla.bicgstab(As,b,rtol=tol,atol=0,maxiter=maxiter,callback=cb)
    else:
        x,info=spla.gmres(As,b,rtol=tol,atol=0,restart=min(100,maxiter),maxiter=maxiter,callback=cb,callback_type="legacy")
    res=float(np.linalg.norm(As@x-b))
    return np.asarray(x),LinearSolveInfo("scipy",method,info==0,it[0],res)

def coo_from_triplets(rows,cols,data,shape):
    import scipy.sparse as sp
    return sp.coo_matrix((data,(rows,cols)),shape=shape).tocsr()
