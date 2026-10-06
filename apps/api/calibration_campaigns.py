from __future__ import annotations
import numpy as np
from scipy.optimize import differential_evolution,least_squares
from materials3d import LiquefactionSandStyle

def simulate_liquefaction(params,strain_history,effective_mean_kpa=100):
    m=LiquefactionSandStyle(**params);s=m.initial();stress=[];ru=[]
    for de in strain_history:
        s,_,_=m.integrate(s,np.asarray(de,float),effective_mean_kpa)
        stress.append(s.stress.tolist());ru.append(s.pore_pressure_ratio)
    return {"stress":stress,"ru":ru}

def calibrate_liquefaction_style(strain_history,observed_ru,fixed=None,bounds=None,seed=42,maxiter=50):
    fixed=fixed or {}
    bounds=bounds or {"Dr":(.2,.9),"G0":(200,900),"hpo":(.1,1.5),"contraction":(.05,2.0),"dilation":(.01,1.0),"fabric_rate":(.2,5.0)}
    names=list(bounds);bb=[tuple(bounds[n]) for n in names];obs=np.asarray(observed_ru,float)
    def objective(x):
        p={**fixed,**dict(zip(names,map(float,x)))};sim=np.asarray(simulate_liquefaction(p,strain_history)["ru"],float)
        n=min(len(sim),len(obs));return float(np.sqrt(np.mean((sim[:n]-obs[:n])**2)))
    res=differential_evolution(objective,bb,seed=seed,maxiter=maxiter,polish=True)
    best={**fixed,**dict(zip(names,map(float,res.x)))}
    return {"parameters":best,"objective_rmse":float(res.fun),"success":bool(res.success),"message":str(res.message),"simulated":simulate_liquefaction(best,strain_history)}

def calibrate_curve(model_fn,parameter_names,bounds,observed):
    obs=np.asarray(observed,float);lo=np.array([bounds[n][0] for n in parameter_names]);hi=np.array([bounds[n][1] for n in parameter_names]);x0=(lo+hi)/2
    def residual(x):
        y=np.asarray(model_fn(dict(zip(parameter_names,x))),float);n=min(len(y),len(obs));return y[:n]-obs[:n]
    res=least_squares(residual,x0,bounds=(lo,hi))
    return {"parameters":dict(zip(parameter_names,map(float,res.x))),"rmse":float(np.sqrt(np.mean(res.fun**2))),"success":bool(res.success),"nfev":int(res.nfev)}
