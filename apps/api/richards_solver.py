from __future__ import annotations
import numpy as np,math

def van_genuchten(h_m:np.ndarray,theta_r:float,theta_s:float,alpha_1_m:float,n:float,ks_m_s:float,l:float=.5):
    m=1-1/n;abs_h=np.abs(np.minimum(h_m,0));se=(1+(alpha_1_m*abs_h)**n)**(-m)
    theta=theta_r+(theta_s-theta_r)*se
    C=(theta_s-theta_r)*m*n*(alpha_1_m**n)*np.maximum(abs_h,1e-12)**(n-1)*(1+(alpha_1_m*abs_h)**n)**(-m-1)
    C=np.where(h_m<0,C,1e-8)
    kr=np.sqrt(se)*(1-(1-se**(1/m))**m)**2
    K=ks_m_s*np.where(h_m<0,kr,1.0)
    return theta,C,K

def solve_richards_1d(depth_m:float,nz:int,initial_head_m:float,theta_r:float,theta_s:float,alpha_1_m:float,n_vg:float,
                      ks_m_s:float,dt_s:float,steps:int,top_flux_m_s:float=0,bottom_head_m:float|None=None,
                      max_picard:int=50,tol:float=1e-6)->dict:
    """Mixed-form Richards equation, backward Euler + Picard finite volumes."""
    nz=max(3,int(nz));dz=depth_m/(nz-1);h=np.full(nz,float(initial_head_m));mass=[];history=[]
    theta0=van_genuchten(h,theta_r,theta_s,alpha_1_m,n_vg,ks_m_s)[0]
    for step in range(steps):
        hold=h.copy();theta_old=van_genuchten(hold,theta_r,theta_s,alpha_1_m,n_vg,ks_m_s)[0]
        converged=False
        for it in range(max_picard):
            theta,C,K=van_genuchten(h,theta_r,theta_s,alpha_1_m,n_vg,ks_m_s)
            Kf=2*K[:-1]*K[1:]/np.maximum(K[:-1]+K[1:],1e-20)
            A=np.zeros((nz,nz));b=np.zeros(nz)
            for i in range(1,nz-1):
                ku=Kf[i-1];kd=Kf[i]
                A[i,i-1]=-dt_s*ku/dz**2;A[i,i]=C[i]+dt_s*(ku+kd)/dz**2;A[i,i+1]=-dt_s*kd/dz**2
                gravity=dt_s*(kd-ku)/dz
                b[i]=C[i]*h[i]-(theta[i]-theta_old[i])-gravity
            # prescribed surface flux q positive downward: -K(dh/dz+1)=q
            A[0,0]=1;A[0,1]=-1;b[0]=dz*(-top_flux_m_s/max(Kf[0],1e-20)-1)
            if bottom_head_m is None:
                A[-1,-2]=-1;A[-1,-1]=1;b[-1]=0
            else:A[-1,-1]=1;b[-1]=bottom_head_m
            hn=np.linalg.solve(A,b)
            err=float(np.max(np.abs(hn-h)));h=.5*h+.5*hn
            if err<tol:converged=True;break
        theta_new=van_genuchten(h,theta_r,theta_s,alpha_1_m,n_vg,ks_m_s)[0]
        storage=float(np.sum(theta_new-theta_old)*dz);inflow=top_flux_m_s*dt_s
        mass.append({"step":step+1,"storage_change_m":storage,"surface_inflow_m":inflow,"residual_m":storage-inflow})
        history.append({"step":step+1,"picard_iterations":it+1,"converged":converged,"head_min_m":float(h.min()),"head_max_m":float(h.max())})
    return {"head_m":h.tolist(),"theta":theta_new.tolist(),"history":history,"mass_balance":mass,
      "method":"1D mixed-form Richards equation, backward Euler finite-volume/Picard","status":"solved" if all(x["converged"] for x in history) else "iteration_warning"}
