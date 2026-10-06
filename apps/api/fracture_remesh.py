from __future__ import annotations
import numpy as np

def detect_fracture_candidates(nodes,triangles,damage,threshold=.8):
    tri=np.asarray(triangles,int);d=np.asarray(damage,float)
    return [int(i) for i,x in enumerate(d) if x>=threshold and i<len(tri)]

def split_triangles_along_damage(nodes,triangles,marked):
    pts=[list(map(float,p)) for p in nodes];out=[];marked=set(marked);mapinfo=[]
    for i,t in enumerate(triangles):
        a,b,c=map(int,t)
        if i not in marked:out.append([a,b,c]);continue
        edges=[(a,b),(b,c),(c,a)]
        lens=[np.linalg.norm(np.asarray(pts[x])-np.asarray(pts[y])) for x,y in edges]
        x,y=edges[int(np.argmax(lens))];mid=((np.asarray(pts[x])+np.asarray(pts[y]))/2).tolist();m=len(pts);pts.append(mid)
        z=next(n for n in (a,b,c) if n not in (x,y));out.extend([[x,m,z],[m,y,z]]);mapinfo.append({"parent":i,"new_node":m,"edge":[x,y]})
    return {"nodes":pts,"triangles":out,"splits":mapinfo}

def remesh_contact_surfaces(nodes,triangles,damage,threshold=.8):
    marked=detect_fracture_candidates(nodes,triangles,damage,threshold)
    mesh=split_triangles_along_damage(nodes,triangles,marked)
    contacts=[{"parent_element":x["parent"],"fracture_edge":x["edge"],"new_node":x["new_node"]} for x in mesh["splits"]]
    return {**mesh,"contact_interfaces":contacts,"marked_elements":marked}
