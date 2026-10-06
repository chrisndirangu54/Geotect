from __future__ import annotations
import numpy as np
from mesh3d import structured_hex_mesh,hex_to_tets,tet_B,elastic_D3
from solver_backend import coo_from_triplets,solve_sparse

def solve_thm3d_tet(lx:float,ly:float,lz:float,nx:int,ny:int,nz:int,E_kpa:float,nu:float,biot_alpha:float,
                    thermal_expansion_1_k:float,permeability_ref_m_s:float,thermal_conductivity:float,
                    heat_capacity_vol:float,storage_1_kpa:float,dt_s:float,steps:int,
                    initial_temp_c:float=20,initial_p_kpa:float=0,top_temp_c:float|None=None,top_p_kpa:float|None=0,
                    permeability_temp_coeff:float=.02,young_temp_coeff:float=.001)->dict:
    nodes,hexes=structured_hex_mesh(lx,ly,lz,max(2,nx),max(2,ny),max(2,nz));tets=hex_to_tets(hexes);nn=len(nodes);nd=5*nn
    x=np.zeros(nd)
    for i in range(nn):x[5*i+3]=initial_p_kpa;x[5*i+4]=initial_temp_c
    top=np.where(np.isclose(nodes[:,2],lz))[0];bottom=np.where(np.isclose(nodes[:,2],0))[0];fixed=[5*i+2 for i in bottom]+[5*int(bottom[0]),5*int(bottom[0])+1];history=[]
    for step in range(1,steps+1):
        old=x.copy();xn=x.copy()
        for it in range(15):
            rows=[];cols=[];data=[];R=np.zeros(nd)
            for conn in tets:
                B,V,grad=tet_B(nodes[conn]);udofs=np.array([[5*n,5*n+1,5*n+2] for n in conn]).ravel();pdofs=np.array([5*n+3 for n in conn]);tdofs=np.array([5*n+4 for n in conn])
                ue=xn[udofs];ue0=old[udofs];pe=xn[pdofs];pe0=old[pdofs];Te=xn[tdofs];Te0=old[tdofs];N=np.full(4,.25);Tm=float(N@Te)
                Eeff=E_kpa*max(.1,1-young_temp_coeff*(Tm-initial_temp_c));D=elastic_D3(Eeff,nu);k=permeability_ref_m_s*np.exp(permeability_temp_coeff*(Tm-initial_temp_c))
                eps=B@(ue-ue0);eth=thermal_expansion_1_k*(Tm-initial_temp_c)*np.array([1,1,1,0,0,0]);sigma=D@(eps-eth);pm=float(N@pe);sigma[:3]-=biot_alpha*pm
                bvol=np.zeros(12)
                for a in range(4):bvol[3*a]=B[0,3*a];bvol[3*a+1]=B[1,3*a+1];bvol[3*a+2]=B[2,3*a+2]
                Kuu=B.T@D@B*V;Kup=-biot_alpha*np.outer(bvol,N)*V;KuT=-(B.T@D@np.array([thermal_expansion_1_k]*3+[0,0,0]))[:,None]@N[None,:]*V
                Kpu=biot_alpha*np.outer(N,bvol)*V/dt_s;Kpp=storage_1_kpa*np.outer(N,N)*V/dt_s+(k/9.81)*(grad@grad.T)*V
                KTT=heat_capacity_vol*np.outer(N,N)*V/dt_s+thermal_conductivity*(grad@grad.T)*V
                ru=B.T@sigma*V;rp=storage_1_kpa*np.outer(N,N)@(pe-pe0)*V/dt_s+biot_alpha*np.outer(N,bvol)@(ue-ue0)*V/dt_s+(k/9.81)*(grad@grad.T)@pe*V
                rt=heat_capacity_vol*np.outer(N,N)@(Te-Te0)*V/dt_s+thermal_conductivity*(grad@grad.T)@Te*V
                blocks=[(udofs,udofs,Kuu),(udofs,pdofs,Kup),(udofs,tdofs,KuT),(pdofs,udofs,Kpu),(pdofs,pdofs,Kpp),(tdofs,tdofs,KTT)]
                for aa,I in enumerate(udofs):R[I]+=ru[aa]
                for aa,I in enumerate(pdofs):R[I]+=rp[aa]
                for aa,I in enumerate(tdofs):R[I]+=rt[aa]
                for ii,jj,Kb in blocks:
                    for a,I in enumerate(ii):
                        for b,J in enumerate(jj):rows.append(I);cols.append(J);data.append(Kb[a,b])
            K=coo_from_triplets(rows,cols,data,(nd,nd)).tolil();fixedn=list(fixed)
            for n in top:
                if top_p_kpa is not None:
                    d=5*n+3;R[d]=xn[d]-top_p_kpa;K.rows[d]=[d];K.data[d]=[1.0];fixedn.append(d)
                if top_temp_c is not None:
                    d=5*n+4;R[d]=xn[d]-top_temp_c;K.rows[d]=[d];K.data[d]=[1.0];fixedn.append(d)
            K=K.tocsr();free=np.setdiff1d(np.arange(nd),np.array(fixedn,int));nr=float(np.linalg.norm(R[free]))
            if nr<1e-6*max(1,float(np.linalg.norm(xn[free]))):break
            dx=solve_sparse(K[np.ix_(free,free)],-R[free],method="spsolve")[0];xn[free]+=dx
        x=xn;U=np.array([[x[5*i],x[5*i+1],x[5*i+2]] for i in range(nn)]);P=np.array([x[5*i+3] for i in range(nn)]);T=np.array([x[5*i+4] for i in range(nn)])
        history.append({"step":step,"max_displacement_m":float(np.linalg.norm(U,axis=1).max()),"p_range_kpa":[float(P.min()),float(P.max())],"T_range_c":[float(T.min()),float(T.max())],"iterations":it+1})
    return {"nodes_m":nodes.tolist(),"tetrahedra":tets.tolist(),"displacement_m":U.tolist(),"pore_pressure_kpa":P.tolist(),"temperature_c":T.tolist(),"history":history,"method":"nonlinear 3D tetrahedral THM u-p-T FEM with temperature-dependent stiffness/permeability"}
