import numpy as np
from verification_campaigns import wave_propagation_benchmark,phase_field_energy_convergence,compare_cpu_gpu
from calibration_campaigns import calibrate_liquefaction_style
from designsafe_client import published_corral_path,nees_corral_path

def test_wave_benchmark():
    out=wave_propagation_benchmark(length_m=10,vs_m_s=100,dt_s=.001,duration_s=.3)
    assert out["relative_error"]<.02

def test_phase_field_campaign_small():
    out=phase_field_energy_convergence(levels=(5,7),Gc_kpa_m=.1,length_scale_m=.1)
    assert out["passed"]
    assert len(out["rows"])==2

def test_cpu_gpu_compare_identity():
    out=compare_cpu_gpu([1,2,3],[1,2,3])
    assert out["l2_relative_error"]==0

def test_liquefaction_calibration_smoke():
    hist=[[0,0,0,0.001,0,0], [0,0,0,-0.001,0,0]]*2
    out=calibrate_liquefaction_style(hist,[0,0,0,0],bounds={"Dr":(.4,.6),"G0":(400,500)},maxiter=1)
    assert "parameters" in out and np.isfinite(out["objective_rmse"])

def test_designsafe_paths():
    assert published_corral_path("PRJ-1234").endswith("/PRJ-1234/")
    assert "public/projects" in nees_corral_path("NEES-TEST")
