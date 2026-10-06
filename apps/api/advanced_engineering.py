from __future__ import annotations
import math, numpy as np

def mohr_coulomb_strength(normal_stress_kpa:float,cohesion_kpa:float,friction_deg:float,pore_pressure_kpa:float=0)->dict:
    eff=max(normal_stress_kpa-pore_pressure_kpa,0);tau=cohesion_kpa+eff*math.tan(math.radians(friction_deg))
    return {"effective_normal_stress_kpa":eff,"shear_strength_kpa":tau,"model":"Mohr-Coulomb"}

def hoek_brown_strength(sigma3_mpa:float,ucs_mpa:float,mb:float,s:float,a:float)->dict:
    sigma1=sigma3_mpa+ucs_mpa*max(mb*sigma3_mpa/max(ucs_mpa,1e-9)+s,0)**a
    return {"sigma1_failure_mpa":sigma1,"model":"Hoek-Brown"}

def hardening_soil_stiffness(stress_kpa:float,e50_ref_mpa:float,eur_ref_mpa:float,m:float=0.5,p_ref_kpa:float=100)->dict:
    ratio=max(stress_kpa,1e-6)/p_ref_kpa
    return {"E50_mpa":e50_ref_mpa*ratio**m,"Eur_mpa":eur_ref_mpa*ratio**m,"model":"Hardening-Soil stiffness scaling baseline"}

def modified_cam_clay_yield(p_kpa:float,q_kpa:float,pc_kpa:float,M:float)->dict:
    f=q_kpa*q_kpa+M*M*p_kpa*(p_kpa-pc_kpa)
    return {"yield_function":f,"yielded":f>=0,"model":"Modified Cam Clay yield check"}

def coupled_hydro_mechanical(total_stress_kpa:list[list[float]],pore_pressure_kpa:list[list[float]],biot_alpha:float=1.0)->dict:
    s=np.asarray(total_stress_kpa,dtype=float);u=np.asarray(pore_pressure_kpa,dtype=float)
    if s.shape!=u.shape:raise ValueError("stress and pore-pressure grids must match")
    eff=s-biot_alpha*u
    return {"effective_stress_kpa":eff.tolist(),"min":float(eff.min()),"max":float(eff.max()),"biot_alpha":biot_alpha,"method":"Biot effective stress coupling"}

def transient_diffusion(head0:list[list[float]],k_m_s:float,storage:float,dx_m:float,dy_m:float,dt_s:float,steps:int,left_head:float|None=None,right_head:float|None=None)->dict:
    h=np.asarray(head0,dtype=float).copy();alpha=k_m_s/max(storage,1e-12);rx=alpha*dt_s/dx_m**2;ry=alpha*dt_s/dy_m**2
    if rx+ry>.5:raise ValueError("Explicit scheme unstable: reduce dt or increase grid spacing")
    for _ in range(max(1,steps)):
        n=h.copy();n[1:-1,1:-1]=h[1:-1,1:-1]+rx*(h[1:-1,2:]-2*h[1:-1,1:-1]+h[1:-1,:-2])+ry*(h[2:,1:-1]-2*h[1:-1,1:-1]+h[:-2,1:-1])
        if left_head is not None:n[:,0]=left_head
        if right_head is not None:n[:,-1]=right_head
        n[0,:]=n[1,:];n[-1,:]=n[-2,:];h=n
    return {"head_m":h.tolist(),"steps":steps,"method":"explicit transient groundwater diffusion"}

def richards_bucket(theta:float,theta_sat:float,theta_res:float,rain_mm:float,et_mm:float,depth_m:float,drainage_coeff:float=.1)->dict:
    water=max(rain_mm-et_mm,0)/1000
    dtheta=water/max(depth_m,1e-9);theta_new=min(theta_sat,max(theta_res,theta+dtheta))
    drainage=max(theta_new-theta_res,0)*drainage_coeff;theta_new=max(theta_res,theta_new-drainage)
    saturation=(theta_new-theta_res)/max(theta_sat-theta_res,1e-9)
    return {"theta":theta_new,"saturation":saturation,"drainage_fraction":drainage,"method":"unsaturated bucket/Richards screening"}

def consolidation_time(settlement_final_mm:float,cv_m2_s:float,drainage_path_m:float,times_s:list[float])->dict:
    out=[]
    for t in times_s:
        tv=cv_m2_s*t/max(drainage_path_m**2,1e-12);u=min(1,2/math.sqrt(math.pi)*math.sqrt(max(tv,0))) if tv<.2 else min(1,1-math.exp(-math.pi**2*tv/4))
        out.append({"time_s":t,"degree_consolidation":u,"settlement_mm":settlement_final_mm*u})
    return {"series":out,"method":"1D Terzaghi consolidation approximation"}

def newmark_sliding(accel_g:list[float],dt_s:float,yield_accel_g:float)->dict:
    vel=disp=0.0;series=[]
    for a in accel_g:
        excess=abs(float(a))-yield_accel_g
        if excess>0:
            sign=1 if a>=0 else -1;vel+=sign*excess*9.81*dt_s;disp+=vel*dt_s
        series.append(disp)
    return {"permanent_displacement_m":abs(disp),"series_m":series,"method":"Newmark sliding-block integration"}

def stereonet_wedge_sets(discontinuity_sets:list[dict],slope_dip:float,slope_dip_direction:float,friction_deg:float)->dict:
    risks=[]
    for i,a in enumerate(discontinuity_sets):
        for j,b in enumerate(discontinuity_sets[i+1:],i+1):
            ddiff=abs((a["dip_direction"]-b["dip_direction"]+180)%360-180)
            dip=min(a["dip"],b["dip"])
            possible=dip>friction_deg and ddiff>20 and ddiff<160 and dip<slope_dip+20
            if possible:risks.append({"set_a":i,"set_b":j,"kinematically_possible":True,"screening_score":dip-friction_deg})
    return {"potential_wedges":risks,"method":"discontinuity-set kinematic screening"}

def rock_mass_classification(rqd:float,joint_spacing_m:float,gsi:float)->dict:
    rmr_proxy=min(100,max(0,.45*rqd+20*min(joint_spacing_m,2)/2+.35*gsi))
    q_proxy=max(.001,(rqd/100)*max(joint_spacing_m,.05)*max(gsi/50,.1))
    return {"RMR_proxy":rmr_proxy,"Q_proxy":q_proxy,"GSI":gsi,"method":"screening proxies; use full classification inputs for design"}

def convergence_confinement(radius_m:float,p0_mpa:float,support_pressure_mpa:float,young_mpa:float,poisson:float)->dict:
    closure=radius_m*(p0_mpa-support_pressure_mpa)*(1+poisson)/max(young_mpa,1e-9)
    return {"radial_closure_m":max(closure,0),"closure_mm":max(closure,0)*1000,"method":"elastic convergence-confinement baseline"}

def tailings_freeboard(crest_elev_m:float,pond_elev_m:float,wave_runup_m:float=0,rain_allowance_m:float=0)->dict:
    fb=crest_elev_m-pond_elev_m-wave_runup_m-rain_allowance_m
    return {"effective_freeboard_m":fb,"status":"critical" if fb<0 else "warning" if fb<1 else "normal"}

def inverse_velocity_failure(times:list[float],velocities:list[float])->dict:
    t=np.asarray(times,dtype=float);v=np.asarray(velocities,dtype=float)
    mask=v>0
    if mask.sum()<2:raise ValueError("need at least two positive velocities")
    x=t[mask];y=1/v[mask];coef=np.polyfit(x,y,1);slope,intercept=coef
    failure_time=float(-intercept/slope) if slope<0 else None
    return {"slope":float(slope),"intercept":float(intercept),"predicted_failure_time":failure_time,"accelerating":slope<0,"method":"inverse-velocity linear extrapolation"}

def pile_group_efficiency(rows:int,cols:int,spacing_diameters:float)->dict:
    count=rows*cols;eta=max(.4,min(1,0.65+0.08*spacing_diameters-0.01*max(count-4,0)))
    return {"pile_count":count,"efficiency":eta,"group_capacity_multiplier":count*eta,"method":"pile-group screening heuristic"}
