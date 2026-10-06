from __future__ import annotations
import json,uuid
from datetime import datetime,timezone

DIGGS_VERSION="3.0"
def diggs_export(project:dict,boreholes:list[dict],tests:list[dict]|None=None,geophysics:list[dict]|None=None)->dict:
    return {"diggs":{"version":DIGGS_VERSION,"project":project,"boreholes":boreholes,"laboratory_tests":tests or [],
      "geophysics":geophysics or [],"generated_at":datetime.now(timezone.utc).isoformat()},
      "note":"GeoTect canonical DIGGS 3.0 JSON representation; XML serializer/validator can map this contract to the official schema."}

def ags_crosswalk(records:list[dict])->dict:
    mapped=[]
    for r in records:
        mapped.append({"location_id":r.get("LOCA_ID") or r.get("location_id"),"depth_from_m":r.get("GEOL_TOP") or r.get("from_m"),
          "depth_to_m":r.get("GEOL_BASE") or r.get("to_m"),"description":r.get("GEOL_DESC") or r.get("description"),
          "source":"AGS","raw":r})
    return {"records":mapped,"target":"GeoTect borehole interval canonical model"}

def ifc43_geotechnical_manifest(project:dict,boreholes:list[dict],strata:list[dict],cuts:list[dict]|None=None,fills:list[dict]|None=None)->dict:
    entities=[]
    for b in boreholes:entities.append({"ifc_type":"IfcBorehole","global_id":b.get("id",str(uuid.uuid4())),"name":b.get("id"),"properties":b})
    for s in strata:entities.append({"ifc_type":"IfcGeotechnicalStratum","global_id":s.get("id",str(uuid.uuid4())),"name":s.get("name"),"properties":s})
    for x in cuts or []:entities.append({"ifc_type":"IfcEarthworksCut","global_id":x.get("id",str(uuid.uuid4())),"properties":x})
    for x in fills or []:entities.append({"ifc_type":"IfcEarthworksFill","global_id":x.get("id",str(uuid.uuid4())),"properties":x})
    return {"schema":"IFC4X3","project":project,"entities":entities,"validation":{"status":"manifest_ready","ids_required":True}}

def ids_validate(objects:list[dict],requirements:list[dict])->dict:
    failures=[]
    for req in requirements:
        selector=req.get("ifc_type");required=req.get("required_properties",[])
        candidates=[o for o in objects if not selector or o.get("ifc_type")==selector]
        if not candidates:failures.append({"requirement":req,"reason":"no_matching_entity"});continue
        for obj in candidates:
            props=obj.get("properties",{})
            missing=[p for p in required if p not in props or props[p] in (None,"")]
            if missing:failures.append({"entity":obj.get("global_id"),"missing":missing,"requirement":req})
    return {"valid":not failures,"failures":failures,"checked":len(requirements)}

def stac_item(asset_id:str,bbox:list[float],geometry:dict,assets:dict,properties:dict|None=None)->dict:
    return {"stac_version":"1.0.0","type":"Feature","id":asset_id,"bbox":bbox,"geometry":geometry,
      "properties":{"datetime":datetime.now(timezone.utc).isoformat(),**(properties or {})},"links":[],"assets":assets}

def stac_catalog(catalog_id:str,items:list[dict])->dict:
    return {"stac_version":"1.0.0","type":"Catalog","id":catalog_id,"description":"GeoTect Earth-observation catalog",
      "links":[{"rel":"item","href":f"items/{x['id']}.json","type":"application/geo+json"} for x in items]}

def sensorthings_observation(sensor_id:str,datastream_id:str,result,unit:str,phenomenon_time:str|None=None)->dict:
    return {"@iot.id":str(uuid.uuid4()),"phenomenonTime":phenomenon_time or datetime.now(timezone.utc).isoformat(),
      "result":result,"Datastream":{"@iot.id":datastream_id},"parameters":{"sensor_id":sensor_id,"unit":unit}}

def bcf_issue(issue:dict)->dict:
    return {"guid":issue.get("id") or str(uuid.uuid4()),"topic_type":issue.get("issue_type","Issue"),"topic_status":issue.get("status","Open"),
      "title":issue.get("title","GeoTect issue"),"priority":issue.get("priority","Normal"),"reference_links":issue.get("reference_links",[]),
      "viewpoints":issue.get("viewpoint",{}),"linked_objects":issue.get("linked_objects",[])}

def opencde_container(project_id:str,documents:list[dict])->dict:
    return {"project_id":project_id,"containers":[{"id":d.get("id") or str(uuid.uuid4()),"name":d.get("name"),"revision":d.get("revision"),
      "status":d.get("status","work_in_progress"),"metadata":d.get("metadata",{})} for d in documents]}
