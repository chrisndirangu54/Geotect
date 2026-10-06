from __future__ import annotations
import httpx

async def bearer_request(url:str,token:str|None=None,method:str="GET",payload:dict|None=None,params:dict|None=None,headers:dict|None=None,timeout:float=90)->dict:
    h={"Accept":"application/json",**(headers or {})}
    if token:h["Authorization"]=f"Bearer {token}"
    async with httpx.AsyncClient(timeout=timeout) as c:
        r=await c.request(method,url,headers=h,json=payload,params=params)
        r.raise_for_status()
        if not r.content:return {"status":r.status_code}
        try:return r.json()
        except Exception:return {"status":r.status_code,"text":r.text[:5000]}

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
    data={"f":"json"};import json
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
    return await bearer_request(url,access_token,method,payload)

async def ogc_features(base_url:str,collection:str|None=None,limit:int=1000)->dict:
    url=base_url.rstrip("/")
    if collection:url+=f"/collections/{collection}/items"
    async with httpx.AsyncClient(timeout=45) as c:
        r=await c.get(url,params={"f":"json","limit":limit});r.raise_for_status();return r.json()

async def autodesk_request(path:str,token:str,method:str="GET",payload:dict|None=None,params:dict|None=None)->dict:
    url="https://developer.api.autodesk.com/"+path.lstrip("/")
    return await bearer_request(url,token,method,payload,params)

async def bentley_request(path:str,token:str,method:str="GET",payload:dict|None=None,params:dict|None=None)->dict:
    url="https://api.bentley.com/"+path.lstrip("/")
    headers={"Accept":"application/vnd.bentley.itwin-platform.v1+json"}
    return await bearer_request(url,token,method,payload,params,headers)

async def trimble_request(base_url:str,path:str,token:str,method:str="GET",payload:dict|None=None,params:dict|None=None)->dict:
    url=base_url.rstrip("/")+"/"+path.lstrip("/")
    return await bearer_request(url,token,method,payload,params)

def integration_catalog()->dict:
    return {
      "esri_arcgis":{"mode":"rest","auth":["oauth2","api_key","access_token"],"capabilities":["portal","feature_service_query","feature_service_edits","attachments","sync","maps","scene_services"]},
      "seequent_evo":{"mode":"rest","auth":["oauth2_access_token"],"capabilities":["discovery","workspaces","files","geoscience_objects","block_models","geostatistics_tasks","geophysics_tasks","geotechnical_tasks","imago"]},
      "archicad":{"mode":"local_bridge","auth":["bridge_token"],"capabilities":["automation_http_json","elements","properties","classifications","3d","ifc","selection","commands"],"requires_desktop":True},
      "micromine_origin":{"mode":"local_bridge","auth":["bridge_token"],"capabilities":["mmpy","block_models","files","commands","vizex","scripts"],"requires_desktop":True},
      "micromine_nexus":{"mode":"managed_connector","auth":["tenant_auth"],"capabilities":["files","versioning","remote_layers","wireframes","strings","alastri_triangulations"]},
      "autodesk_aps":{"mode":"rest","auth":["oauth2_access_token"],"capabilities":["acc_projects","data_management","model_derivative","viewer","webhooks","revit_cloud_workflows","civil3d_cloud_workflows"]},
      "civil3d":{"mode":"local_bridge","auth":["bridge_token"],"capabilities":["dotnet_api","alignments","surfaces","corridors","profiles","cogo_points","landxml","dwg"],"requires_desktop":True},
      "revit":{"mode":"local_bridge","auth":["bridge_token"],"capabilities":["dotnet_api","elements","parameters","families","views","ifc","cloud_models"],"requires_desktop":True},
      "bentley_itwin":{"mode":"rest","auth":["oauth2_access_token"],"capabilities":["itwins","repositories","synchronization","exports","reality_data","issues","visualization","workflows"]},
      "openground":{"mode":"rest_via_itwin","auth":["oauth2_access_token"],"capabilities":["itwin_repository","subsurface_repository","documents","components","project_links"]},
      "trimble_connect":{"mode":"rest","auth":["oauth2_access_token"],"capabilities":["regions","projects","files","folders","models","bcf_topics","comments","views"]},
      "datamine_studio":{"mode":"local_bridge","auth":["bridge_token"],"capabilities":["com_automation","commands","macros","files","block_models"],"requires_desktop":True},
      "deswik":{"mode":"managed_or_file","auth":["customer_api_if_available"],"capabilities":["industry_formats","block_models","grid_models","gis","databases","mdm_exchange","planning_exchange"]},
      "maptek":{"mode":"local_bridge","auth":["bridge_token"],"capabilities":["python_sdk","project_objects","surfaces","drillholes","scans","import_export","workflows"],"requires_desktop":True},
      "maptek_vulcan":{"mode":"local_bridge","auth":["bridge_token"],"capabilities":["vulcan_python_sdk","block_models","triangulations","grids","databases","layers"],"requires_desktop":True},
      "plaxis":{"mode":"local_bridge","auth":["bridge_token","plaxis_remote_password"],"capabilities":["remote_scripting","input","output","soiltest","phases","calculate","results"],"requires_desktop":True},
      "geostudio":{"mode":"file_and_local_api","auth":["bridge_token_if_api_enabled"],"capabilities":["project_exchange","plaxis_2d_exchange","slope_stability","seepage","finite_element_workflows"],"requires_desktop":True},
      "modflow_flopy":{"mode":"native","auth":["none"],"capabilities":["mf6_create","write","run","load","groundwater_flow","transport","package_exchange"]},
      "ogc_api_features":{"mode":"rest","auth":["none","bearer"],"capabilities":["collections","features","geojson"]},
      "geoserver":{"mode":"rest","auth":["basic","bearer"],"capabilities":["wfs","wms","wmts","rest_config"]},
      "qgis":{"mode":"file_and_service","auth":["none"],"capabilities":["geopackage","geojson","wfs","wms","postgis"]}
    }
