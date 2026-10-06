import numpy as np
from elastoplastic_materials import MohrCoulomb,HardeningSoil
from elastoplastic_fem import solve_elastoplastic_2d,staged_excavation,adaptive_mesh_cycle
from biot_solver import solve_biot_1d
from richards_solver import solve_richards_1d
from solver_benchmarks import suite

def test_mc_return_mapping_on_envelope():
    m=MohrCoulomb(30000,.3,10,30,0);s=m.initial_state();s.stress=np.array([-100.0,-100.0,0.0])
    yielded=False
    for _ in range(100):
        s,_,info=m.integrate(s,np.array([5e-5,-5e-5,0]))
        yielded=yielded or s.yielded
    assert yielded
    assert abs(m.yield_value(s.stress))<1e-3

def test_hardening_soil_state_evolves():
    m=HardeningSoil(30000,25000,90000,.2,5,30,0,.5,100,.9,100,1.2);s=m.initial_state();s.stress=np.array([-100.0,-100.0,0.0])
    for _ in range(60):s,_,_=m.integrate(s,np.array([5e-5,-5e-5,0]))
    assert s.eq_plastic_shear>=0
    assert s.pc_kpa>0

def test_elastoplastic_fem_and_staging():
    mat={"model":"mohr_coulomb","E_kpa":30000,"nu":.3,"cohesion_kpa":20,"friction_deg":30}
    out=solve_elastoplastic_2d(8,4,4,3,mat,top_pressure_kpa=5,load_steps=2,newton_max=8)
    assert len(out["element_states"])==len(out["triangles"])
    staged=staged_excavation({"width_m":8,"height_m":4,"nx":4,"ny":3,"material":mat,"load_steps":1,"newton_max":6},
        [{"name":"initial"},{"name":"excavate","deactivate_elements":[0]}])
    assert len(staged["stages"])==2
    assert 0 in staged["stages"][1]["result"]["inactive_elements"]
    mesh=adaptive_mesh_cycle(out,.25)["refined_mesh"]
    assert len(mesh["triangles"])>=len(out["triangles"])

def test_biot_and_richards():
    b=solve_biot_1d(5,11,30e6,.3,1e-9,9810,1.0,1e-9,50e3,3600,4)
    assert len(b["series"])==4
    r=solve_richards_1d(1,21,-1,.05,.45,1.6,1.6,1e-5,60,3,top_flux_m_s=1e-7)
    assert len(r["history"])==3
    assert all(np.isfinite(r["head_m"]))

def test_reference_suite():
    out=suite()
    assert out["passed"],out
