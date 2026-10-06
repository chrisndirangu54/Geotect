import numpy as np
from up3d_fem import solve_up3d_tet
from hex8_up_fem import solve_up3d_hex
from materials3d import LiquefactionSandStyle,AnisotropicCriticalState
from nonlocal_softening import nonlocal_average,regularized_strength
from fracture_remesh import remesh_contact_surfaces
from thm_coupling import solve_thm_1d
from parallel_backends import execution_capabilities

def test_up3d_tet_smoke():
    out=solve_up3d_tet(1,1,1,2,2,2,
      {"model":"anisotropic_critical_state","E_kpa":50000,"nu":.3},
      permeability_m_s=1e-6,storage_1_kpa=1e-4,dt_s=10,steps=1,top_pressure_kpa=.001,density_kg_m3=0,newton_max=5,tolerance=1e-5)
    assert len(out["tetrahedra"])>0
    assert np.all(np.isfinite(out["displacement_m"]))
    assert np.all(np.isfinite(out["pore_pressure_kpa"]))

def test_up3d_hex_smoke():
    out=solve_up3d_hex(1,1,1,2,2,2,
      {"model":"anisotropic_critical_state","E_kpa":50000,"nu":.3},
      permeability_m_s=1e-6,storage_1_kpa=1e-4,dt_s=10,steps=1,top_pressure_kpa=.001,density_kg_m3=0,newton_max=5,tolerance=1e-5)
    assert len(out["hexahedra"])==1
    assert np.all(np.isfinite(out["displacement_m"]))

def test_liquefaction_style_state():
    m=LiquefactionSandStyle(Dr=.35,G0=476,hpo=.53)
    s=m.initial();rus=[]
    for sign in [1,-1]*8:
        de=np.array([0,0,0,sign*2e-3,0,0],float)
        s,_,meta=m.integrate(s,de,100);rus.append(s.pore_pressure_ratio)
    assert all(0<=x<1 for x in rus)
    assert rus[-1]>=rus[0]

def test_anisotropic_critical_state():
    m=AnisotropicCriticalState();s=m.initial()
    for _ in range(5):
        s,_,meta=m.integrate(s,np.array([-1e-3,-5e-4,-5e-4,1e-3,0,0]))
    assert np.all(np.isfinite(s.stress))
    assert s.hardening>=0

def test_nonlocal_and_fracture_remesh():
    c=[[0,0],[1,0],[0,1]];v=[0,1,0]
    nl=nonlocal_average(c,v,.75)
    assert len(nl)==3
    reg=regularized_strength(20,30,v,c,.75)
    assert len(reg["cohesion_kpa"])==3
    rem=remesh_contact_surfaces([[0,0],[1,0],[0,1]],[[0,1,2]],[1.0],.8)
    assert len(rem["triangles"])==2
    assert len(rem["contact_interfaces"])==1

def test_thm_smoke_and_optional_backends():
    out=solve_thm_1d(1,11,1,5,1e-4,1e-4,1e-5,1,30e6,20,30,20,0,1,0)
    assert len(out["history"])==5
    assert np.all(np.isfinite(out["displacement_m"]))
    caps=execution_capabilities()
    assert caps["cpu_sparse"] is True
