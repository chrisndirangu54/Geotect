from __future__ import annotations
import numpy as np

def ndvi(red:list[list[float]],nir:list[list[float]])->dict:
    r=np.asarray(red,dtype=float);n=np.asarray(nir,dtype=float)
    if r.shape!=n.shape:raise ValueError("red and nir grids must match")
    out=(n-r)/np.maximum(n+r,1e-9)
    return {"ndvi":out.tolist(),"min":float(np.nanmin(out)),"max":float(np.nanmax(out)),"mean":float(np.nanmean(out))}

def raster_change(before:list[list[float]],after:list[list[float]],threshold:float=0)->dict:
    a=np.asarray(before,dtype=float);b=np.asarray(after,dtype=float)
    if a.shape!=b.shape:raise ValueError("rasters must match")
    d=b-a;mask=np.abs(d)>abs(threshold)
    return {"difference":d.tolist(),"changed_fraction":float(mask.mean()),"mean_change":float(d.mean()),"max_abs_change":float(np.abs(d).max())}

def pointcloud_change(before:list[list[float]],after:list[list[float]],tolerance_m:float=.1)->dict:
    a=np.asarray(before,dtype=float);b=np.asarray(after,dtype=float)
    if a.ndim!=2 or b.ndim!=2 or a.shape[1]!=3 or b.shape[1]!=3:raise ValueError("point clouds must be Nx3")
    # nearest-neighbour baseline without external spatial-index dependency
    sample=a if len(a)<=5000 else a[np.linspace(0,len(a)-1,5000).astype(int)]
    distances=[]
    for p in sample:
        d=np.sqrt(((b-p)**2).sum(axis=1));distances.append(float(d.min()))
    dist=np.asarray(distances)
    return {"sampled_points":len(sample),"mean_nearest_change_m":float(dist.mean()),"p95_change_m":float(np.quantile(dist,.95)),
            "fraction_over_tolerance":float((dist>tolerance_m).mean()),"method":"nearest-neighbour point-cloud change baseline"}
