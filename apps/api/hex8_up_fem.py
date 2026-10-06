from __future__ import annotations
import numpy as np,math
from mesh3d import structured_hex_mesh
from up3d_fem import make_material3d
from materials3d import LiquefactionSandStyle
from solver_backend import coo_from_triplets,solve_sparse

GP=[-1/math.sqrt(3),1/math.sqrt(3)]

def hex8_shape(xi,eta,zeta):
    signs=np.array([[-1,-1,-1],[1,-1,-1],[1,1,-1],[-1,1,-1],[-1,-1,1],[1,-1,1],[1,1,1],[-1,1,1]],float)
    N=np.prod((1+signs*np.array([xi,eta,zeta]))/2,axis=1)
    d=np.zeros((8,3))
    for i,(a,b,c) in enumerate(signs):
        d[i,0]=a*(1+b*eta)*(1+c*zeta)/8
        d[i,1]=b*(1+a*xi)*(1+c*zeta)/8
        d[i,2]=c*(1+a*xi)*(1+b*eta)/8
    return N,d

def hex8_B(xy,xi,eta,zeta):
    N,dref=hex8_shape(xi,eta,zeta);J=dref.T@xy;det=float(np.linalg.det(J))
    if det<=0:raise ValueError("non-positive HEX8 Jacobian")
    grad=dref@np.linalg.inv(J);B=np.zeros((6,24))
    for i,(dx,dy,dz) in enumerate(grad):
        B[:,3*i:3*i+3]=[[dx,0,0],[0,dy,0],[0,0,dz],[dy,dx,0],[0,dz,dy],[dz,0,dx]]
    return N,grad,B,det

def solve_up3d_hex(lx:float,ly:float,lz:float,nx:int,ny:int,nz:int,material:dict,
                   permeability_m_s:float=1e-6,storage_1_kpa:float=1e-6,biot_alpha:float=1.0,dt_s:float=60,steps:int=1,
                   top_pressure_kpa:float=0,density_kg_m3:float=0,drained_top_kpa:float|None=0.0,
                   newton_max:int=20,tolerance:float=1e-6,linear_method:str="auto",backend:str="auto")->dict:
    nodes,hexes=structured_hex_mesh(lx,ly,lz,max(2,nx),max(2,ny),max(2,nz));nn=len(nodes);nd=4*nn
    model=make_material3d(material);states=[[model.initial() for _ in range(8)] for _ in hexes];xprev=np.zeros(nd)
    top=np.where(np.isclose(nodes[:,2],lz))[0];bottom=np.where(np.isclose(nodes[:,2],0))[0];fixed=[4*i+2 for i in bottom]+[4*int(bottom[0]),4*int(bottom[0])+1];history=[]
    for step in range(1,max(1,steps)+1):
        old=xprev.copy();x=old.copy();committed=[[s.copy() for s in el] for el in states];lf=step/max(1,steps);conv=False
        for it in range(newton_max):
            rows=[];cols=[];data=[];R=np.zeros(nd);trial=[[s.copy() for s in el] for el in committed]
            for e,conn in enumerate(hexes):
                xy=nodes[conn];udofs=np.array([[4*n,4*n+1,4*n+2] for n in conn]).ravel();pdofs=np.array([4*n+3 for n in conn]);ue=x[udofs];ue0=old[udofs];pe=x[pdofs];pe0=old[pdofs]
                Kuu=np.zeros((24,24));Kup=np.zeros((24,8));Kpu=np.zeros((8,24));Kpp=np.zeros((8,8));ru=np.zeros(24);rp=np.zeros(8);gpidx=0
                for xi in GP:
                    for eta in GP:
                        for zeta in GP:
                            N,grad,B,det=hex8_B(xy,xi,eta,zeta);deps=B@(ue-ue0);pmean=float(N@pe)
                            if isinstance(model,LiquefactionSandStyle):st,C,meta=model.integrate(committed[e][gpidx],deps,max(1.0,-pmean+100))
                            else:st,C,meta=model.integrate(committed[e][gpidx],deps)
                            trial[e][gpidx]=st;gpidx+=1
                            sigma=st.stress.copy();sigma[:3]-=biot_alpha*pmean
                            bvol=np.zeros(24)
                            for a in range(8):bvol[3*a]=B[0,3*a];bvol[3*a+1]=B[1,3*a+1];bvol[3*a+2]=B[2,3*a+2]
                            Kuu+=B.T@C@B*det;Kup+=-biot_alpha*np.outer(bvol,N)*det;Kpu+=biot_alpha*np.outer(N,bvol)*det/dt_s
                            Kpp+=storage_1_kpa*np.outer(N,N)*det/dt_s+(permeability_m_s/9.81)*(grad@grad.T)*det
                            ru+=B.T@sigma*det;rp+=storage_1_kpa*np.outer(N,N)@(pe-pe0)*det/dt_s+biot_alpha*np.outer(N,bvol)@(ue-ue0)*det/dt_s+(permeability_m_s/9.81)*(grad@grad.T)@pe*det
                            body=-density_kg_m3*9.81/1000
                            for a in range(8):ru[3*a+2]-=lf*body*N[a]*det
                for a,I in enumerate(udofs):
                    R[I]+=ru[a]
                    for b,J in enumerate(udofs):rows.append(I);cols.append(J);data.append(Kuu[a,b])
                    for b,J in enumerate(pdofs):rows.append(I);cols.append(J);data.append(Kup[a,b])
                for a,I in enumerate(pdofs):
                    R[I]+=rp[a]
                    for b,J in enumerate(udofs):rows.append(I);cols.append(J);data.append(Kpu[a,b])
                    for b,J in enumerate(pdofs):rows.append(I);cols.append(J);data.append(Kpp[a,b])
            if top_pressure_kpa:
                area=lx*ly/max(len(top),1);q=-lf*top_pressure_kpa
                for n in top:R[4*n+2]-=q*area
            K=coo_from_triplets(rows,cols,data,(nd,nd)).tolil();fixed_now=list(fixed)
            if drained_top_kpa is not None:
                for n in top:
                    d=4*n+3;R[d]=x[d]-drained_top_kpa;K.rows[d]=[d];K.data[d]=[1.0];fixed_now.append(d)
            K=K.tocsr();free=np.setdiff1d(np.arange(nd),np.array(fixed_now,int));nr=float(np.linalg.norm(R[free]))
            if nr<tolerance*max(1.0,float(np.linalg.norm(x[free]))):conv=True;states=trial;xprev=x;break
            dx,info=solve_sparse(K[np.ix_(free,free)],-R[free],method=linear_method,backend=backend,tol=min(1e-8,tolerance*.1));x[free]+=dx
        if not conv:states=trial;xprev=x
        U=np.array([[xprev[4*i],xprev[4*i+1],xprev[4*i+2]] for i in range(nn)]);P=np.array([xprev[4*i+3] for i in range(nn)])
        history.append({"step":step,"converged":conv,"iterations":it+1,"residual":nr,"max_displacement_m":float(np.linalg.norm(U,axis=1).max()),"p_min_kpa":float(P.min()),"p_max_kpa":float(P.max())})
    U=np.array([[xprev[4*i],xprev[4*i+1],xprev[4*i+2]] for i in range(nn)]);P=np.array([xprev[4*i+3] for i in range(nn)])
    return {"nodes_m":nodes.tolist(),"hexahedra":hexes.tolist(),"displacement_m":U.tolist(),"pore_pressure_kpa":P.tolist(),"history":history,
      "status":"solved" if all(h["converged"] for h in history) else "nonlinear_iteration_warning","material_model":material.get("model","anisotropic_critical_state"),
      "method":"3D HEX8 monolithic u-p FEM research solver with 2x2x2 integration"}
