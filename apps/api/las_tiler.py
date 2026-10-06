from __future__ import annotations
import json,math,os
from pathlib import Path
import numpy as np

def tile_las(path:str,out_dir:str,max_points_per_tile:int=50000)->dict:
    """Spatially partition LAS/LAZ point clouds into octree-like NPZ tiles plus manifest."""
    import laspy
    las=laspy.read(path)
    pts=np.column_stack([las.x,las.y,las.z]).astype(np.float32)
    colors=None
    dims=set(las.point_format.dimension_names)
    if {"red","green","blue"}.issubset(dims):
        colors=np.column_stack([las.red,las.green,las.blue]).astype(np.uint16)
    out=Path(out_dir);out.mkdir(parents=True,exist_ok=True)
    n=len(pts);target=max(1000,int(max_points_per_tile))
    if n==0: raise ValueError("empty point cloud")
    tile_count=max(1,math.ceil(n/target))
    side=max(1,math.ceil(tile_count**(1/3)))
    mins=pts.min(axis=0);maxs=pts.max(axis=0);span=np.maximum(maxs-mins,1e-9)
    idx=np.floor((pts-mins)/span*side).astype(int);idx=np.clip(idx,0,side-1)
    keys=idx[:,0]+side*idx[:,1]+side*side*idx[:,2]
    tiles=[]
    for key in np.unique(keys):
        sel=np.where(keys==key)[0]
        for chunk_i,start in enumerate(range(0,len(sel),target)):
            ids=sel[start:start+target]
            name=f"tile_{int(key)}_{chunk_i}.npz"
            payload={"xyz":pts[ids]}
            if colors is not None:payload["rgb"]=colors[ids]
            np.savez_compressed(out/name,**payload)
            p=pts[ids]
            tiles.append({"uri":name,"points":int(len(ids)),"min":p.min(axis=0).tolist(),"max":p.max(axis=0).tolist()})
    manifest={"format":"geotect-point-tiles-v1","source":os.path.basename(path),"point_count":int(n),
              "bounds":{"min":mins.tolist(),"max":maxs.tolist()},"tiles":tiles}
    (out/"tileset.json").write_text(json.dumps(manifest))
    return manifest
