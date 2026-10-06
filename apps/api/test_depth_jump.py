import numpy as np
from mixed_elements import p2_shape,enrich_triangles_p2
from large_deformation import deformation_gradient,jacobian,green_lagrange
from strength_reduction import reduce_strength
from cyclic_materials import cyclic_series,newmark_beta_sdof
from contact_surfaces import SurfaceContactState,coulomb_surface_contact
from quadratic_up_fem import solve_quadratic_up_2d
from updated_lagrangian_fem import solve_updated_lagrangian_2d
from parallel_backends import execution_capabilities,mpi_partition
from verification_dashboard import render_html

def test_p2_partition_and_enrichment():
    N,dr,ds=p2_shape(.2,.3)
    assert abs(float(N.sum())-1)<1e-12
    nodes=np.array([[0,0],[1,0],[0,1]],float);tris=np.array([[0,1,2]],int)
    n6,t6,_=enrich_triangles_p2(nodes,tris)
    assert len(n6)==6 and t6.shape==(1,6)

def test_large_deformation_kinematics():
    F=deformation_gradient(np.array([[.1,0],[0,-.05]]))
    assert jacobian(F)>0
    E=green_lagrange(F)
    assert E.shape==(2,2)

def test_strength_reduction_material():
    m=reduce_strength({"cohesion_kpa":20,"friction_deg":30,"dilation_deg":10},2)
    assert m["cohesion_kpa"]==10
    assert 0<m["friction_deg"]<30

def test_cyclic_and_dynamic():
    c=cyclic_series([0,.001,-.001,.001],50000,.001)
    assert len(c["history"])==4
    d=newmark_beta_sdof([0,1,-1,0],.01,1,100)
    assert np.isfinite(d["max_abs_displacement_m"])

def test_3d_surface_contact():
    out=coulomb_surface_contact([.2,.2,.1],[0,0,-.2],[[0,0,0],[1,0,0],[0,1,0]],SurfaceContactState(),1e5,1e4,30,1)
    assert out["normal_traction_kpa"]>0
    assert len(out["force_directional_kpa"])==3

def test_quadratic_up_smoke():
    out=solve_quadratic_up_2d(2,1,2,2,
      {"model":"mohr_coulomb","E_kpa":50000,"nu":.3,"cohesion_kpa":1e6,"friction_deg":0},
      permeability_m_s=1e-6,storage_1_kpa=1e-4,dt_s=60,steps=1,top_pressure_kpa=.01,density_kg_m3=0,newton_max=8,tolerance=1e-5)
    assert np.all(np.isfinite(out["displacement_m"]))
    assert np.all(np.isfinite(out["pore_pressure_kpa"]))

def test_updated_lagrangian_smoke():
    out=solve_updated_lagrangian_2d(2,1,3,2,{"model":"mohr_coulomb","E_kpa":50000,"nu":.3,"cohesion_kpa":1e9,"friction_deg":0},
      top_pressure_kpa=.01,density_kg_m3=0,load_steps=1,newton_max=8,tolerance=1e-5)
    assert np.all(np.isfinite(out["displacement_m"]))

def test_execution_capabilities_and_dashboard():
    caps=execution_capabilities();part=mpi_partition(10)
    assert caps["cpu_sparse"] is True
    assert part["count"]>=0
    html=render_html({"version":"test","commit_sha":"abc","benchmarks":{"cases":[]},"convergence":{"studies":[]},"execution_capabilities":caps})
    assert "GeoTect Solver Verification" in html
