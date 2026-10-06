from __future__ import annotations
import numpy as np

def calibrate_scalar(observed:list[float],simulated:list[float],parameter_value:float,elasticity:float=1.0,bounds:list[float]|None=None)->dict:
    o=np.asarray(observed,dtype=float);s=np.asarray(simulated,dtype=float)
    if o.shape!=s.shape or not len(o):raise ValueError("observed and simulated must match")
    denom=float(np.dot(s,s))
    factor=float(np.dot(o,s)/denom) if denom>0 else 1.0
    updated=parameter_value*(max(factor,1e-6)**(1/max(elasticity,1e-9)))
    if bounds:updated=max(bounds[0],min(bounds[1],updated))
    before=float(np.sqrt(np.mean((o-s)**2)));after=float(np.sqrt(np.mean((o-s*factor)**2)))
    return {"parameter_before":parameter_value,"parameter_after":updated,"scale_factor":factor,"rmse_before":before,"rmse_after_proxy":after,
      "method":"least-squares scalar response calibration"}
