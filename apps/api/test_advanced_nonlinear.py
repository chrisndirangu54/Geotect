import numpy as np
import scipy.sparse as sp
from solver_backend import solve_sparse
from interface_elements import InterfaceState,coulomb_interface_response
from continuation_benchmarks import snap_through_scalar
from coupled_up_fem import solve_monolithic_up_2d
from elastoplastic_fem import solve_adaptive_elastoplastic
from convergence_studies import observed_order

def test_sparse_solver_cpu():
    A=sp.csr_matrix([[4.0,1.0],[1.0,3.0]]);b=np.array([1.0,2.0])
    x,info=solve_sparse(A,b,method="spsolve",backend="auto")
    assert info.converged
    assert np.linalg.norm(A@x-b)<1e-10

def test_coulomb_interface_slips():
    s=InterfaceState()
    ns,K,info=coulomb_interface_response([-0.001,0.02],s,1e5,1e4,30,cohesion_kpa=1)
    assert info["normal_traction_kpa"]>0
    assert not info["sticking"]
    assert abs(info["shear_traction_kpa"])<=info["strength_kpa"]+1e-9
    assert abs(ns.plastic_slip_m)>0

def test_arc_length_continuation_runs():
    out=snap_through_scalar(steps=5,arc_length=.03)
    assert len(out["path"])>=1
    assert np.isfinite(out["load_factor"])

def test_monolithic_up_finite():
    out=solve_monolithic_up_2d(
      4,2,3,3,
      {"model":"mohr_coulomb","E_kpa":50000,"nu":.3,"cohesion_kpa":1e6,"friction_deg":0},
      {"ks_m_s":1e-6,"theta_r":.05,"theta_s":.45,"alpha_1_m":1.6,"n_vg":1.6,"specific_storage_1_kpa":1e-5},
      dt_s=60,steps=1,density_kg_m3=0,top_pressure_kpa=.1,initial_pore_pressure_kpa=0,
      newton_max=10,tolerance=1e-5,parallel_assembly=False,linear_method="spsolve")
    assert len(out["pore_pressure_kpa"])==len(out["nodes_m"])
    assert np.all(np.isfinite(out["pore_pressure_kpa"]))
    assert np.all(np.isfinite(out["displacement_m"]))

def test_adaptive_driver_and_order():
    base={"width_m":4,"height_m":2,"nx":3,"ny":3,"material":{"model":"mohr_coulomb","E_kpa":30000,"nu":.3,"cohesion_kpa":1e6,"friction_deg":0},
      "density_kg_m3":0,"top_pressure_kpa":1,"load_steps":1,"newton_max":8}
    out=solve_adaptive_elastoplastic(base,cycles=2,refine_fraction=.25)
    assert len(out["cycles"])>=1
    order=observed_order([.25,.0625,.015625],[1,.5,.25])
    assert abs(order["mean_order"]-2)<1e-12
