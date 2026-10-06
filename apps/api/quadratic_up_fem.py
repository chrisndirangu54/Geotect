from __future__ import annotations
import numpy as np,math
from mixed_elements import enrich_triangles_p2,GAUSS_TRI_3,p2_gradients_physical,p1_shape,p1_gradients_physical,b_matrix_p2,pressure_stabilization,stabilization_tau
from elastoplastic_fem import structured_tri_mesh,make_material
from elastoplastic_materials import MaterialState,numerical_tangent
from solver_backend import coo_from_triplets,solve_sparse

GAMMA_W=9.81

def solve_quadratic_up_2d(width_m:float,height_m:float,nx:int,ny:int,material:dict,
                          permeability_m_s:float=1e-6,storage_1_kpa:float=1e-6,biot_alpha:float=1.0,
                          dt_s:float=3600,steps:int=1,top_pressure_kpa:float=0,density_kg_m3:float=0,
                          drained_top_kpa:float|None=0.0,stabilization_scale:float=.05,
                          newton_max:int=20,tolerance:float=1e-6,linear_method:str="auto",backend:str="auto")->dict:
    """Quadratic-displacement / linear-pressure P2-P1 monolithic u-p FEM."""
    vnodes,tris3=structured_tri_mesh(width_m,height_m,max(2,int(nx)),max(2,int(ny)))
    unodes,tris6,_=enrich_triangles_p2(vnodes,tris3)
    nu=len(unodes);npn=len(vnodes);nd=2*nu+npn
    model=make_material(material)
    states=[[model.initial_state() for _ in GAUSS_TRI_3] for _ in range(len(tris6))]
    xprev=np.zeros(nd);history=[]
    top_u=np.where(np.isclose(unodes[:,1],height_m))[0];bot_u=np.where(np.isclose(unodes[:,1],0))[0]
    top_p=np.where(np.isclose(vnodes[:,1],height_m))[0]
    fixed_u=[2*i+1 for i in bot_u]+[2*int(bot_u[0])]
    p_offset=2*nu

    for step in range(1,max(1,steps)+1):
        old=xprev.copy();x=old.copy();committed=[[s.copy() for s in el] for el in states];lf=step/max(1,steps)
        converged=False
        for it in range(newton_max):
            rows=[];cols=[];data=[];R=np.zeros(nd);trial=[[s.copy() for s in el] for el in committed]
            for e,(conn6,conn3) in enumerate(zip(tris6,tris3)):
                xy6=unodes[conn6];xy3=vnodes[conn3]
                udofs=np.array([[2*n,2*n+1] for n in conn6]).ravel()
                pdofs=p_offset+conn3
                ue=x[udofs];ue0=old[udofs];pe=x[pdofs];pe0=old[pdofs]
                Kuu=np.zeros((12,12));Kup=np.zeros((12,3));Kpu=np.zeros((3,12));Kpp=np.zeros((3,3))
                ru=np.zeros(12);rp=np.zeros(3)
                gradP,detP=p1_gradients_physical(xy3);area=detP/2
                h=math.sqrt(4*area/math.pi)
                Eref=float(material.get("E_kpa",material.get("E50_ref_kpa",30000)));nuref=float(material.get("nu",material.get("nu_ur",.3)))
                stab=pressure_stabilization(gradP,area,stabilization_tau(h,Eref,nuref,stabilization_scale))
                for gp,(r,s,w) in enumerate(GAUSS_TRI_3):
                    N2,grad2,detJ=p2_gradients_physical(xy6,r,s);B=b_matrix_p2(grad2);N1,_,_=p1_shape(r,s);weight=detJ*w
                    deps=B@(ue-ue0)
                    st,C,info=numerical_tangent(model,committed[e][gp],deps);trial[e][gp]=st
                    pc=float(N1@pe)
                    sigma=st.stress+np.array([-biot_alpha*pc,-biot_alpha*pc,0.0])
                    Kuu+=B.T@C@B*weight
                    bvol=np.array([B[0,0],B[1,1],B[0,2],B[1,3],B[0,4],B[1,5],B[0,6],B[1,7],B[0,8],B[1,9],B[0,10],B[1,11]])
                    Kup+=-biot_alpha*np.outer(bvol,N1)*weight
                    Kpu+=biot_alpha*np.outer(N1,bvol)*weight/dt_s
                    Kpp+=storage_1_kpa*np.outer(N1,N1)*weight/dt_s+(permeability_m_s/GAMMA_W)*(gradP@gradP.T)*weight
                    ru+=B.T@sigma*weight
                    rp+=storage_1_kpa*np.outer(N1,N1)@(pe-pe0)*weight/dt_s+biot_alpha*np.outer(N1,bvol)@(ue-ue0)*weight/dt_s+(permeability_m_s/GAMMA_W)*(gradP@gradP.T)@pe*weight
                    body=-density_kg_m3*9.81/1000
                    for a in range(6):ru[2*a+1]-=lf*body*N2[a]*weight
                Kpp+=stab
                for a,I in enumerate(udofs):
                    R[I]+=ru[a]
                    for b,J in enumerate(udofs):rows.append(I);cols.append(J);data.append(Kuu[a,b])
                    for b,J in enumerate(pdofs):rows.append(I);cols.append(J);data.append(Kup[a,b])
                for a,I in enumerate(pdofs):
                    R[I]+=rp[a]
                    for b,J in enumerate(udofs):rows.append(I);cols.append(J);data.append(Kpu[a,b])
                    for b,J in enumerate(pdofs):rows.append(I);cols.append(J);data.append(Kpp[a,b])
            if top_pressure_kpa:
                order=top_u[np.argsort(unodes[top_u,0])]
                for a,b in zip(order[:-1],order[1:]):
                    L=float(np.linalg.norm(unodes[b]-unodes[a]));q=-lf*top_pressure_kpa
                    R[2*a+1]-=q*L/2;R[2*b+1]-=q*L/2
            K=coo_from_triplets(rows,cols,data,(nd,nd)).tolil()
            fixed=list(fixed_u)
            if drained_top_kpa is not None:
                for n in top_p:
                    d=p_offset+n;R[d]=x[d]-drained_top_kpa;K.rows[d]=[d];K.data[d]=[1.0];fixed.append(d)
            K=K.tocsr();free=np.setdiff1d(np.arange(nd),np.array(fixed,int))
            nr=float(np.linalg.norm(R[free]))
            if nr<tolerance*max(1.0,float(np.linalg.norm(x[free]))):
                states=trial;xprev=x;converged=True;break
            dx,info=solve_sparse(K[np.ix_(free,free)],-R[free],method=linear_method,backend=backend,tol=min(1e-8,tolerance*.1))
            x[free]+=dx
        if not converged:states=trial;xprev=x
        U=xprev[:p_offset].reshape(-1,2);P=xprev[p_offset:]
        history.append({"step":step,"converged":converged,"newton_iterations":it+1,"residual":nr,
          "max_displacement_m":float(np.linalg.norm(U,axis=1).max()),"p_min_kpa":float(P.min()),"p_max_kpa":float(P.max())})
    U=xprev[:p_offset].reshape(-1,2);P=xprev[p_offset:]
    return {"displacement_nodes_m":unodes.tolist(),"pressure_nodes_m":vnodes.tolist(),"triangles_p2":tris6.tolist(),"triangles_p1":tris3.tolist(),
      "displacement_m":U.tolist(),"pore_pressure_kpa":P.tolist(),"history":history,
      "method":"P2 displacement / P1 pressure mixed monolithic u-p FEM with pressure stabilization",
      "status":"solved" if all(h["converged"] for h in history) else "nonlinear_iteration_warning"}
