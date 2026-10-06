from __future__ import annotations
from dataclasses import dataclass
import math,numpy as np

@dataclass
class State3D:
    stress:np.ndarray
    plastic_strain:np.ndarray
    eqp:float=0.0
    hardening:float=0.0
    backstress:np.ndarray|None=None
    fabric:np.ndarray|None=None
    pore_pressure_ratio:float=0.0
    def copy(self):return State3D(self.stress.copy(),self.plastic_strain.copy(),self.eqp,self.hardening,
        None if self.backstress is None else self.backstress.copy(),None if self.fabric is None else self.fabric.copy(),self.pore_pressure_ratio)

def invariants(stress):
    s=np.asarray(stress,float);mean=-(s[0]+s[1]+s[2])/3
    dev=np.array([s[0]+mean,s[1]+mean,s[2]+mean,s[3],s[4],s[5]])
    j2=.5*(dev[0]**2+dev[1]**2+dev[2]**2)+dev[3]**2+dev[4]**2+dev[5]**2
    q=math.sqrt(max(3*j2,0));return mean,q,dev

class AnisotropicCriticalState:
    def __init__(self,E_kpa=50000,nu=.3,M=1.2,lambda_c=.12,kappa=.02,pc0_kpa=100,anisotropy=0.2):
        from mesh3d import elastic_D3
        self.D=elastic_D3(E_kpa,nu);self.M=M;self.lam=lambda_c;self.kap=kappa;self.pc0=pc0_kpa;self.aniso=anisotropy
    def initial(self):return State3D(np.zeros(6),np.zeros(6),backstress=np.zeros(6))
    def integrate(self,state,deps):
        trial=state.stress+self.D@deps;p,q,dev=invariants(trial);pc=self.pc0*math.exp(max(state.hardening,0))
        a=state.backstress if state.backstress is not None else np.zeros(6)
        adev=dev-a;qa=math.sqrt(max(1.5*(adev[0]**2+adev[1]**2+adev[2]**2)+3*(adev[3]**2+adev[4]**2+adev[5]**2),0))
        f=qa*qa+self.M*self.M*p*(p-pc)
        if f<=1e-8:
            ns=state.copy();ns.stress=trial;return ns,self.D,{"yield":f,"branch":"elastic"}
        scale=max(0,min(1,(self.M*max(p,1e-6))/max(qa,1e-6)))
        returned=trial.copy();returned[:3]=-p+scale*dev[:3];returned[3:]=scale*dev[3:]
        dep=np.linalg.solve(self.D,trial-returned);ns=state.copy();ns.stress=returned;ns.plastic_strain+=dep
        ns.eqp+=float(np.linalg.norm(dep));ns.hardening+=max(-(dep[0]+dep[1]+dep[2]),0)/(max(self.lam-self.kap,1e-6))
        ns.backstress=a+self.aniso*(dev-a)*min(ns.eqp,1.0)
        return ns,self.D,{"yield":0.0,"branch":"anisotropic_critical_state","pc_kpa":pc}

class LiquefactionSandStyle:
    """Research cyclic effective-stress sand model inspired by PM4Sand/UBCSAND concepts, not an exact implementation."""
    def __init__(self,Dr=.5,G0=500,hpo=.5,density=1.8,phic_deg=33,contraction=.5,dilation=.2,fabric_rate=2.0):
        from mesh3d import elastic_D3
        self.Dr=Dr;self.G0=G0;self.hpo=hpo;self.density=density;self.phic=math.radians(phic_deg);self.contraction=contraction;self.dilation=dilation;self.fabric_rate=fabric_rate
    def initial(self):return State3D(np.zeros(6),np.zeros(6),backstress=np.zeros(6),fabric=np.zeros(6))
    def integrate(self,state,deps,effective_mean_kpa=100):
        p=max(effective_mean_kpa,1.0);G=self.G0*math.sqrt(p/101.3);E=2*G*(1+.3)
        from mesh3d import elastic_D3
        D=elastic_D3(E,.3);trial=state.stress+D@deps;pm,q,dev=invariants(trial)
        eta=q/max(pm,1e-6);eta_cs=6*math.sin(self.phic)/(3-math.sin(self.phic))
        fabric=state.fabric if state.fabric is not None else np.zeros(6);alpha=state.backstress if state.backstress is not None else np.zeros(6)
        f=eta-eta_cs*(.65+.35*self.Dr)
        ns=state.copy()
        if f<=0:
            ns.stress=trial;return ns,D,{"branch":"elastic","ru":ns.pore_pressure_ratio}
        dl=f/max(G*(1+self.hpo),1e-9);contract=self.contraction*(1-self.Dr)*dl;dilate=self.dilation*self.Dr*max(eta-.8*eta_cs,0)*dl
        volumetric=contract-dilate
        ns.pore_pressure_ratio=max(0,min(.999,state.pore_pressure_ratio+volumetric))
        scale=max(.02,1-dl);ns.stress=trial*scale;ns.eqp+=abs(dl)
        ns.fabric=fabric+self.fabric_rate*dl*(dev/(np.linalg.norm(dev)+1e-12)-fabric)
        ns.backstress=alpha+dl*(dev-alpha)
        ns.plastic_strain+=np.sign(deps)*abs(dl)/6
        return ns,D,{"branch":"cyclic_sand_plastic","ru":ns.pore_pressure_ratio,"eta":eta,"fabric_norm":float(np.linalg.norm(ns.fabric))}
