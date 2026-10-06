import math
import numpy as np
from ert_inversion import invert_ert
from groundwater_pde import solve_steady_groundwater
from geology_solids import extrude_stratum
from sections import build_fence_section,correlate_boreholes
from seismic_volume import reconstruct_volume

def test_ert_inversion_positive():
    G=[[1,0],[0,1],[.5,.5]]
    rho=[100,200,math.sqrt(100*200)]
    out=invert_ert(G,rho,regularization=.1,iterations=3)
    assert len(out["cell_resistivity_ohm_m"])==2
    assert all(v>0 for v in out["cell_resistivity_ohm_m"])

def test_groundwater_gradient():
    out=solve_steady_groundwater(8,5,1,1,1e-5,100,90,max_iterations=5000)
    h=np.array(out["head_m"])
    assert h[:,0].mean()>h[:,-1].mean()
    assert out["converged"]

def test_geology_solid_closed_faces():
    s=extrude_stratum("unit",[[36,-1],[36.01,-1],[36.01,-1.01],[36,-1.01]],100,80,.8)
    assert len(s["vertices"])==8
    assert len(s["triangles"])>=12

def test_section_and_correlation():
    b=[
      {"id":"A","collar":{"lon":36.0,"lat":-1.0,"elevation_m":100},"intervals":[{"from_m":0,"to_m":10,"lithology":"basalt","confidence":.9}]},
      {"id":"B","collar":{"lon":36.01,"lat":-1.0,"elevation_m":101},"intervals":[{"from_m":1,"to_m":12,"lithology":"basalt","confidence":.8}]}
    ]
    sec=build_fence_section([{"lon":35.99,"lat":-1.0},{"lon":36.02,"lat":-1.0}],b)
    cor=correlate_boreholes(b)
    assert len(sec["columns"])==2
    assert len(cor["correlations"])==1

def test_seismic_reconstruction_shape():
    traces=[{"x":0,"y":0,"dt_s":.001,"samples":[0,1,0]},{"x":10,"y":0,"dt_s":.001,"samples":[0,2,0]}]
    out=reconstruct_volume(traces,4,3,1800)
    assert out["shape"]==[3,4,3]
