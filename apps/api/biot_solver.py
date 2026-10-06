from __future__ import annotations
import numpy as np,math

def solve_biot_1d(height_m:float,n:int,young_pa:float,poisson:float,permeability_m_s:float,fluid_unit_weight_n_m3:float,
                  biot_alpha:float,storage_1_pa:float,load_pa:float,dt_s:float,steps:int,drained_top:bool=True)->dict:
    """Monolithic 1D u-p Biot consolidation FE with linear two-node elements."""
    n=max(3,int(n));x=np.linspace(0,height_m,n);ne=n-1;nd=2*n
    constrained_u=[0];constrained_p=[2*(n-1)+1] if drained_top else []
    u=np.zeros(n);p=np.zeros(n);series=[]
    # drained constrained modulus for 1D strain
    M=young_pa*(1-poisson)/((1+poisson)*(1-2*poisson))
    kappa=permeability_m_s/fluid_unit_weight_n_m3
    for step in range(steps):
        K=np.zeros((nd,nd));rhs=np.zeros(nd)
        for e in range(ne):
            nodes=[e,e+1];le=x[e+1]-x[e]
            B=np.array([-1/le,1/le]);Ke=M*np.outer(B,B)*le
            H=kappa*np.outer(B,B)*le
            Nmass=le/6*np.array([[2,1],[1,2]],dtype=float)
            Q=biot_alpha*np.outer(B,np.array([.5,.5]))*le
            S=storage_1_pa*Nmass
            iu=[2*j for j in nodes];ip=[2*j+1 for j in nodes]
            for a in range(2):
                for b in range(2):
                    K[iu[a],iu[b]]+=Ke[a,b]
                    K[iu[a],ip[b]]-=Q[a,b]
                    K[ip[a],iu[b]]+=Q[b,a]/dt_s
                    K[ip[a],ip[b]]+=S[a,b]/dt_s+H[a,b]
                    rhs[ip[a]]+=(S[a,b]/dt_s)*p[nodes[b]]+(Q[b,a]/dt_s)*u[nodes[b]]
        rhs[2*(n-1)]-=load_pa
        constraints=[2*i for i in constrained_u]+constrained_p
        free=np.setdiff1d(np.arange(nd),constraints)
        sol=np.zeros(nd);sol[free]=np.linalg.solve(K[np.ix_(free,free)],rhs[free])
        u=sol[0::2];p=sol[1::2]
        series.append({"time_s":(step+1)*dt_s,"top_settlement_m":float(-u[-1]),"max_pore_pressure_pa":float(p.max())})
    return {"z_m":x.tolist(),"displacement_m":u.tolist(),"pore_pressure_pa":p.tolist(),"series":series,
      "method":"monolithic 1D Biot u-p finite element, backward Euler","assumptions":["small strain","linear poroelastic skeleton","constant permeability"]}
