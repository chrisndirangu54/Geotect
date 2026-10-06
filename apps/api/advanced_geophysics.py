from __future__ import annotations
import numpy as np

def linear_potential_inversion(kernel:list[list[float]],observations:list[float],regularization:float=.1)->dict:
    G=np.asarray(kernel,dtype=float);d=np.asarray(observations,dtype=float)
    if G.ndim!=2 or len(d)!=G.shape[0]:raise ValueError("kernel/data dimensions mismatch")
    A=G.T@G+np.eye(G.shape[1])*max(regularization,1e-9)
    m=np.linalg.solve(A,G.T@d);pred=G@m;res=d-pred
    return {"model":m.tolist(),"predicted":pred.tolist(),"rms":float(np.sqrt(np.mean(res**2))),
            "method":"L2-regularized linear potential-field inversion","applies_to":["gravity","magnetics"]}

def masw_dispersion(freq_hz:list[float],phase_velocity_m_s:list[float])->dict:
    f=np.asarray(freq_hz,dtype=float);v=np.asarray(phase_velocity_m_s,dtype=float)
    if f.shape!=v.shape or len(f)<2:raise ValueError("matching frequency and phase-velocity vectors required")
    order=np.argsort(f);f=f[order];v=v[order]
    wavelengths=v/np.maximum(f,1e-9)
    # common engineering depth sensitivity proxy ~ lambda/2
    depth=.5*wavelengths
    return {"frequency_hz":f.tolist(),"phase_velocity_m_s":v.tolist(),"sensitivity_depth_m":depth.tolist(),
            "vs_proxy_m_s":(v/.92).tolist(),"method":"MASW dispersion interpretation baseline; inversion calibration required"}
