from __future__ import annotations
import numpy as np

def solve_thm_1d(length_m:float,n:int,dt_s:float,steps:int,thermal_diffusivity_m2_s:float,hydraulic_diffusivity_m2_s:float,
                 thermal_expansion_1_k:float,biot_alpha:float,young_pa:float,initial_temp_c:float=20,
                 left_temp_c:float=20,right_temp_c:float=20,initial_head_m:float=0,left_head_m:float=0,right_head_m:float=0):
    n=max(3,n);dx=length_m/(n-1);T=np.full(n,initial_temp_c,float);h=np.full(n,initial_head_m,float);u=np.zeros(n);hist=[]
    rt=thermal_diffusivity_m2_s*dt_s/dx**2;rh=hydraulic_diffusivity_m2_s*dt_s/dx**2
    if rt>.5 or rh>.5:raise ValueError("explicit THM diffusion step unstable")
    for s in range(steps):
        Tn=T.copy();hn=h.copy()
        Tn[1:-1]=T[1:-1]+rt*(T[2:]-2*T[1:-1]+T[:-2]);hn[1:-1]=h[1:-1]+rh*(h[2:]-2*h[1:-1]+h[:-2])
        Tn[0]=left_temp_c;Tn[-1]=right_temp_c;hn[0]=left_head_m;hn[-1]=right_head_m
        strain_t=thermal_expansion_1_k*(Tn-initial_temp_c);strain_h=biot_alpha*(hn-initial_head_m)*9810/max(young_pa,1e-12)
        strain=strain_t+strain_h;u=np.cumsum(strain)*dx
        T,h=Tn,hn;hist.append({"step":s+1,"max_temp_c":float(T.max()),"min_temp_c":float(T.min()),"max_displacement_m":float(np.max(np.abs(u)))})
    return {"x_m":np.linspace(0,length_m,n).tolist(),"temperature_c":T.tolist(),"head_m":h.tolist(),"displacement_m":u.tolist(),"history":hist,
      "method":"coupled 1D thermo-hydro-mechanical diffusion/strain baseline"}
