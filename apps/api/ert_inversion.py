from __future__ import annotations
import numpy as np

def _smoothness_matrix(n:int)->np.ndarray:
    if n<2: return np.eye(n)
    L=np.zeros((n-1,n),dtype=float)
    for i in range(n-1):
        L[i,i]=-1.0;L[i,i+1]=1.0
    return L

def invert_ert(sensitivity:list[list[float]], apparent_resistivity:list[float], regularization:float=1.0,
               reference_resistivity:float=100.0, iterations:int=6)->dict:
    """Regularized log-resistivity inversion using a supplied sensitivity/Jacobian matrix.

    This is an executable deterministic inversion core. Survey-specific forward modelling
    may provide the sensitivity matrix from pyGIMLi/SimPEG/vendor software.
    """
    G=np.asarray(sensitivity,dtype=float)
    rho=np.asarray(apparent_resistivity,dtype=float)
    if G.ndim!=2 or rho.ndim!=1 or G.shape[0]!=rho.size:
        raise ValueError("sensitivity must be [measurements,cells] and match apparent_resistivity")
    if np.any(rho<=0): raise ValueError("apparent resistivity must be positive")
    n=G.shape[1]
    L=_smoothness_matrix(n)
    m=np.full(n,np.log(float(reference_resistivity)))
    d=np.log(rho)
    history=[]
    lam=max(float(regularization),1e-9)
    for k in range(max(1,int(iterations))):
        pred=G@m
        residual=d-pred
        A=G.T@G + lam*(L.T@L) + np.eye(n)*1e-8
        b=G.T@residual - lam*(L.T@L)@m
        dm=np.linalg.solve(A,b)
        m=m+dm
        rms=float(np.sqrt(np.mean(residual**2)))
        history.append({"iteration":k+1,"log_rms":rms,"update_norm":float(np.linalg.norm(dm))})
        if np.linalg.norm(dm)<1e-6: break
    modeled=G@m
    return {
      "cell_resistivity_ohm_m":np.exp(m).tolist(),
      "modeled_log_data":modeled.tolist(),
      "observed_log_data":d.tolist(),
      "history":history,
      "regularization":lam,
      "method":"Tikhonov-regularized log-resistivity inversion",
      "status":"inverted",
      "note":"Survey geometry/forward sensitivity must be physically validated."
    }
