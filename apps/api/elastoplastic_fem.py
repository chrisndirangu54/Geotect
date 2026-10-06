from __future__ import annotations
import math,numpy as np
from elastoplastic_materials import MohrCoulomb,HardeningSoil,MaterialState,numerical_tangent

def structured_tri_mesh(width:float,height:float,nx:int,ny:int):
    xs=np.linspace(0,width,nx);ys=np.linspace(0,height,ny)
    nodes=np.array([[x,y] for y in ys for x in xs],dtype=float)
    tris=[]
    for j in range(ny-1):
        for i in range(nx-1):
            a=j*nx+i;b=a+1;c=a+nx;d=c+1
            tris += [[a,b,d],[a,d,c]]
    return nodes,np.asarray(tris,dtype=int)

def tri_B(xy:np.ndarray):
    x1,y1=xy[0];x2,y2=xy[1];x3,y3=xy[2]
    A=.5*((x2-x1)*(y3-y1)-(x3-x1)*(y2-y1))
    if A<=0: raise ValueError("non-positive element area")
    b=np.array([y2-y3,y3-y1,y1-y2]);c=np.array([x3-x2,x1-x3,x2-x1])
    B=np.zeros((3,6))
    for i in range(3):
        B[0,2*i]=b[i];B[1,2*i+1]=c[i];B[2,2*i]=c[i];B[2,2*i+1]=b[i]
    B/=2*A
    return B,A

def make_material(spec:dict):
    kind=spec.get("model","mohr_coulomb")
    if kind=="hardening_soil":
        return HardeningSoil(
          float(spec["E50_ref_kpa"]),float(spec["Eoed_ref_kpa"]),float(spec["Eur_ref_kpa"]),float(spec.get("nu_ur",.2)),
          float(spec.get("cohesion_kpa",0)),float(spec.get("friction_deg",30)),float(spec.get("dilation_deg",0)),float(spec.get("m",.5)),
          float(spec.get("p_ref_kpa",100)),float(spec.get("Rf",.9)),float(spec.get("pc0_kpa",100)),float(spec.get("cap_M",1.2)))
    return MohrCoulomb(float(spec.get("E_kpa",30000)),float(spec.get("nu",.3)),float(spec.get("cohesion_kpa",5)),
                       float(spec.get("friction_deg",30)),float(spec.get("dilation_deg",0)),float(spec.get("tensile_cutoff_kpa",0)))

def _state_from_dict(s:dict)->MaterialState:
    return MaterialState(np.asarray(s.get("stress",[0,0,0]),dtype=float),np.asarray(s.get("plastic_strain",[0,0,0]),dtype=float),
        float(s.get("eq_plastic_shear",0)),float(s.get("plastic_volumetric",0)),float(s.get("pc_kpa",100)),bool(s.get("yielded",False)))

def _state_dict(s:MaterialState)->dict:
    return {"stress":s.stress.tolist(),"plastic_strain":s.plastic_strain.tolist(),"eq_plastic_shear":s.eq_plastic_shear,
      "plastic_volumetric":s.plastic_volumetric,"pc_kpa":s.pc_kpa,"yielded":s.yielded}

def solve_elastoplastic_2d(width_m:float,height_m:float,nx:int,ny:int,material:dict,
                          density_kg_m3:float=2000,gravity_m_s2:float=9.81,top_pressure_kpa:float=0,
                          load_steps:int=10,newton_max:int=30,tolerance:float=1e-6,
                          inactive_elements:list[int]|None=None,contact_penalty_kpa_m:float=1e8,
                          contact_y_m:float=0.0,adaptive_cycles:int=0,refine_fraction:float=.15,
                          initial_displacement:list[list[float]]|None=None,initial_states:list[dict]|None=None,
                          mesh_nodes_m:list[list[float]]|None=None,mesh_triangles:list[list[int]]|None=None)->dict:
    """Incremental 2D small-strain elastoplastic triangular FEM."""
    if mesh_nodes_m is not None and mesh_triangles is not None:\n        nodes=np.asarray(mesh_nodes_m,dtype=float);tris=np.asarray(mesh_triangles,dtype=int)\n    else:\n        nodes,tris=structured_tri_mesh(float(width_m),float(height_m),max(2,int(nx)),max(2,int(ny)))
    model=make_material(material);inactive=set(inactive_elements or [])
    states=[model.initial_state() for _ in range(len(tris))]
    if initial_states:
        for i,s in enumerate(initial_states[:len(states)]):states[i]=_state_from_dict(s)
    u=np.asarray(initial_displacement,dtype=float).reshape(-1) if initial_displacement is not None else np.zeros(2*len(nodes))
    if len(u)!=2*len(nodes):raise ValueError("initial_displacement shape does not match mesh")
    history=[];yielded=np.zeros(len(tris),dtype=bool)
    base_nodes=np.where(np.isclose(nodes[:,1],0))[0]
    left=np.argmin(nodes[:,0]+1e3*np.abs(nodes[:,1]));fixed_x=[2*left]
    active=np.array([i not in inactive for i in range(len(tris))])

    for step in range(1,max(1,load_steps)+1):
        factor=step/max(1,load_steps);u_step=u.copy();committed=[s.copy() for s in states]
        converged=False
        for it in range(newton_max):
            K=np.zeros((len(u),len(u)));fint=np.zeros(len(u));fext=np.zeros(len(u));trial_states=[s.copy() for s in committed]
            for e,conn in enumerate(tris):
                if not active[e]:continue
                xy=nodes[conn];B,A=tri_B(xy);dofs=np.array([[2*n,2*n+1] for n in conn]).ravel()
                ue=u_step[dofs];deps=B@ue
                st,C,info=numerical_tangent(model,committed[e],deps)
                trial_states[e]=st;yielded[e]=st.yielded
                fint[dofs]+=B.T@st.stress*A;K[np.ix_(dofs,dofs)]+=B.T@C@B*A
                body_y=-density_kg_m3*gravity_m_s2/1000
                for n in conn:fext[2*n+1]+=factor*body_y*A/3
            top_nodes=np.where(np.isclose(nodes[:,1],height_m))[0]
            if top_pressure_kpa:
                order=top_nodes[np.argsort(nodes[top_nodes,0])]
                for a,b in zip(order[:-1],order[1:]):
                    L=np.linalg.norm(nodes[b]-nodes[a]);q=-factor*top_pressure_kpa
                    fext[2*a+1]+=q*L/2;fext[2*b+1]+=q*L/2
            for n in base_nodes:
                dof=2*n+1;gap=nodes[n,1]+u_step[dof]-contact_y_m
                if gap<0:
                    K[dof,dof]+=contact_penalty_kpa_m;fint[dof]+=contact_penalty_kpa_m*gap
            R=fext-fint;fixed=list(fixed_x)
            if it==0 and np.all(nodes[base_nodes,1]+u_step[2*base_nodes+1]>=contact_y_m):fixed.append(2*base_nodes[0]+1)
            free=np.setdiff1d(np.arange(len(u)),np.array(fixed,dtype=int))
            norm=float(np.linalg.norm(R[free]));scale=max(1,float(np.linalg.norm(fext[free])))
            if norm<tolerance*scale:
                states=trial_states;u=u_step;converged=True
                history.append({"step":step,"newton_iterations":it,"residual":norm,"converged":True});break
            try:du=np.linalg.solve(K[np.ix_(free,free)],R[free])
            except np.linalg.LinAlgError:du=np.linalg.lstsq(K[np.ix_(free,free)]+np.eye(len(free))*1e-9,R[free],rcond=None)[0]
            alpha=1.0
            if np.linalg.norm(du)>max(width_m,height_m)*.1:alpha=min(alpha,max(width_m,height_m)*.1/max(np.linalg.norm(du),1e-12))
            u_step[free]+=alpha*du
        if not converged:
            states=trial_states;u=u_step;history.append({"step":step,"newton_iterations":newton_max,"residual":norm,"converged":False})

    plastic=[float(s.eq_plastic_shear) for s in states];indicators=np.asarray(plastic)
    marked=np.where(indicators>=np.quantile(indicators,1-min(max(refine_fraction,0),1)))[0].tolist() if len(indicators) and np.any(indicators>0) else []
    return {"nodes_m":nodes.tolist(),"triangles":tris.tolist(),"displacement_m":u.reshape(-1,2).tolist(),
      "max_displacement_m":float(np.max(np.linalg.norm(u.reshape(-1,2),axis=1))),"element_plastic_shear":plastic,
      "yielded_elements":np.where(yielded)[0].tolist(),"active_elements":np.where(active)[0].tolist(),
      "inactive_elements":np.where(~active)[0].tolist(),"refinement_candidates":marked,"element_states":[_state_dict(s) for s in states],
      "history":history,"material_model":material.get("model","mohr_coulomb"),
      "method":"incremental Newton-Raphson CST elastoplastic FEM with return mapping and unilateral penalty contact",
      "status":"solved" if all(h["converged"] for h in history) else "nonlinear_iteration_warning"}

def staged_excavation(base:dict,stages:list[dict])->dict:
    results=[];inactive=set(base.get("inactive_elements",[]));prev=None
    for i,stage in enumerate(stages,1):
        inactive.update(stage.get("deactivate_elements",[]));inactive.difference_update(stage.get("activate_elements",[]))
        kwargs={**base,**stage};kwargs["inactive_elements"]=sorted(inactive);kwargs.pop("deactivate_elements",None);kwargs.pop("activate_elements",None);kwargs.pop("name",None)
        if prev is not None:
            kwargs["initial_displacement"]=prev["displacement_m"];kwargs["initial_states"]=prev["element_states"]
        out=solve_elastoplastic_2d(**kwargs);results.append({"stage":i,"name":stage.get("name",f"stage-{i}"),"result":out});prev=out
    return {"stages":results,"method":"staged activation/deactivation FEM with stress/plastic-history transfer"}

def adaptive_refine_plan(result:dict,max_fraction:float=.2)->dict:
    plastic=np.asarray(result.get("element_plastic_shear",[]),dtype=float)
    tris=np.asarray(result.get("triangles",[]),dtype=int);nodes=np.asarray(result.get("nodes_m",[]),dtype=float)
    if not len(plastic) or not np.any(plastic>0):return {"marked_elements":[],"reason":"no plasticity indicator"}
    gradients=np.zeros(len(tris));cent=np.array([nodes[t].mean(axis=0) for t in tris])
    for i in range(len(tris)):
        d=np.linalg.norm(cent-cent[i],axis=1);idx=np.argsort(d)[1:min(7,len(tris))]
        if len(idx):gradients[i]=max(abs(plastic[i]-plastic[idx]))/(max(d[idx].min(),1e-9))
    indicator=plastic+gradients/max(gradients.max(),1e-12)*max(plastic.max(),1e-12)
    n=max(1,int(math.ceil(len(tris)*max_fraction)));marked=np.argsort(indicator)[-n:].tolist()
    return {"marked_elements":marked,"indicator":indicator.tolist(),"criterion":"plastic strain + local gradient","refine_fraction":max_fraction}

def refine_marked_mesh(nodes:list[list[float]],triangles:list[list[int]],marked_elements:list[int])->dict:
    pts=[list(map(float,p)) for p in nodes];out=[];marked=set(map(int,marked_elements));parent=[]
    for i,t in enumerate(triangles):
        a,b,c=map(int,t)
        if i not in marked:
            out.append([a,b,c]);parent.append(i);continue
        centroid=((np.asarray(pts[a])+np.asarray(pts[b])+np.asarray(pts[c]))/3).tolist();m=len(pts);pts.append(centroid)
        out.extend([[a,b,m],[b,c,m],[c,a,m]]);parent.extend([i,i,i])
    return {"nodes_m":pts,"triangles":out,"parent_element":parent,"refined_elements":sorted(marked),"method":"local centroid triangle refinement"}

def adaptive_mesh_cycle(result:dict,max_fraction:float=.2)->dict:
    plan=adaptive_refine_plan(result,max_fraction)
    return {**plan,"refined_mesh":refine_marked_mesh(result.get("nodes_m",[]),result.get("triangles",[]),plan.get("marked_elements",[]))}


def solve_adaptive_elastoplastic(base:dict,cycles:int=2,refine_fraction:float=.2)->dict:
    results=[];current=dict(base);prev=None
    for cycle in range(max(1,int(cycles))):
        if prev is not None:
            current["mesh_nodes_m"]=prev["refined_mesh"]["nodes_m"];current["mesh_triangles"]=prev["refined_mesh"]["triangles"]
            old_u=np.asarray(results[-1]["result"]["displacement_m"],dtype=float);old_states=results[-1]["result"]["element_states"]
            parent=prev["refined_mesh"]["parent_element"];old_nodes=np.asarray(results[-1]["result"]["nodes_m"],dtype=float)
            new_nodes=np.asarray(prev["refined_mesh"]["nodes_m"],dtype=float)
            new_u=[]
            for p in new_nodes:
                d=np.linalg.norm(old_nodes-p,axis=1);i=int(np.argmin(d))
                if d[i]<1e-10:new_u.append(old_u[i].tolist())
                else:
                    tri_idx=int(parent[min(len(parent)-1,len(new_u)%len(parent))]);tri=np.asarray(results[-1]["result"]["triangles"][tri_idx],dtype=int)
                    new_u.append(old_u[tri].mean(axis=0).tolist())
            current["initial_displacement"]=new_u
            current["initial_states"]=[old_states[int(pi)] for pi in parent]
            current["inactive_elements"]=[]
        out=solve_elastoplastic_2d(**current)
        plan=adaptive_mesh_cycle(out,refine_fraction)
        results.append({"cycle":cycle+1,"result":out,"refinement":plan})
        if not plan.get("marked_elements"):break
        prev=plan
    return {"cycles":results,"status":"solved","method":"automatic solve-estimate-refine-project-resolve elastoplastic FEM"}
