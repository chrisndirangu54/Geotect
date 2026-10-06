from __future__ import annotations
import numpy as np

def nonlocal_average(centroids,values,length_scale_m:float):
    x=np.asarray(centroids,float);v=np.asarray(values,float);out=np.zeros_like(v,dtype=float)
    for i,p in enumerate(x):
        d=np.linalg.norm(x-p,axis=1);w=np.exp(-(d/max(length_scale_m,1e-9))**2);out[i]=float(np.dot(w,v)/max(w.sum(),1e-12))
    return out

def regularized_strength(base_cohesion_kpa:float,base_friction_deg:float,local_eqp,centroids,length_scale_m:float,
                         softening_rate:float=.5,min_fraction:float=.2):
    nl=nonlocal_average(centroids,local_eqp,length_scale_m);factor=np.maximum(min_fraction,np.exp(-softening_rate*nl))
    return {"nonlocal_eqp":nl.tolist(),"cohesion_kpa":(base_cohesion_kpa*factor).tolist(),
      "friction_deg":(base_friction_deg*factor).tolist(),"length_scale_m":length_scale_m}
