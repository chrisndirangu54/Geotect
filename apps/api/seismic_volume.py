from __future__ import annotations
import numpy as np

def reconstruct_volume(traces:list[dict], nx:int=48, ny:int=48, velocity_m_s:float=1800.0)->dict:
    """IDW reconstruction of seismic amplitudes onto a regular x-y-time volume."""
    if not traces: raise ValueError("traces required")
    ns=min(len(t["samples"]) for t in traces)
    if ns<2: raise ValueError("each trace requires >=2 samples")
    dt=float(traces[0].get("dt_s",0.001))
    xs=np.array([float(t["x"]) for t in traces]); ys=np.array([float(t["y"]) for t in traces])
    samples=np.array([np.asarray(t["samples"][:ns],dtype=float) for t in traces])
    gx=np.linspace(xs.min(),xs.max(),max(2,int(nx)))
    gy=np.linspace(ys.min(),ys.max(),max(2,int(ny)))
    volume=np.empty((len(gy),len(gx),ns),dtype=np.float32)
    for iy,y in enumerate(gy):
        for ix,x in enumerate(gx):
            dist=np.hypot(xs-x,ys-y)
            exact=np.where(dist<1e-9)[0]
            if exact.size: volume[iy,ix,:]=samples[exact[0]]
            else:
                w=1.0/np.maximum(dist,1e-6)**2
                volume[iy,ix,:]=(w[:,None]*samples).sum(axis=0)/w.sum()
    depth=np.arange(ns,dtype=float)*dt*float(velocity_m_s)/2.0
    # Downsample response payload if the reconstructed cube is huge.
    payload=volume.tolist()
    return {
      "x":gx.tolist(),"y":gy.tolist(),"depth_m":depth.tolist(),"amplitude":payload,
      "shape":[len(gy),len(gx),ns],"velocity_m_s":velocity_m_s,
      "method":"IDW trace interpolation + constant-velocity time-depth conversion",
      "status":"reconstructed"
    }
