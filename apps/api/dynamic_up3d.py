from __future__ import annotations
import math,numpy as np
from mesh3d import structured_hex_mesh
from hex8_up_fem import hex8_B,GP
from up3d_fem import make_material3d
from materials3d import LiquefactionSandStyle
from solver_backend import coo_from_triplets,solve_sparse

def solve_dynamic_up3d_hex(lx:float,ly:float,lz:float,nx:int,ny:int,nz:int,material:dict,
                           accel_m_s2:list[list[float]],dt_s:float,permeability_m_s:float=1e-6,
                           storage_1_kpa:float=1e-6,biot_alpha:float=1.0,density_kg_m3:float=1800,
                           rayleigh_a0:float=0.0,rayleigh_a1:float=0.0,absorbing_boundaries:bool=True,
                           drained_top_kpa:float|None=0.0,newton_max:int=15,tolerance:float=1e-5,
                           beta:float=.25,gamma:float=.5,linear_method:str="auto",backend:str="auto")->dict:
    """Dynamic HEX8 u-p solver with Newmark inertia, base acceleration and Lysmer-style dashpots."""
    nodes,hexes=structured_hex_mesh(lx,ly,lz,max(2,nx),max(2,ny),max(2,nz));nn=len(nodes);nd=4*nn
    model=make_material3d(material);states=[[model.initial() for _ in range(8)] for _ in hexes]
    x=np.zeros(nd);v=np.zeros(3*nn);a=np.zeros(3*nn);history=[]
    top=np.where(np.isclose(nodes[:,2],lz))[0];bottom=np.where(np.isclose(nodes[:,2],0))[0]
    p_off=3*nn
    # full state maps [ux,uy,uz,p] stored separately for convenience
    U=np.zeros((nn,3));P=np.zeros(nn)
    # vertical support; horizontal earthquake applied as inertia forcing
    fixed_mech=[3*i+2 for i in bottom]+[3*int(bottom[0]),3*int(bottom[0])+1]
    side=np.where(np.isclose(nodes[:,0],0)|np.isclose(nodes[:,0],lx)|np.isclose(nodes[:,1],0)|np.isclose(nodes[:,1],ly))[0]
    E=float(material.get("E_kpa",material.get("E50_ref_kpa",50000)))*1000;nu=float(material.get("nu",material.get("nu_ur",.3)))
    G=E/(2*(1+nu));rho=density_kg_m3;vs=math.sqrt(max(G/rho,1e-12));vp=math.sqrt(max((E*(1-nu)/((1+nu)*(1-2*nu)))/rho,1e-12))
    a0n=1/(beta*dt_s**2);a1n=gamma/(beta*dt_s)

    for step,ag_raw in enumerate(accel_m_s2,1):
        ag=np.asarray(ag_raw,float);ag=np.pad(ag,(0,max(0,3-len(ag))))[:3]
        Uold=U.copy();Vold=v.reshape(nn,3).copy();Aold=a.reshape(nn,3).copy();Pold=P.copy()
        Utrial=U.copy();Ptrial=P.copy();committed=[[s.copy() for s in el] for el in states];conv=False
        Upred=Uold+dt_s*Vold+dt_s**2*(.5-beta)*Aold
        Vpred=Vold+dt_s*(1-gamma)*Aold
        for it in range(newton_max):
            rows=[];cols=[];data=[];Rm=np.zeros(3*nn);Rp=np.zeros(nn);trial=[[s.copy() for s in el] for el in committed]
            Mdiag=np.zeros(3*nn);Kdiag_for_damp=np.zeros(3*nn)
            for e,conn in enumerate(hexes):
                xy=nodes[conn];udofs=np.array([[3*n,3*n+1,3*n+2] for n in conn]).ravel()
                ue=Utrial[conn].reshape(-1);ue0=Uold[conn].reshape(-1);pe=Ptrial[conn];pe0=Pold[conn]
                Kuu=np.zeros((24,24));Kup=np.zeros((24,8));Kpu=np.zeros((8,24));Kpp=np.zeros((8,8));ru=np.zeros(24);rp=np.zeros(8);gp=0;vol=0
                for xi in GP:
                    for eta in GP:
                        for zeta in GP:
                            N,grad,B,det=hex8_B(xy,xi,eta,zeta);vol+=det;deps=B@(ue-ue0);pm=float(N@pe)
                            if isinstance(model,LiquefactionSandStyle):st,C,meta=model.integrate(committed[e][gp],deps,max(1,-pm+100))
                            else:st,C,meta=model.integrate(committed[e][gp],deps)
                            trial[e][gp]=st;gp+=1
                            sigma=st.stress.copy();sigma[:3]-=biot_alpha*pm
                            bvol=np.zeros(24)
                            for aa in range(8):bvol[3*aa]=B[0,3*aa];bvol[3*aa+1]=B[1,3*aa+1];bvol[3*aa+2]=B[2,3*aa+2]
                            Kuu+=B.T@C@B*det;Kup+=-biot_alpha*np.outer(bvol,N)*det;Kpu+=biot_alpha*np.outer(N,bvol)*det/dt_s
                            Kpp+=storage_1_kpa*np.outer(N,N)*det/dt_s+(permeability_m_s/9.81)*(grad@grad.T)*det
                            ru+=B.T@sigma*det;rp+=storage_1_kpa*np.outer(N,N)@(pe-pe0)*det/dt_s+biot_alpha*np.outer(N,bvol)@(ue-ue0)*det/dt_s+(permeability_m_s/9.81)*(grad@grad.T)@pe*det
                mnode=rho*vol/8
                for n in conn:
                    for d in range(3):Mdiag[3*n+d]+=mnode
                for aa,I in enumerate(udofs):
                    Rm[I]+=ru[aa]
                    for bb,J in enumerate(udofs):rows.append(I);cols.append(J);data.append(Kuu[aa,bb])
                    for bb,nj in enumerate(conn):rows.append(I);cols.append(3*nn+nj);data.append(Kup[aa,bb])
                for aa,ni in enumerate(conn):
                    Rp[ni]+=rp[aa]
                    for bb,J in enumerate(udofs):rows.append(3*nn+ni);cols.append(J);data.append(Kpu[aa,bb])
                    for bb,nj in enumerate(conn):rows.append(3*nn+ni);cols.append(3*nn+nj);data.append(Kpp[aa,bb])
            Anew=(Utrial-Upred)*a0n;Vnew=Vpred+gamma*dt_s*Anew
            accvec=Anew.reshape(-1);velvec=Vnew.reshape(-1)
            Rm += Mdiag*accvec + rayleigh_a0*Mdiag*velvec
            # earthquake input as inertia forcing
            for n in range(nn):
                for d in range(3):Rm[3*n+d]+=Mdiag[3*n+d]*ag[d]
            # optional absorbing dashpots on lateral boundaries
            if absorbing_boundaries:
                area_scale=max((ly*lz+lx*lz)/(max(len(side),1)),1e-9)
                for n in side:
                    Rm[3*n]+=rho*vs*area_scale*Vnew[n,0];Rm[3*n+1]+=rho*vs*area_scale*Vnew[n,1];Rm[3*n+2]+=rho*vp*area_scale*Vnew[n,2]
            K=coo_from_triplets(rows,cols,data,(4*nn,4*nn)).tolil()
            for i,mv in enumerate(Mdiag):K[i,i]+=a0n*mv+rayleigh_a0*a1n*mv
            if absorbing_boundaries:
                area_scale=max((ly*lz+lx*lz)/(max(len(side),1)),1e-9)
                for n in side:
                    K[3*n,3*n]+=a1n*rho*vs*area_scale;K[3*n+1,3*n+1]+=a1n*rho*vs*area_scale;K[3*n+2,3*n+2]+=a1n*rho*vp*area_scale
            R=np.r_[Rm,Rp]
            fixed=list(fixed_mech)
            if drained_top_kpa is not None:
                for n in top:
                    d=3*nn+n;R[d]=Ptrial[n]-drained_top_kpa;K.rows[d]=[d];K.data[d]=[1.0];fixed.append(d)
            K=K.tocsr();free=np.setdiff1d(np.arange(4*nn),np.array(fixed,int));nr=float(np.linalg.norm(R[free]))
            if nr<tolerance*max(1,float(np.linalg.norm(np.r_[Utrial.reshape(-1),Ptrial]))):
                conv=True;states=trial;break
            dx,info=solve_sparse(K[np.ix_(free,free)],-R[free],method=linear_method,backend=backend,tol=min(1e-8,tolerance*.1))
            full=np.zeros(4*nn);full[free]=dx;Utrial+=full[:3*nn].reshape(nn,3);Ptrial+=full[3*nn:]
        U=Utrial;P=Ptrial;a=((U-Upred)*a0n).reshape(-1);v=(Vpred+gamma*dt_s*a.reshape(nn,3)).reshape(-1)
        history.append({"step":step,"time_s":step*dt_s,"converged":conv,"iterations":it+1,"residual":nr,"max_displacement_m":float(np.linalg.norm(U,axis=1).max()),"pore_pressure_max_kpa":float(P.max()),"input_accel_m_s2":ag.tolist()})
    return {"nodes_m":nodes.tolist(),"hexahedra":hexes.tolist(),"displacement_m":U.tolist(),"pore_pressure_kpa":P.tolist(),"velocity_m_s":v.reshape(nn,3).tolist(),"history":history,
      "status":"solved" if all(h["converged"] for h in history) else "nonlinear_iteration_warning","method":"dynamic 3D HEX8 u-p Newmark solver with inertia, effective stress, base acceleration and absorbing dashpots"}
