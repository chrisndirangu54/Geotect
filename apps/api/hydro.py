def darcy_flux(permeability_m_s:float,head_up_m:float,head_down_m:float,length_m:float,area_m2:float=1.0)->dict:
    if length_m<=0 or area_m2<=0: raise ValueError("length and area must be positive")
    gradient=(head_up_m-head_down_m)/length_m
    q=permeability_m_s*area_m2*gradient
    return {"specific_discharge_m_s":permeability_m_s*gradient,"flow_m3_s":q,"hydraulic_gradient":gradient,"method":"Darcy screening"}

def pore_pressure(gamma_w_kn_m3:float,pressure_head_m:float)->float:
    return gamma_w_kn_m3*max(pressure_head_m,0)
