from __future__ import annotations
from urllib.parse import urlencode
import httpx

async def esri_service_info(base_url:str,token:str|None=None)->dict:
    params={"f":"json"}
    if token:params["token"]=token
    async with httpx.AsyncClient(timeout=20) as c:
        r=await c.get(base_url.rstrip("/"),params=params);r.raise_for_status();return r.json()

async def esri_query(layer_url:str,where:str="1=1",out_fields:str="*",token:str|None=None,result_offset:int=0,result_record_count:int=2000)->dict:
    params={"f":"json","where":where,"outFields":out_fields,"returnGeometry":"true","resultOffset":result_offset,"resultRecordCount":result_record_count}
    if token:params["token"]=token
    async with httpx.AsyncClient(timeout=60) as c:
        r=await c.get(layer_url.rstrip("/")+"/query",params=params);r.raise_for_status();return r.json()

async def esri_apply_edits(layer_url:str,adds:list|None=None,updates:list|None=None,deletes:list|None=None,token:str|None=None)->dict:
    data={"f":"json"}
    import json
    if adds:data["adds"]=json.dumps(adds)
    if updates:data["updates"]=json.dumps(updates)
    if deletes:data["deletes"]=",".join(map(str,deletes))
    if token:data["token"]=token
    async with httpx.AsyncClient(timeout=60) as c:
        r=await c.post(layer_url.rstrip("/")+"/applyEdits",data=data);r.raise_for_status();return r.json()

async def seequent_discovery(access_token:str,services:list[str]|None=None)->dict:
    services=services or ["geoscienceobject","blockmodel","file"]
    params=[("service",s) for s in services]
    async with httpx.AsyncClient(timeout=30) as c:
        r=await c.get("https://discover.api.seequent.com/evo/identity/v2/discovery",params=params,headers={"Authorization":f"Bearer {access_token}"})
        r.raise_for_status();return r.json()

async def seequent_request(url:str,access_token:str,method:str="GET",payload:dict|None=None)->dict:
    async with httpx.AsyncClient(timeout=90) as c:
        r=await c.request(method,url,headers={"Authorization":f"Bearer {access_token}","Accept":"application/json"},json=payload)
        r.raise_for_status()
        if not r.content:return {"status":r.status_code}
        return r.json()

async def ogc_features(base_url:str,collection:str|None=None,limit:int=1000)->dict:
    url=base_url.rstrip("/")
    if collection:url+=f"/collections/{collection}/items"
    async with httpx.AsyncClient(timeout=45) as c:
        r=await c.get(url,params={"f":"json","limit":limit});r.raise_for_status();return r.json()

def integration_catalog()->dict:
    return {
      "esri_arcgis":{"mode":"rest","auth":["oauth2","api_key","access_token"],"capabilities":["portal","feature_service_query","feature_service_edits","attachments","sync","maps","scene_services"]},
      "seequent_evo":{"mode":"rest","auth":["oauth2_access_token"],"capabilities":["discovery","workspaces","files","geoscience_objects","block_models","geostatistics_tasks","geophysics_tasks","geotechnical_tasks","imago"]},
      "archicad":{"mode":"local_bridge","auth":["bridge_token"],"capabilities":["automation_http_json","elements","properties","classifications","3d","ifc","selection","commands"],"requires_desktop":True},
      "micromine_origin":{"mode":"local_bridge","auth":["bridge_token"],"capabilities":["mmpy","block_models","files","commands","vizex","scripts"],"requires_desktop":True},
      "micromine_nexus":{"mode":"managed_connector","auth":["tenant_auth"],"capabilities":["files","versioning","remote_layers","wireframes","strings","alastri_triangulations"]},
      "ogc_api_features":{"mode":"rest","auth":["none","bearer"],"capabilities":["collections","features","geojson"]},
      "geoserver":{"mode":"rest","auth":["basic","bearer"],"capabilities":["wfs","wms","wmts","rest_config"]},
      "qgis":{"mode":"file_and_service","auth":["none"],"capabilities":["geopackage","geojson","wfs","wms","postgis"]}
    }
