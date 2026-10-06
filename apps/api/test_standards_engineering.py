from open_standards import diggs_export,ags_crosswalk,ifc43_geotechnical_manifest,ids_validate,stac_item,sensorthings_observation
from advanced_engineering import mohr_coulomb_strength,hoek_brown_strength,coupled_hydro_mechanical,consolidation_time,inverse_velocity_failure
from engineering_agents import route_agent,evidence_answer,anomaly_zscore
from calibration import calibrate_scalar

def test_open_standards():
    assert diggs_export({},[])["diggs"]["version"]=="3.0"
    assert ags_crosswalk([{"LOCA_ID":"BH1","GEOL_TOP":0,"GEOL_BASE":2}])["records"][0]["location_id"]=="BH1"
    m=ifc43_geotechnical_manifest({},[{"id":"BH1"}],[])
    assert m["schema"]=="IFC4X3"
    assert ids_validate(m["entities"],[{"ifc_type":"IfcBorehole","required_properties":["id"]}])["valid"]
    assert stac_item("x",[0,0,1,1],{"type":"Point","coordinates":[0,0]},{})["stac_version"]=="1.0.0"
    assert "Datastream" in sensorthings_observation("s","d",1,"m")

def test_advanced_engineering():
    assert mohr_coulomb_strength(100,5,30)["shear_strength_kpa"]>0
    assert hoek_brown_strength(5,50,1,1,.5)["sigma1_failure_mpa"]>5
    assert coupled_hydro_mechanical([[100]],[[20]])["effective_stress_kpa"][0][0]==80
    assert len(consolidation_time(100,1e-6,2,[0,1000])["series"])==2
    assert inverse_velocity_failure([0,1,2],[1,2,4])["accelerating"]

def test_agents_and_calibration():
    assert route_agent("groundwater pore pressure modflow")["agent"]=="hydrogeology"
    assert evidence_answer("q",[{"id":"BH1","type":"borehole"}],"x",.8)["evidence_count"]==1
    assert isinstance(anomaly_zscore([1,1,1,10])["anomalies"],list)
    assert calibrate_scalar([2,4],[1,2],10)["parameter_after"]>10
