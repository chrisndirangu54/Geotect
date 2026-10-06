from __future__ import annotations
import numpy as np,math
from mesh3d import structured_hex_mesh,hex_to_tets,tet_B,elastic_D3
from materials3d import AnisotropicCriticalState,LiquefactionSandStyle,State3D
from solver_backend import coo_from_triplets,solve_sparse

def make_material3d(spec:dict):
    kind=spec.get("model","anisotropic_critical_state")
    if kind in {"liquefaction_sand_style","pm4sand_style","ubcsand_style"}:
        return LiquefactionSandStyle(float(spec.get("Dr",.5)),float(spec.get("G0",500)),float(spec.get("hpo",.5)),
          float(spec.get("density",1.8)),float(spec.get("phic_deg",33)),float(spec.get("contraction",.5)),
          float(spec.get("dilation",.2)),float(spec.get("fabric_rate",2.0)))
    return AnisotropicCriticalState(float(spec.get("E_kpa",50000)),float(spec.get("nu",.3)),float(spec.get("M",1.2)),
      float(spec.get("lambda_c",.12)),float(spec.get("kappa",.02)),float(spec.get("pc0_kpa",100)),float(spec.get("anisotropy",.2)))

def solve_up3d_tet(lx:float,ly:float,lz:float,nx:int,ny:int,nz:int,material:dict,
                   permeability_m_s:float=1e-6,storage_1_kpa:float=1e-6,biot_alpha:float=1.0,
                   dt_s:float=60,steps:int=1,top_pressure_kpa:float=0,density_kg_m3:float=0,
                   drained_top_kpa:float|None=0.0,newton_max:int=20,tolerance:float=1e-6,
                   linear_method:str="auto",backend:str="auto")->dict:
    nodes,hexes=structured_hex_mesh(lx,ly,lz,max(2,nx),max(2,ny),max(2,nz));tets=hex_to_tets(hexes)
    nn=len(nodes);nd=4*nn;model=make_material3d(material);states=[model.initial() for _ in tets]
    xprev=np.zeros(nd);top=np.where(np.isclose(nodes[:,2],lz))[0];bottom=np.where(np.isclose(nodes[:,2],0))[0]
    fixed=[4*i+2 for i in bottom]
    # prevent rigid translation
    fixed += [4*int(bottom[0]),4*int(bottom[0])+1]
    history=[]
    for step in range(1,max(1,steps)+1):
        old=xprev.copy();x=old.copy();committed=[s.copy() for s in states];lf=step/max(1,steps);conv=False
        for it in range(newton_max):
            rows=[];cols=[];data=[];R=np.zeros(nd);trial=[s.copy() for s in committed]
            for e,conn in enumerate(tets):
                xy=nodes[conn];B,V,grad=tet_B(xy)
                udofs=np.array([[4*n,4*n+1,4*n+2] for n in conn]).ravel();pdofs=np.array([4*n+3 for n in conn])
                ue=x[udofs];ue0=old[udofs];pe=x[pdofs];pe0=old[pdofs]
                deps=B@(ue-ue0)
                pmean=float(np.mean(pe))
                if isinstance(model,LiquefactionSandStyle):
                    st,C,meta=model.integrate(committed[e],deps,max(1.0,-pmean+100))
                else:
                    st,C,meta=model.integrate(committed[e],deps)
                trial[e]=st
                N=np.full(4,.25)
                sigma=st.stress.copy();sigma[:3]-=biot_alpha*pmean
                Kuu=B.T@C@B*V
                bvol=np.zeros(12)
                for a in range(4):
                    bvol[3*a]=B[0,3*a];bvol[3*a+1]=B[1,3*a+1];bvol[3*a+2]=B[2,3*a+2]
                Kup=-biot_alpha*np.outer(bvol,N)*V
                Kpu=biot_alpha*np.outer(N,bvol)*V/dt_s
                Kpp=storage_1_kpa*np.outer(N,N)*V/dt_s+(permeability_m_s/9.81)*(grad@grad.T)*V
                ru=B.T@sigma*V;rp=storage_1_kpa*np.outer(N,N)@(pe-pe0)*V/dt_s+biot_alpha*np.outer(N,bvol)@(ue-ue0)*V/dt_s+(permeability_m_s/9.81)*(grad@grad.T)@pe*V
                body=-density_kg_m3*9.81/1000
                for a in range(4):ru[3*a+2]-=lf*body*V/4
                for a,I in enumerate(udofs):
                    R[I]+=ru[a]
                    for b,J in enumerate(udofs):rows.append(I);cols.append(J);data.append(Kuu[a,b])
                    for b,J in enumerate(pdofs):rows.append(I);cols.append(J);data.append(Kup[a,b])
                for a,I in enumerate(pdofs):
                    R[I]+=rp[a]
                    for b,J in enumerate(udofs):rows.append(I);cols.append(J);data.append(Kpu[a,b])
                    for b,J in enumerate(pdofs):rows.append(I);cols.append(J);data.append(Kpp[a,b])
            if top_pressure_kpa:
                q=-lf*top_pressure_kpa
                area=lx*ly/max(len(top),1)
                for n in top:R[4*n+2]-=q*area
            K=coo_from_triplets(rows,cols,data,(nd,nd)).tolil()
            fixed_now=list(fixed)
            if drained_top_kpa is not None:
                for n in top:
                    d=4*n+3;R[d]=x[d]-drained_top_kpa;K.rows[d]=[d];K.data[d]=[1.0];fixed_now.append(d)
            K=K.tocsr();free=np.setdiff1d(np.arange(nd),np.array(fixed_now,int))
            nr=float(np.linalg.norm(R[free]))
            if nr<tolerance*max(1.0,float(np.linalg.norm(x[free]))):
                conv=True;states=trial;xprev=x;break
            dx,info=solve_sparse(K[np.ix_(free,free)],-R[free],method=linear_method,backend=backend,tol=min(1e-8,tolerance*.1))
            x[free]+=dx
        if not conv:states=trial;xprev=x
        U=np.array([[xprev[4*i],xprev[4*i+1],xprev[4*i+2]] for i in range(nn)]);P=np.array([xprev[4*i+3] for i in range(nn)])
        history.append({"step":step,"converged":conv,"iterations":it+1,"residual":nr,"max_displacement_m":float(np.linalg.norm(U,axis=1).max()),"p_min_kpa":float(P.min()),"p_max_kpa":float(P.max())})
    U=np.array([[xprev[4*i],xprev[4*i+1],xprev[4*i+2]] for i in range(nn)]);P=np.array([xprev[4*i+3] for i in range(nn)])
    return {"nodes_m":nodes.tolist(),"tetrahedra":tets.tolist(),"displacement_m":U.tolist(),"pore_pressure_kpa":P.tolist(),
      "history":history,"status":"solved" if all(h["converged"] for h in history) else "nonlinear_iteration_warning",
      "material_model":material.get("model","anisotropic_critical_state"),
      "method":"3D tetrahedral monolithic u-p FEM research solver"}
