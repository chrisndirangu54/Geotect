from __future__ import annotations

def extrude_stratum(name:str,footprint:list[list[float]],top_elevation_m:float,bottom_elevation_m:float,confidence:float=1.0)->dict:
    """Generate a closed prism solid from a geodetic polygon footprint."""
    if len(footprint)<3: raise ValueError("footprint requires at least 3 vertices")
    n=len(footprint)
    vertices=[[float(lon),float(lat),float(top_elevation_m)] for lon,lat in footprint]+[
        [float(lon),float(lat),float(bottom_elevation_m)] for lon,lat in footprint]
    faces=[]
    # fan triangulation top/bottom
    for i in range(1,n-1):
        faces.append([0,i,i+1]);faces.append([n,n+i+1,n+i])
    for i in range(n):
        j=(i+1)%n
        faces.extend([[i,j,n+j],[i,n+j,n+i]])
    return {"name":name,"vertices":vertices,"triangles":faces,"confidence":max(0,min(float(confidence),1)),
            "state":"interpreted","representation":"closed_triangulated_prism"}
