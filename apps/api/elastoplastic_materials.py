from __future__ import annotations
from dataclasses import dataclass,asdict
import math,numpy as np

@dataclass
class MaterialState:
    stress: np.ndarray
    plastic_strain: np.ndarray
    eq_plastic_shear: float=0.0
    plastic_volumetric: float=0.0
    pc_kpa: float=100.0
    yielded: bool=False
    def copy(self): return MaterialState(self.stress.copy(),self.plastic_strain.copy(),self.eq_plastic_shear,self.plastic_volumetric,self.pc_kpa,self.yielded)

def elastic_matrix(E_kpa:float,nu:float)->np.ndarray:
    lam=E_kpa*nu/((1+nu)*(1-2*nu));mu=E_kpa/(2*(1+nu))
    return np.array([[lam+2*mu,lam,0],[lam,lam+2*mu,0],[0,0,mu]],dtype=float)

def principal_2d(stress:np.ndarray)->tuple[float,float,float]:
    sx,sy,txy=map(float,stress)
    mean=.5*(sx+sy);rad=math.sqrt((.5*(sx-sy))**2+txy*txy)
    return mean+rad,mean-rad,mean

def invariants_plane(stress:np.ndarray)->tuple[float,float]:
    # Tensor stresses use the mechanics convention (tension positive).
    # Geotechnical p-q invariants below use compression positive.
    smax,smin,_=principal_2d(stress)
    sigma1_c=-smin;sigma3_c=-smax
    p=.5*(sigma1_c+sigma3_c);q=max(sigma1_c-sigma3_c,0.0)
    return p,q

class MohrCoulomb:
    """Plane-strain engineering Mohr-Coulomb integrator.

    Uses an elastic predictor and non-associated closest correction in p-q space.
    It preserves an exact MC shear envelope q = M_phi p + k_phi in triaxial-style
    compression convention while using dilation angle psi for plastic flow.
    """
    def __init__(self,E_kpa:float,nu:float,cohesion_kpa:float,friction_deg:float,dilation_deg:float=0,tensile_cutoff_kpa:float=0):
        self.E=E_kpa;self.nu=nu;self.c=cohesion_kpa;self.phi=math.radians(friction_deg);self.psi=math.radians(dilation_deg);self.tension=tensile_cutoff_kpa
        self.D=elastic_matrix(E_kpa,nu);self.G=E_kpa/(2*(1+nu));self.K=E_kpa/(3*(1-2*nu))
        self.M=2*math.sin(self.phi)/(1-math.sin(self.phi)+1e-12);self.k=2*self.c*math.cos(self.phi)/(1-math.sin(self.phi)+1e-12)
        self.Mpsi=2*math.sin(self.psi)/(1-math.sin(self.psi)+1e-12)

    def initial_state(self)->MaterialState:return MaterialState(np.zeros(3),np.zeros(3))

    def yield_value(self,stress:np.ndarray)->float:
        p,q=invariants_plane(stress);return q-self.M*p-self.k

    def integrate(self,state:MaterialState,deps:np.ndarray)->tuple[MaterialState,np.ndarray,dict]:
        trial=state.stress+self.D@deps
        p,q=invariants_plane(trial);f=q-self.M*p-self.k
        if f<=1e-9:
            ns=state.copy();ns.stress=trial;ns.yielded=False
            return ns,self.D,{"yield_value":f,"plastic_multiplier":0.0,"branch":"elastic"}
        # Return in p-q using plastic potential g=q-Mpsi*p.
        denom=3*self.G+self.K*self.M*self.Mpsi
        dl=max(f/max(denom,1e-12),0.0)
        p_new=p+self.K*self.Mpsi*dl
        q_new=max(0.0,q-3*self.G*dl)
        # Preserve trial principal directions and reconstruct 2D tensor.
        sx,sy,txy=trial;theta=.5*math.atan2(2*txy,sx-sy)
        sigma1_c=p_new+.5*q_new;sigma3_c=p_new-.5*q_new
        smax=-sigma3_c;smin=-sigma1_c
        ct,st=math.cos(theta),math.sin(theta)
        returned=np.array([smax*ct*ct+smin*st*st,smax*st*st+smin*ct*ct,(smax-smin)*st*ct])
        dep_p=np.linalg.solve(self.D,trial-returned)
        ns=state.copy();ns.stress=returned;ns.plastic_strain=state.plastic_strain+dep_p
        ns.eq_plastic_shear=state.eq_plastic_shear+math.sqrt(max(2/3*np.dot(dep_p,dep_p),0));ns.plastic_volumetric=state.plastic_volumetric+dep_p[0]+dep_p[1];ns.yielded=True
        # Algorithmic tangent: numerical local derivative of return map is used by global solver.
        return ns,self.D,{"yield_value":self.yield_value(returned),"plastic_multiplier":dl,"branch":"mohr_coulomb_shear"}

class HardeningSoil:
    """Multi-surface Hardening-Soil formulation for GeoTect.

    Implements stress-dependent E50/Eur/Eoed, hyperbolic shear hardening,
    non-associated shear flow, and isotropic volumetric cap hardening.
    This follows the classical HS concepts, but validation against a target
    implementation remains mandatory because commercial implementations differ
    in details of initial stress, tension cutoff and surface smoothing.
    """
    def __init__(self,E50_ref_kpa:float,Eoed_ref_kpa:float,Eur_ref_kpa:float,nu_ur:float,
                 cohesion_kpa:float,friction_deg:float,dilation_deg:float=0,m:float=.5,p_ref_kpa:float=100,
                 Rf:float=.9,pc0_kpa:float=100,cap_M:float=1.2):
        self.E50r=E50_ref_kpa;self.Eoedr=Eoed_ref_kpa;self.Eurr=Eur_ref_kpa;self.nu=nu_ur;self.c=cohesion_kpa
        self.phi=math.radians(friction_deg);self.psi=math.radians(dilation_deg);self.m=m;self.pref=p_ref_kpa;self.Rf=Rf;self.pc0=pc0_kpa;self.capM=cap_M
        self.M=2*math.sin(self.phi)/(1-math.sin(self.phi)+1e-12);self.k=2*self.c*math.cos(self.phi)/(1-math.sin(self.phi)+1e-12);self.Mpsi=2*math.sin(self.psi)/(1-math.sin(self.psi)+1e-12)

    def stiffness(self,p_kpa:float,unloading:bool=False,oedometer:bool=False)->float:
        base=self.Eurr if unloading else self.Eoedr if oedometer else self.E50r
        effective=max(p_kpa+self.c/math.tan(self.phi) if abs(math.tan(self.phi))>1e-12 else p_kpa,self.pref*.01)
        ref=max(self.pref+self.c/math.tan(self.phi) if abs(math.tan(self.phi))>1e-12 else self.pref,1e-9)
        return base*(effective/ref)**self.m

    def initial_state(self)->MaterialState:return MaterialState(np.zeros(3),np.zeros(3),pc_kpa=self.pc0)

    def surfaces(self,stress:np.ndarray,state:MaterialState)->tuple[float,float]:
        p,q=invariants_plane(stress)
        qf=max(self.M*p+self.k,1e-6)
        # Hyperbolic shear hardening: plastic shear expands the mobilized surface toward qf.
        mobilization=1-math.exp(-max(state.eq_plastic_shear,0)*self.E50r/max(qf,1e-6))
        qy=max(.05*qf,min(self.Rf*qf,qf*max(mobilization,.05)))
        fs=q-qy
        # Elliptical compression cap in p-q space.
        pc=max(state.pc_kpa,1e-6);fc=(q/max(self.capM,1e-6))**2+p*(p-pc)
        return fs,fc

    def integrate(self,state:MaterialState,deps:np.ndarray)->tuple[MaterialState,np.ndarray,dict]:
        p0,_=invariants_plane(state.stress);E=self.stiffness(max(p0,1.0));D=elastic_matrix(E,self.nu);trial=state.stress+D@deps
        fs,fc=self.surfaces(trial,state)
        if fs<=1e-8 and fc<=1e-8:
            ns=state.copy();ns.stress=trial;ns.yielded=False;return ns,D,{"branch":"elastic","fs":fs,"fc":fc,"E_kpa":E}
        ns=state.copy();stress=trial.copy();dep_p=np.zeros(3);branch=[]
        # Shear-surface return, iterated because surface expands with shear strain.
        if fs>0:
            for _ in range(20):
                p,q=invariants_plane(stress);qf=max(self.M*p+self.k,1e-6)
                mob=1-math.exp(-max(ns.eq_plastic_shear,0)*self.E50r/qf);qy=max(.05*qf,min(self.Rf*qf,qf*max(mob,.05)))
                f=q-qy
                if abs(f)<1e-6:break
                G=E/(2*(1+self.nu));K=E/(3*(1-2*self.nu));dl=max(f/(3*G+K*self.M*self.Mpsi+self.E50r*.1),0)
                p2=p+K*self.Mpsi*dl;q2=max(q-3*G*dl,0)
                sx,sy,txy=stress;th=.5*math.atan2(2*txy,sx-sy);ct,st=math.cos(th),math.sin(th)
                sigma1_c=p2+.5*q2;sigma3_c=p2-.5*q2;smax=-sigma3_c;smin=-sigma1_c
                corrected=np.array([smax*ct*ct+smin*st*st,smax*st*st+smin*ct*ct,(smax-smin)*st*ct])
                inc=np.linalg.solve(D,stress-corrected);dep_p+=inc;stress=corrected
                ns.eq_plastic_shear+=math.sqrt(max(2/3*np.dot(inc,inc),0))
            branch.append("shear")
        # Cap return by radial scaling q and clamping p to current/expanded cap.
        p,q=invariants_plane(stress);_,fc2=self.surfaces(stress,ns)
        if fc2>0:
            pc=max(ns.pc_kpa,1e-6)
            # Solve q^2/M^2 + p(p-pc)=0 for a radial scale alpha.
            A=(q/max(self.capM,1e-6))**2+p*p;B=-p*pc
            alpha=max(0,min(1,-B/max(A,1e-12)))
            p2=alpha*p;q2=alpha*q
            sx,sy,txy=stress;th=.5*math.atan2(2*txy,sx-sy);ct,st=math.cos(th),math.sin(th)
            sigma1_c=p2+.5*q2;sigma3_c=p2-.5*q2;smax=-sigma3_c;smin=-sigma1_c
            corrected=np.array([smax*ct*ct+smin*st*st,smax*st*st+smin*ct*ct,(smax-smin)*st*ct])
            inc=np.linalg.solve(D,stress-corrected);dep_p+=inc;stress=corrected
            deps_v=max(-(inc[0]+inc[1]),0);ns.plastic_volumetric+=inc[0]+inc[1]
            ns.pc_kpa=pc*math.exp(deps_v*max(self.Eoedr/max(pc,1e-6),1e-6))
            branch.append("cap")
        ns.stress=stress;ns.plastic_strain=state.plastic_strain+dep_p;ns.yielded=True
        fs3,fc3=self.surfaces(stress,ns)
        return ns,D,{"branch":"+".join(branch),"fs":fs3,"fc":fc3,"E_kpa":E,"pc_kpa":ns.pc_kpa}

def numerical_tangent(model,state:MaterialState,deps:np.ndarray,h:float=1e-7)->tuple[MaterialState,np.ndarray,dict]:
    base,_,info=model.integrate(state,deps);C=np.zeros((3,3))
    scale=max(float(np.linalg.norm(deps)),1.0)
    eps=h*scale
    for j in range(3):
        dd=deps.copy();dd[j]+=eps
        s2,_,_=model.integrate(state,dd);C[:,j]=(s2.stress-base.stress)/eps
    C=.5*(C+C.T)
    # stabilise near corners while preserving positive diagonal floor
    for i in range(3):C[i,i]=max(C[i,i],1e-6)
    return base,C,info
