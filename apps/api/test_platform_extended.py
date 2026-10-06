from remote_sensing import ndvi,raster_change,pointcloud_change
from advanced_geophysics import linear_potential_inversion,masw_dispersion
from construction_mining import cut_fill,bench_geometry,convergence
from tiles3d import point_tiles_to_3dtiles
from billing import quota

def test_remote_sensing():
    n=ndvi([[1,2]],[[3,4]])
    assert n["max"]<=1 and n["min"]>=-1
    c=raster_change([[1,1]],[[2,1]],.5)
    assert c["changed_fraction"]==.5

def test_pointcloud_change():
    out=pointcloud_change([[0,0,0],[1,1,1]],[[0,0,0],[2,2,2]],.2)
    assert out["sampled_points"]==2

def test_geophysics_baselines():
    inv=linear_potential_inversion([[1,0],[0,1],[1,1]],[1,2,3],.1)
    assert len(inv["model"])==2
    m=masw_dispersion([10,20],[300,400])
    assert len(m["sensitivity_depth_m"])==2

def test_construction_mining():
    v=cut_fill([[0,0],[0,0]],[[1,-1],[2,-2]],10)
    assert v["cut_m3"]==v["fill_m3"]
    assert bench_geometry(10,5,60,3)["bench_count"]==3
    assert convergence(5,4.99)["closure_mm"]>0

def test_3dtiles_and_quota():
    manifest={"format":"geotect-point-tiles-v1","tiles":[{"uri":"tile.npz","points":10,"min":[0,0,0],"max":[1,1,1]}]}
    assert len(point_tiles_to_3dtiles(manifest)["root"]["children"])==1
    assert quota("free",{"compute_jobs_month":21})["allowed"] is False
