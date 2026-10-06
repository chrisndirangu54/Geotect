TEMPLATES={
 "tailings_dam":{"layers":["dam_shell","beach","pond","foundation","piezometers","inclinometers","insar"],"risks":["overtopping","internal_erosion","slope_instability"]},
 "highway_cut":{"layers":["alignment","cut_slope","geology","drainage","rockfall"],"risks":["landslide","rockfall","erosion"]},
 "building_foundation":{"layers":["footprints","boreholes","cpt","groundwater","foundations"],"risks":["settlement","bearing_failure","liquefaction"]},
 "open_pit":{"layers":["pit","benches","ramps","faults","slope_radar","piezometers","waste_dumps"],"risks":["bench_failure","inter_ramp_failure","rockfall"]},
 "underground_mine":{"layers":["declines","stopes","drives","support","seismicity","ventilation"],"risks":["fall_of_ground","seismic_event","inrush"]},
 "tunnel":{"layers":["alignment","excavation","support","geology","groundwater","convergence"],"risks":["face_instability","convergence","water_ingress"]},
 "corridor":{"layers":["chainage","alignment","geology","crossings","hazards"],"risks":["landslide","settlement","flood","erosion"]},
 "esg":{"layers":["water","vegetation","rehabilitation","biodiversity","communities","emissions"],"risks":["water_quality","erosion","habitat_disturbance","community_exposure"]},
 "emergency":{"layers":["incidents","evacuation","assets","sensors","access","weather"],"risks":["life_safety","access_loss","secondary_failure"]}
}
def template(name:str)->dict:
    if name not in TEMPLATES:raise KeyError(name)
    return {"name":name,**TEMPLATES[name]}
