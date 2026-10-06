from probabilistic import monte_carlo_slope
from investigation import recommend_locations
from design_tools import bearing_capacity,retaining_wall
from risk_automation import evaluate_rules
from copilot import interpret_command
from field_sync import merge_offline_records
from interoperability import export_geojson

def test_probabilistic_slope():
    x=monte_carlo_slope(1000,35,28,2,5,1)
    assert 0<=x["probability_of_failure"]<=1
    assert x["fos"]["p05"]<=x["fos"]["p95"]

def test_investigation_optimizer():
    c=[{"x":0,"y":0,"uncertainty":.9},{"x":100,"y":100,"uncertainty":.8},{"x":10,"y":10,"uncertainty":.2}]
    out=recommend_locations(c,[{"x":0,"y":10}],2,20)
    assert len(out["recommendations"])<=2

def test_design_screening():
    assert bearing_capacity(2,1,18,5,30)["ultimate_bearing_capacity_kpa"]>0
    assert retaining_wall(5,18,30)["resultant_active_force_kn_m"]>0

def test_rule_engine_and_copilot():
    out=evaluate_rules({"rain":100,"pore":50},[{"id":"x","conditions":[{"field":"rain","op":"gt","value":80}],"actions":["rerun_slope"]}])
    assert out["count"]==1
    cmd=interpret_command("draw a tunnel 40 m below terrain")
    assert cmd["actions"][0]["tool"]=="draw_tunnel"

def test_offline_conflict_and_geojson():
    m=merge_offline_records([{"id":"1","version":2,"updated_at":"2"}],[{"id":"1","base_version":1,"updated_at":"3"}])
    assert len(m["conflicts"])==1
    g=export_geojson([{"id":"p","geometry":"point","positions":[{"lon":1,"lat":2,"elevation_m":3}]}])
    assert g["features"][0]["geometry"]["type"]=="Point"
