import math
from typing import Any

def geotiff_to_mesh(path:str,max_side:int=128)->dict[str,Any]:
    import rasterio
    import numpy as np
    from rasterio.warp import transform

    with rasterio.open(path) as src:
        band=src.read(1,masked=True)
        rows,cols=band.shape
        stride=max(1,math.ceil(max(rows,cols)/max_side))
        rr=list(range(0,rows,stride));cc=list(range(0,cols,stride))
        if rr[-1]!=rows-1: rr.append(rows-1)
        if cc[-1]!=cols-1: cc.append(cols-1)

        xs=[];ys=[];zs=[]
        for r in rr:
            for c in cc:
                x,y=src.xy(r,c)
                xs.append(x);ys.append(y)
                v=band[r,c]
                zs.append(float(v) if not np.ma.is_masked(v) else 0.0)

        if src.crs and str(src.crs)!="EPSG:4326":
            lons,lats=transform(src.crs,"EPSG:4326",xs,ys)
        else:
            lons,lats=xs,ys

        vertices=[[float(lon),float(lat),float(z)] for lon,lat,z in zip(lons,lats,zs)]
        indices=[]
        width=len(cc)
        for r in range(len(rr)-1):
            for c in range(len(cc)-1):
                a=r*width+c;b=a+1;d=(r+1)*width+c;e=d+1
                indices.extend([a,d,b,b,d,e])

        valid=[z for z in zs if math.isfinite(z)]
        return {
          "source_crs":str(src.crs),"vertex_crs":"EPSG:4326","rows":len(rr),"cols":len(cc),
          "vertices":vertices,"indices":indices,
          "min_elevation_m":min(valid) if valid else None,"max_elevation_m":max(valid) if valid else None,
          "stride":stride,"representation":"triangulated_dem"
        }
