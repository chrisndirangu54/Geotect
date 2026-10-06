from __future__ import annotations
import numpy as np

def deformation_gradient(grad_u:np.ndarray)->np.ndarray:
    return np.eye(2)+np.asarray(grad_u,float)

def green_lagrange(F:np.ndarray)->np.ndarray:
    C=F.T@F
    return .5*(C-np.eye(2))

def almansi_strain(F:np.ndarray)->np.ndarray:
    b=F@F.T
    return .5*(np.eye(2)-np.linalg.inv(b))

def jacobian(F:np.ndarray)->float:
    return float(np.linalg.det(F))

def push_forward_cauchy(F:np.ndarray,second_piola:np.ndarray)->np.ndarray:
    J=max(jacobian(F),1e-12)
    return (F@second_piola@F.T)/J

def geometric_stiffness_scalar(gradN:np.ndarray,cauchy:np.ndarray,weight:float)->np.ndarray:
    n=len(gradN);Kg=np.zeros((2*n,2*n))
    for a in range(n):
        for b in range(n):
            g=float(gradN[a]@cauchy@gradN[b])*weight
            Kg[2*a,2*b]+=g;Kg[2*a+1,2*b+1]+=g
    return Kg

def updated_coordinates(nodes:np.ndarray,displacement:np.ndarray)->np.ndarray:
    x=np.asarray(nodes,float);u=np.asarray(displacement,float)
    if x.shape!=u.shape:raise ValueError("nodes and displacement shapes must match")
    return x+u
