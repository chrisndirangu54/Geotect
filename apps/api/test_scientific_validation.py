import numpy as np
from dynamic_up3d import solve_dynamic_up3d_hex
from phase_field_fracture import solve_phase_field_2d,xfem_heaviside_enrichment
from thm3d_fem import solve_thm3d_tet
from experimental_validation import dataset_catalog,validation_metrics,validate_channels
from opensees_reference import available as opensees_available

def test_dynamic_up3d_smoke():
    out=solve_dynamic_up3d_hex(
      1,1,1,2,2,2,
      {"model":"anisotropic_critical_state","E_kpa":50000,"nu":.3},
      accel_m_s2=[[0,0,0],[1e-4,0,0]],dt_s=.01,permeability_m_s=1e-6,storage_1_kpa=1e-3,
      density_kg_m3=1800,rayleigh_a0=.01,absorbing_boundaries=True,newton_max=5,tolerance=1e-4)
    assert len(out["history"])==2
    assert np.all(np.isfinite(out["displacement_m"]))
    assert np.all(np.isfinite(out["pore_pressure_kpa"]))

def test_phase_field_and_xfem():
    out=solve_phase_field_2d(1,1,3,3,30000,.25,.1,.1,1e-4,steps=2)
    assert len(out["phase_field"])==len(out["nodes_m"])
    assert all(0<=x<=1 for x in out["phase_field"])
    xf=xfem_heaviside_enrichment([[0,0],[1,0],[0,1],[1,1]],[.5,0],[1,0])
    assert len(xf["level_set"])==4

def test_thm3d_smoke():
    out=solve_thm3d_tet(1,1,1,2,2,2,30000,.3,1.0,1e-5,1e-6,2.0,1e3,1e-4,.1,2,
      initial_temp_c=20,top_temp_c=21,initial_p_kpa=0,top_p_kpa=0)
    assert len(out["history"])==2
    assert np.all(np.isfinite(out["temperature_c"]))
    assert np.all(np.isfinite(out["displacement_m"]))

def test_experimental_validation_catalog_and_metrics():
    cat=dataset_catalog()
    assert "censeis" in cat and "leap" in cat and "ngl" in cat
    m=validation_metrics([0,1,2],[0,1,2],[0,1,2],[0,1.1,1.9])
    assert m["rmse"]<.2
    v=validate_channels({"time":[0,1,2],"a":[0,1,2]},{"time":[0,1,2],"b":[0,1.1,1.9]},{"accel":{"observed":"a","simulated":"b","tolerances":{"peak_relative_error":.2,"r2":.8}}})
    assert v["passed"]

def test_opensees_reference_is_optional():
    info=opensees_available()
    assert "available" in info
