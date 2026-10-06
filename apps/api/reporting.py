from __future__ import annotations
from datetime import datetime,timezone
def engineering_report(project:dict,sections:list[dict],results:list[dict],risks:list[dict],approvals:list[dict])->dict:
    return {"title":f'GeoTect Engineering Report — {project.get("name","Project")}',"generated_at":datetime.now(timezone.utc).isoformat(),
      "executive_summary":{"project_id":project.get("id"),"risk_count":len(risks),"analysis_count":len(results),"approval_state":approvals[-1].get("state") if approvals else "draft"},
      "project":project,"sections":sections,"analyses":results,"risks":risks,"approvals":approvals,
      "disclaimer":"Numerical results retain method/assumption metadata and require competent professional review where applicable."}

def borehole_log(bh:dict)->dict:
    return {"id":bh["id"],"collar":bh["collar"],"total_depth_m":bh["total_depth_m"],"columns":[{"from_m":i["from_m"],"to_m":i["to_m"],"lithology":i["lithology"],"confidence":i.get("confidence",1)} for i in bh.get("intervals",[])]}
