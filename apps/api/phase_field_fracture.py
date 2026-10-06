from __future__ import annotations
import numpy as np
from elastoplastic_fem import structured_tri_mesh,tri_B
from mesh3d import elastic_D3
from solver_backend import coo_from_triplets,solve_sparse

def solve_phase_field_2d(width_m:float,height_m:float,nx:int,ny:int,E_kpa:float,nu:float,Gc_kpa_m:float,length_scale_m:float,
                         top_displacement_m:float,steps:int=10,kappa:float=1e-8)->dict:
    """AT2 staggered phase-field fracture baseline with linear elasticity."""
    nodes,tris=structured_tri_mesh(width_m,height_m,max(2,nx),max(2,ny));nn=len(nodes);u=np.zeros((nn,2));d=np.zeros(nn);H=np.zeros(len(tris))
    lam=E_kpa*nu/((1+nu)*(1-2*nu));mu=E_kpa/(2*(1+nu));D=np.array([[lam+2*mu,lam,0],[lam,lam+2*mu,0],[0,0,mu]],float)
    bottom=np.where(np.isclose(nodes[:,1],0))[0];top=np.where(np.isclose(nodes[:,1],height_m))[0];left=np.argmin(nodes[:,0]+1000*np.abs(nodes[:,1]))
    history=[]
    for step in range(1,steps+1):
        target=top_displacement_m*step/steps
        # staggered fixed-point
        for stag in range(20):
            rows=[];cols=[];data=[];rhs=np.zeros(2*nn)
            for e,conn in enumerate(tris):
                B,A=tri_B(nodes[conn]);de=float(np.mean(d[conn]));g=(1-de)**2+kappa;Ke=g*(B.T@D@B)*A;dofs=np.array([[2*n,2*n+1] for n in conn]).ravel()
                for a,I in enumerate(dofs):
                    for b,J in enumerate(dofs):rows.append(I);cols.append(J);data.append(Ke[a,b])
            K=coo_from_triplets(rows,cols,data,(2*nn,2*nn)).tolil();fixed={2*left:0.0}
            for n in bottom:fixed[2*n+1]=0.0
            for n in top:fixed[2*n+1]=target
            allidx=np.arange(2*nn);fd=np.array(sorted(fixed),int);fv=np.array([fixed[i] for i in fd])
            free=np.setdiff1d(allidx,fd);rhsf=rhs[free]-K[np.ix_(free,fd)]@fv;sol=np.zeros(2*nn);sol[fd]=fv
            if len(free):sol[free]=solve_sparse(K.tocsr()[np.ix_(free,free)],rhsf,method="spsolve")[0]
            un=sol.reshape(nn,2)
            # history energy and phase field
            prow=[];pcol=[];pdata=[];prhs=np.zeros(nn)
            for e,conn in enumerate(tris):
                B,A=tri_B(nodes[conn]);eps=B@un[conn].reshape(-1);psi=.5*float(eps@(D@eps));H[e]=max(H[e],psi)
                grad=np.array([[B[0,0],B[0,2],B[0,4]],[B[1,1],B[1,3],B[1,5]]]);N=np.full(3,1/3)
                Kd=Gc_kpa_m*length_scale_m*(grad.T@grad)*A+(Gc_kpa_m/length_scale_m+2*H[e])*np.outer(N,N)*A
                fdmg=2*H[e]*N*A
                for a,I in enumerate(conn):
                    prhs[I]+=fdmg[a]
                    for b,J in enumerate(conn):prow.append(I);pcol.append(J);pdata.append(Kd[a,b])
            Kd=coo_from_triplets(prow,pcol,pdata,(nn,nn));dn=solve_sparse(Kd,prhs,method="spsolve")[0];dn=np.clip(np.maximum(d,dn),0,1)
            err=max(float(np.max(np.abs(un-u))),float(np.max(np.abs(dn-d))));u,d=un,dn
            if err<1e-7:break
        history.append({"step":step,"load_displacement_m":target,"max_damage":float(d.max()),"iterations":stag+1})
    return {"nodes_m":nodes.tolist(),"triangles":tris.tolist(),"displacement_m":u.tolist(),"phase_field":d.tolist(),"history":history,"method":"AT2 staggered phase-field fracture"}

def xfem_heaviside_enrichment(nodes,crack_point,crack_normal):
    x=np.asarray(nodes,float);p=np.asarray(crack_point,float);n=np.asarray(crack_normal,float);n=n/max(np.linalg.norm(n),1e-12)
    phi=(x-p)@n;H=np.where(phi>=0,1.0,-1.0)
    enriched=np.where(np.abs(phi)<np.percentile(np.abs(phi),50) if len(phi)>2 else np.ones_like(phi,dtype=bool))[0]
    return {"level_set":phi.tolist(),"heaviside":H.tolist(),"enriched_nodes":enriched.tolist(),"method":"XFEM Heaviside crack enrichment map"}
