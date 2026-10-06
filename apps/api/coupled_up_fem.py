from __future__ import annotations
import math,numpy as np
from concurrent.futures import ThreadPoolExecutor
from elastoplastic_fem import structured_tri_mesh,tri_B,make_material
from elastoplastic_materials import MaterialState,numerical_tangent
from solver_backend import coo_from_triplets,solve_sparse
from interface_elements import InterfaceState,interface_global_force_tangent

GAMMA_W_KPA_M=9.81

def _N_centroid():
    return np.array([1/3,1/3,1/3],dtype=float)

def _gradN(xy:np.ndarray):
    B,A=tri_B(xy)
    return np.array([[B[0,0],B[0,2],B[0,4]],[B[1,1],B[1,3],B[1,5]]]),A

def _retention_from_pressure(p_kpa:float,hydraulic:dict):
    theta_r=float(hydraulic.get("theta_r",.05));theta_s=float(hydraulic.get("theta_s",.45))
    alpha=float(hydraulic.get("alpha_1_m",1.6));n=float(hydraulic.get("n_vg",1.6));m=1-1/n
    ks=float(hydraulic.get("ks_m_s",1e-6));ell=float(hydraulic.get("mualem_l",.5));beta=float(hydraulic.get("bishop_beta",1.0))
    if p_kpa>=0:
        return {"Se":1.0,"theta":theta_s,"C_1_kpa":float(hydraulic.get("saturated_storage_1_kpa",1e-6)),
                "K_m_s":ks,"chi":1.0,"dchi_dp":0.0}
    h=p_kpa/GAMMA_W_KPA_M;ah=alpha*abs(h);Se=(1+ah**n)**(-m)
    theta=theta_r+(theta_s-theta_r)*Se
    # dSe/dp; p is negative in suction
    dSe_dh=m*n*(alpha**n)*(abs(h)**(n-1))*(1+ah**n)**(-m-1)
    dSe_dp=dSe_dh/GAMMA_W_KPA_M
    C=max((theta_s-theta_r)*dSe_dp,1e-10)
    term=max(0.0,1-(1-Se**(1/m))**m)
    Kr=(Se**ell)*term**2
    chi=Se**beta
    dchi=beta*max(Se,1e-12)**(beta-1)*dSe_dp
    return {"Se":Se,"theta":theta,"C_1_kpa":C,"K_m_s":ks*Kr,"chi":chi,"dchi_dp":dchi}

def _serialize_state(s:MaterialState):
    return {"stress":s.stress.tolist(),"plastic_strain":s.plastic_strain.tolist(),"eq_plastic_shear":s.eq_plastic_shear,
      "plastic_volumetric":s.plastic_volumetric,"pc_kpa":s.pc_kpa,"yielded":s.yielded}

def solve_monolithic_up_2d(width_m:float,height_m:float,nx:int,ny:int,material:dict,hydraulic:dict,
                           dt_s:float=3600,steps:int=1,biot_alpha:float=1.0,density_kg_m3:float=2000,
                           gravity_m_s2:float=9.81,top_pressure_kpa:float=0,initial_pore_pressure_kpa:float=0,
                           drained_top_kpa:float|None=0.0,no_flow_sides:bool=True,
                           rainfall_flux_m_s:float=0.0,newton_max:int=25,tolerance:float=1e-6,
                           linear_method:str="auto",backend:str="auto",parallel_assembly:bool=True,
                           inactive_elements:list[int]|None=None,interfaces:list[dict]|None=None,
                           initial_displacement:list[list[float]]|None=None,initial_pressure_kpa:list[float]|None=None,
                           initial_states:list[dict]|None=None)->dict:
    """2D monolithic u-p FEM with elastoplastic skeleton and saturated/unsaturated flow.

    Unknown ordering is [ux, uy, p] per node. Soil stresses are kPa; pore pressure
    is kPa; permeability is m/s. The flow block uses pressure head p/gamma_w.
    """
    nx=max(2,int(nx));ny=max(2,int(ny));nodes,tris=structured_tri_mesh(width_m,height_m,nx,ny);nn=len(nodes);nd=3*nn
    model=make_material(material);inactive=set(inactive_elements or []);active=np.array([i not in inactive for i in range(len(tris))])
    states=[model.initial_state() for _ in tris]
    if initial_states:
        for i,s in enumerate(initial_states[:len(states)]):
            states[i]=MaterialState(np.asarray(s.get("stress",[0,0,0]),float),np.asarray(s.get("plastic_strain",[0,0,0]),float),
                float(s.get("eq_plastic_shear",0)),float(s.get("plastic_volumetric",0)),float(s.get("pc_kpa",100)),bool(s.get("yielded",False)))
    u0=np.zeros((nn,2)) if initial_displacement is None else np.asarray(initial_displacement,float)
    p0=np.full(nn,float(initial_pore_pressure_kpa)) if initial_pressure_kpa is None else np.asarray(initial_pressure_kpa,float)
    if u0.shape!=(nn,2) or p0.shape!=(nn,):raise ValueError("initial fields do not match mesh")
    xprev=np.zeros(nd)
    for i in range(nn):xprev[3*i:3*i+2]=u0[i];xprev[3*i+2]=p0[i]
    top=np.where(np.isclose(nodes[:,1],height_m))[0];bottom=np.where(np.isclose(nodes[:,1],0))[0]
    left=np.where(np.isclose(nodes[:,0],0))[0];right=np.where(np.isclose(nodes[:,0],width_m))[0]
    fixed_u=[3*i+1 for i in bottom]+[3*int(bottom[0])]
    iface_states=[InterfaceState() for _ in (interfaces or [])]
    time_history=[]

    def assemble(x,committed,old_x,load_factor):
        rows=[];cols=[];data=[];R=np.zeros(nd);trial=[s.copy() for s in committed]
        def elem(e):
            if not active[e]:return e,[],[],[],np.array([],float),committed[e],{}
            conn=tris[e];xy=nodes[conn];B,A=tri_B(xy);gradN,_=_gradN(xy);N=_N_centroid()
            udofs=np.array([[3*n,3*n+1] for n in conn]).ravel();pdofs=np.array([3*n+2 for n in conn])
            ue=x[udofs];ue0=old_x[udofs];pe=x[pdofs];pe0=old_x[pdofs]
            deps=B@(ue-ue0)
            st,C,info=numerical_tangent(model,committed[e],deps)
            pc=float(N@pe);pc0=float(N@pe0);ret=_retention_from_pressure(pc,hydraulic)
            chi=ret["chi"];dchi=ret["dchi_dp"];Ksat=ret["K_m_s"];storage=ret["C_1_kpa"]+float(hydraulic.get("specific_storage_1_kpa",0))
            sigma_total=st.stress+np.array([-biot_alpha*chi*pc,-biot_alpha*chi*pc,0.0])
            fint=B.T@sigma_total*A
            fbody=np.zeros(6);body=-density_kg_m3*gravity_m_s2/1000
            for a in range(3):fbody[2*a+1]=load_factor*body*A/3
            Kuu=B.T@C@B*A
            bvol=np.array([B[0,0],B[1,1],B[0,2],B[1,3],B[0,4],B[1,5]])
            dsig_dp=-biot_alpha*(chi+pc*dchi)
            Kup=np.outer(bvol,N)*dsig_dp*A
            H=(Ksat/GAMMA_W_KPA_M)*(gradN.T@gradN)*A
            M=storage*np.outer(N,N)*A
            Q=biot_alpha*chi*np.outer(N,bvol)*A
            rp=M@((pe-pe0)/dt_s)+Q@((ue-ue0)/dt_s)+H@pe
            Kpu=Q/dt_s
            Kpp=M/dt_s+H
            lr=[];lc=[];ld=[]
            for a,I in enumerate(udofs):
                for b,J in enumerate(udofs):lr.append(I);lc.append(J);ld.append(Kuu[a,b])
                for b,J in enumerate(pdofs):lr.append(I);lc.append(J);ld.append(Kup[a,b])
            for a,I in enumerate(pdofs):
                for b,J in enumerate(udofs):lr.append(I);lc.append(J);ld.append(Kpu[a,b])
                for b,J in enumerate(pdofs):lr.append(I);lc.append(J);ld.append(Kpp[a,b])
            rr=np.zeros(nd);rr[udofs]+=fint-fbody;rr[pdofs]+=rp
            return e,lr,lc,ld,rr,st,{"Se":ret["Se"],"chi":chi,"K_m_s":Ksat,"p_kpa":pc}
        if parallel_assembly and len(tris)>16:
            with ThreadPoolExecutor() as ex:parts=list(ex.map(elem,range(len(tris))))
        else:parts=[elem(e) for e in range(len(tris))]
        elem_meta=[]
        for e,lr,lc,ld,rr,st,meta in parts:
            rows.extend(lr);cols.extend(lc);data.extend(ld);R+=rr;trial[e]=st;elem_meta.append(meta)
        # mechanical surface load
        if top_pressure_kpa:
            order=top[np.argsort(nodes[top,0])]
            for a,b in zip(order[:-1],order[1:]):
                L=float(np.linalg.norm(nodes[b]-nodes[a]));q=-load_factor*top_pressure_kpa
                R[3*a+1]-=q*L/2;R[3*b+1]-=q*L/2
        # rainfall flux positive downward; residual convention adds outward flux.
        if rainfall_flux_m_s:
            order=top[np.argsort(nodes[top,0])]
            for a,b in zip(order[:-1],order[1:]):
                L=float(np.linalg.norm(nodes[b]-nodes[a]));val=-rainfall_flux_m_s*L/2
                R[3*a+2]+=val;R[3*b+2]+=val
        # interface contributions
        new_ifaces=[]
        for ii,spec in enumerate(interfaces or []):
            a=int(spec["node_a"]);b=int(spec["node_b"]);ua=x[3*a:3*a+2];ub=x[3*b:3*b+2]
            ns,fi,Ki,meta=interface_global_force_tangent(nodes[a],nodes[b],ua,ub,iface_states[ii],
                float(spec.get("normal_stiffness_kpa_m",1e6)),float(spec.get("shear_stiffness_kpa_m",1e5)),
                float(spec.get("friction_deg",30)),float(spec.get("cohesion_kpa",0)),float(spec.get("dilation_deg",0)))
            dofs=[3*a,3*a+1,3*b,3*b+1];R[dofs]+=fi
            for ia,I in enumerate(dofs):
                for jb,J in enumerate(dofs):rows.append(I);cols.append(J);data.append(Ki[ia,jb])
            new_ifaces.append(ns)
        K=coo_from_triplets(rows,cols,data,(nd,nd))
        return R,K,trial,elem_meta,new_ifaces

    for step in range(1,max(1,steps)+1):
        old=xprev.copy();x=old.copy();committed=[s.copy() for s in states];lf=step/max(1,steps);converged=False
        for it in range(newton_max):
            R,K,trial,meta,new_ifaces=assemble(x,committed,old,lf)
            fixed=list(fixed_u)
            if drained_top_kpa is not None:
                for n in top:
                    dof=3*n+2;R[dof]=x[dof]-drained_top_kpa
                    K=K.tolil();K.rows[dof]=[dof];K.data[dof]=[1.0];K=K.tocsr()
                    fixed.append(dof)
            free=np.setdiff1d(np.arange(nd),np.array(fixed,dtype=int))
            nr=float(np.linalg.norm(R[free]));scale=max(1.0,float(np.linalg.norm(x[free])))
            if nr<tolerance*scale:
                states=trial;xprev=x;iface_states[:]=new_ifaces;converged=True;break
            dx,linfo=solve_sparse(K[np.ix_(free,free)],-R[free],linear_method,backend=backend,tol=min(1e-8,tolerance*.1))
            alpha=1.0
            if np.linalg.norm(dx)>max(width_m,height_m):alpha=max(width_m,height_m)/max(np.linalg.norm(dx),1e-12)
            x[free]+=alpha*dx
        if not converged:
            states=trial;xprev=x;iface_states[:]=new_ifaces
        U=np.array([[xprev[3*i],xprev[3*i+1]] for i in range(nn)]);P=np.array([xprev[3*i+2] for i in range(nn)])
        time_history.append({"step":step,"time_s":step*dt_s,"converged":converged,"newton_iterations":it+1,
          "residual_norm":nr,"max_displacement_m":float(np.linalg.norm(U,axis=1).max()),"p_min_kpa":float(P.min()),"p_max_kpa":float(P.max()),
          "linear_backend":linfo.backend if 'linfo' in locals() else None,"linear_method":linfo.method if 'linfo' in locals() else None})

    U=np.array([[xprev[3*i],xprev[3*i+1]] for i in range(nn)]);P=np.array([xprev[3*i+2] for i in range(nn)])
    return {"nodes_m":nodes.tolist(),"triangles":tris.tolist(),"displacement_m":U.tolist(),"pore_pressure_kpa":P.tolist(),
      "element_states":[_serialize_state(s) for s in states],"interface_states":[s.__dict__ for s in iface_states],
      "history":time_history,"method":"2D monolithic u-p FEM with elastoplastic skeleton, Biot/Bishop coupling and pressure-dependent unsaturated flow",
      "status":"solved" if all(h["converged"] for h in time_history) else "nonlinear_iteration_warning",
      "assumptions":["small strain","linear triangular interpolation","Bishop chi=Se^beta","van Genuchten-Mualem unsaturated hydraulics"]}
