from __future__ import annotations
import numpy as np,math
from elastoplastic_fem import structured_tri_mesh,tri_B,make_material
from elastoplastic_materials import numerical_tangent
from large_deformation import updated_coordinates,geometric_stiffness_scalar
from solver_backend import coo_from_triplets,solve_sparse

def solve_updated_lagrangian_2d(width_m:float,height_m:float,nx:int,ny:int,material:dict,
                                top_pressure_kpa:float,density_kg_m3:float=0,load_steps:int=10,
                                newton_max:int=25,tolerance:float=1e-6,linear_method:str="auto",backend:str="auto")->dict:
    nodes0,tris=structured_tri_mesh(width_m,height_m,max(2,nx),max(2,ny));nn=len(nodes0);u=np.zeros((nn,2))
    model=make_material(material);states=[model.initial_state() for _ in tris];history=[]
    bottom=np.where(np.isclose(nodes0[:,1],0))[0];fixed=[2*i+1 for i in bottom]+[2*int(bottom[0])]
    for step in range(1,max(1,load_steps)+1):
        lf=step/load_steps;u_step=u.copy();committed=[s.copy() for s in states];conv=False
        for it in range(newton_max):
            nodes=updated_coordinates(nodes0,u_step);rows=[];cols=[];data=[];R=np.zeros(2*nn);trial=[s.copy() for s in committed]
            for e,conn in enumerate(tris):
                xy=nodes[conn];B,A=tri_B(xy);dofs=np.array([[2*n,2*n+1] for n in conn]).ravel()
                deps=B@(u_step[conn].reshape(-1)-u[conn].reshape(-1))
                st,C,_=numerical_tangent(model,committed[e],deps);trial[e]=st
                Kmat=B.T@C@B*A
                sig=np.array([[st.stress[0],st.stress[2]],[st.stress[2],st.stress[1]]])
                grad=np.array([[B[0,0],B[1,1]],[B[0,2],B[1,3]],[B[0,4],B[1,5]]])
                Kgeo=geometric_stiffness_scalar(grad,sig,A)
                fint=B.T@st.stress*A
                R[dofs]+=fint
                body=-density_kg_m3*9.81/1000
                for n in conn:R[2*n+1]-=lf*body*A/3
                K=Kmat+Kgeo
                for a,I in enumerate(dofs):
                    for b,J in enumerate(dofs):rows.append(I);cols.append(J);data.append(K[a,b])
            top=np.where(np.isclose(nodes0[:,1],height_m))[0];order=top[np.argsort(nodes0[top,0])]
            for a,b in zip(order[:-1],order[1:]):
                L=float(np.linalg.norm(nodes[b]-nodes[a]));q=-lf*top_pressure_kpa
                R[2*a+1]-=q*L/2;R[2*b+1]-=q*L/2
            K=coo_from_triplets(rows,cols,data,(2*nn,2*nn))
            free=np.setdiff1d(np.arange(2*nn),np.array(fixed,int));nr=float(np.linalg.norm(R[free]))
            if nr<tolerance*max(1,float(np.linalg.norm(u_step))):
                conv=True;states=trial;u=u_step;break
            du,info=solve_sparse(K[np.ix_(free,free)],-R[free],method=linear_method,backend=backend,tol=min(1e-8,tolerance*.1))
            u_step.reshape(-1)[free]+=du
        if not conv:states=trial;u=u_step
        history.append({"step":step,"converged":conv,"iterations":it+1,"residual":nr,"max_displacement_m":float(np.linalg.norm(u,axis=1).max())})
    return {"nodes_initial_m":nodes0.tolist(),"nodes_current_m":updated_coordinates(nodes0,u).tolist(),"triangles":tris.tolist(),"displacement_m":u.tolist(),
      "history":history,"status":"solved" if all(x["converged"] for x in history) else "nonlinear_iteration_warning",
      "method":"updated-Lagrangian elastoplastic triangular FEM with material + geometric tangent"}
