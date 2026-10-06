import math

def limit_equilibrium_screening(slope_deg:float,friction_deg:float,cohesion_kpa:float,gamma_kn_m3:float,height_m:float,pore_pressure_ratio:float=0.0)->dict:
    beta=math.radians(max(slope_deg,.1));phi=math.radians(friction_deg)
    normal=gamma_kn_m3*height_m*math.cos(beta)**2
    effective=max(normal*(1-max(0,min(pore_pressure_ratio,1))),.001)
    resisting=cohesion_kpa+effective*math.tan(phi)
    driving=max(gamma_kn_m3*height_m*math.sin(beta)*math.cos(beta),.001)
    fos=resisting/driving
    return {"factor_of_safety":round(fos,4),"method":"infinite-slope/LEM screening","status":"screening","stable_screening":fos>=1.3}

class ExternalFEMAdapter:
    """Contract for validated FEM engines. GeoTect never fabricates FEM output."""
    name="external-fem"
    async def run(self,model:dict)->dict:
        raise NotImplementedError("Configure a validated FEM backend (e.g. OpenSees/FEniCSx/vendor solver) before running FEM.")

def fem_capabilities()->dict:
    return {"status":"adapter_required","accepted_model_parts":["mesh","materials","boundary_conditions","stages","loads","groundwater"],
            "outputs_expected":["displacement","stress","strain","plastic_points","factor_of_safety"],"fake_solver":False}
