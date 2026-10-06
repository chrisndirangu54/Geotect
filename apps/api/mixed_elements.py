from __future__ import annotations
import numpy as np

GAUSS_TRI_3=[
    (1/6,1/6,1/6),
    (2/3,1/6,1/6),
    (1/6,2/3,1/6),
]

def p2_shape(r:float,s:float):
    l1=1-r-s;l2=r;l3=s
    N=np.array([l1*(2*l1-1),l2*(2*l2-1),l3*(2*l3-1),4*l1*l2,4*l2*l3,4*l3*l1],float)
    dNdr=np.array([
      -(4*l1-1),4*l2-1,0,
      4*(l1-l2),4*l3,-4*l3
    ],float)
    dNds=np.array([
      -(4*l1-1),0,4*l3-1,
      -4*l2,4*l2,4*(l1-l3)
    ],float)
    return N,dNdr,dNds

def p1_shape(r:float,s:float):
    return np.array([1-r-s,r,s],float),np.array([-1,1,0],float),np.array([-1,0,1],float)

def enrich_triangles_p2(nodes:list[list[float]]|np.ndarray,triangles:list[list[int]]|np.ndarray):
    pts=[list(map(float,p)) for p in np.asarray(nodes,float)]
    edge_mid={};tris6=[]
    for tri in np.asarray(triangles,int):
        mids=[]
        for a,b in [(tri[0],tri[1]),(tri[1],tri[2]),(tri[2],tri[0])]:
            key=tuple(sorted((int(a),int(b))))
            if key not in edge_mid:
                edge_mid[key]=len(pts);pts.append(((np.asarray(pts[a])+np.asarray(pts[b]))/2).tolist())
            mids.append(edge_mid[key])
        tris6.append([int(tri[0]),int(tri[1]),int(tri[2]),*mids])
    return np.asarray(pts,float),np.asarray(tris6,int),dict(edge_mid)

def p2_gradients_physical(xy6:np.ndarray,r:float,s:float):
    N,dNr,dNs=p2_shape(r,s)
    J=np.array([[np.dot(dNr,xy6[:,0]),np.dot(dNr,xy6[:,1])],
                [np.dot(dNs,xy6[:,0]),np.dot(dNs,xy6[:,1])]],float)
    detJ=float(np.linalg.det(J))
    if detJ<=0:raise ValueError("non-positive P2 element Jacobian")
    invJ=np.linalg.inv(J)
    grad=np.vstack([dNr,dNs]).T@invJ
    return N,grad,detJ

def p1_gradients_physical(xy3:np.ndarray):
    x1,y1=xy3[0];x2,y2=xy3[1];x3,y3=xy3[2]
    J=np.array([[x2-x1,y2-y1],[x3-x1,y3-y1]],float)
    detJ=float(np.linalg.det(J))
    if detJ<=0:raise ValueError("non-positive P1 element Jacobian")
    invJ=np.linalg.inv(J)
    grads_ref=np.array([[-1,-1],[1,0],[0,1]],float)
    return grads_ref@invJ,detJ

def b_matrix_p2(grad:np.ndarray):
    B=np.zeros((3,12))
    for i,(dx,dy) in enumerate(grad):
        B[0,2*i]=dx;B[1,2*i+1]=dy;B[2,2*i]=dy;B[2,2*i+1]=dx
    return B

def pressure_stabilization(grad_p:np.ndarray,area:float,tau:float):
    return tau*(grad_p@grad_p.T)*area

def stabilization_tau(element_size_m:float,young_kpa:float,nu:float,scale:float=.05):
    shear=young_kpa/(2*(1+nu))
    return scale*element_size_m**2/max(shear,1e-9)
