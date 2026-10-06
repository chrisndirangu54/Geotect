from __future__ import annotations
import math

def bearing_capacity(width_m:float,depth_m:float,gamma_kn_m3:float,cohesion_kpa:float,friction_deg:float)->dict:
    phi=math.radians(friction_deg);nq=math.exp(math.pi*math.tan(phi))*math.tan(math.pi/4+phi/2)**2 if friction_deg>0 else 1
    nc=(nq-1)/math.tan(phi) if friction_deg>0 else 5.14;ng=2*(nq+1)*math.tan(phi) if friction_deg>0 else 0
    q=gamma_kn_m3*depth_m;qu=cohesion_kpa*nc+q*nq+.5*gamma_kn_m3*width_m*ng
    return {"ultimate_bearing_capacity_kpa":qu,"allowable_kpa_fs3":qu/3,"method":"Terzaghi-style strip footing screening"}

def elastic_settlement(load_kpa:float,width_m:float,young_mpa:float,poisson:float,influence:float=1)->dict:
    s=(load_kpa*1000*width_m*(1-poisson**2)/(young_mpa*1e6))*influence
    return {"settlement_m":s,"settlement_mm":s*1000,"method":"elastic half-space screening"}

def retaining_wall(height_m:float,gamma_kn_m3:float,friction_deg:float,surcharge_kpa:float=0)->dict:
    phi=math.radians(friction_deg);ka=math.tan(math.pi/4-phi/2)**2
    soil=.5*ka*gamma_kn_m3*height_m**2;surcharge=ka*surcharge_kpa*height_m
    return {"ka":ka,"resultant_active_force_kn_m":soil+surcharge,"application_height_m":height_m/3,"method":"Rankine active earth pressure"}

def pile_capacity(diameter_m:float,length_m:float,unit_shaft_kpa:float,unit_base_kpa:float)->dict:
    shaft=math.pi*diameter_m*length_m*unit_shaft_kpa;base=math.pi*(diameter_m**2)/4*unit_base_kpa
    return {"shaft_kn":shaft,"base_kn":base,"ultimate_kn":shaft+base,"allowable_kn_fs2_5":(shaft+base)/2.5,"method":"unit shaft/base capacity screening"}

def liquefaction_screening(csr:float,crr:float,msf:float=1.0)->dict:
    fs=crr*msf/max(csr,1e-9)
    return {"factor_of_safety":fs,"susceptible_screening":fs<1.0,"method":"CSR/CRR screening; requires site-specific corrections"}
