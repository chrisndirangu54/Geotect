from open_standards import bcf_issue,opencde_container
from advanced_engineering import richards_bucket,newmark_sliding,rock_mass_classification,tailings_freeboard,pile_group_efficiency
from engineering_agents import select_models,rank_root_causes

def test_remaining_engineering():
    assert 0<=richards_bucket(.2,.4,.05,50,0,1)["saturation"]<=1
    assert newmark_sliding([0,.5,.6],.1,.2)["permanent_displacement_m"]>=0
    assert rock_mass_classification(70,.5,55)["RMR_proxy"]>0
    assert tailings_freeboard(105,100,1,1)["effective_freeboard_m"]==3
    assert pile_group_efficiency(2,2,3)["group_capacity_multiplier"]>0

def test_governance_formats_and_agents():
    assert "guid" in bcf_issue({"title":"x"})
    assert len(opencde_container("p",[{"name":"doc"}])["containers"])==1
    assert select_models({"soil":"clay","groundwater":True,"regional_scale":True})["groundwater_model"]=="MODFLOW 6"
    r=rank_root_causes({"rain":10},[{"cause":"rainfall","signals":{"rain":{"target":10,"tolerance":2,"weight":1}}}])
    assert r["ranked_causes"][0]["cause"]=="rainfall"
