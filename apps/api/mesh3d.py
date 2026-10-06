from __future__ import annotations
import numpy as np

def structured_hex_mesh(lx:float,ly:float,lz:float,nx:int,ny:int,nz:int):
    xs=np.linspace(0,lx,nx);ys=np.linspace(0,ly,ny);zs=np.linspace(0,lz,nz)
    nodes=np.array([[x,y,z] for z in zs for y in ys for x in xs],float)
    hexes=[]
    def idx(i,j,k):return k*ny*nx+j*nx+i
    for k in range(nz-1):
        for j in range(ny-1):
            for i in range(nx-1):
                n000=idx(i,j,k);n100=idx(i+1,j,k);n110=idx(i+1,j+1,k);n010=idx(i,j+1,k)
                n001=idx(i,j,k+1);n101=idx(i+1,j,k+1);n111=idx(i+1,j+1,k+1);n011=idx(i,j+1,k+1)
                hexes.append([n000,n100,n110,n010,n001,n101,n111,n011])
    return nodes,np.asarray(hexes,int)

def hex_to_tets(hexes):
    t=[]
    for h in np.asarray(hexes,int):
        a,b,c,d,e,f,g,hh=h
        t += [[a,b,d,e],[b,c,d,g],[b,d,e,g],[b,e,f,g],[d,e,g,hh]]
    return np.asarray(t,int)

def tet_B(xy:np.ndarray):
    X=np.c_[np.ones(4),xy]
    det=float(np.linalg.det(X));V=abs(det)/6
    if V<=0:raise ValueError("degenerate tetrahedron")
    inv=np.linalg.inv(X)
    grads=inv[1:,:].T
    B=np.zeros((6,12))
    for i,(dx,dy,dz) in enumerate(grads):
        B[:,3*i:3*i+3]=[[dx,0,0],[0,dy,0],[0,0,dz],[dy,dx,0],[0,dz,dy],[dz,0,dx]]
    return B,V,grads

def elastic_D3(E_kpa:float,nu:float):
    lam=E_kpa*nu/((1+nu)*(1-2*nu));mu=E_kpa/(2*(1+nu))
    D=np.array([
      [lam+2*mu,lam,lam,0,0,0],[lam,lam+2*mu,lam,0,0,0],[lam,lam,lam+2*mu,0,0,0],
      [0,0,0,mu,0,0],[0,0,0,0,mu,0],[0,0,0,0,0,mu]],float)
    return D
