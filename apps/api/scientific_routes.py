from pathlib import Path
from tempfile import NamedTemporaryFile
from fastapi import APIRouter,UploadFile,File,HTTPException
from spatial_models import demo_scene
from readers import inspect_dataset
from terrain_mesh import geotiff_to_mesh
from uncertainty import idw_with_uncertainty
from hydro import darcy_flux
from insar import analyze_displacement
from infrastructure_risk import propagate_failures
from simulation import limit_equilibrium_screening,fem_capabilities
from iot_adapters import parse_mqtt,parse_lorawan,parse_modbus,parse_opcua,SUPPORTED_PROTOCOLS

router=APIRouter(prefix="/api/v1")

@router.get("/workspace/demo")
def workspace_demo(): return demo_scene()

async def _temp_upload(file:UploadFile,allowed:set[str]):
    suffix=Path(file.filename or "").suffix.lower()
    if suffix not in allowed: raise HTTPException(400,f"Unsupported extension {suffix}")
    tmp=NamedTemporaryFile(suffix=suffix,delete=False)
    try:
        while chunk:=await file.read(1024*1024): tmp.write(chunk)
        tmp.flush();return tmp.name
    finally: tmp.close()

@router.post("/datasets/inspect")
async def dataset_inspect(file:UploadFile=File(...)):
    import os
    path=await _temp_upload(file,{".tif",".tiff",".las",".laz",".sgy",".segy"})
    try:return inspect_dataset(path)
    except Exception as e: raise HTTPException(422,str(e))
    finally: os.unlink(path)

@router.post("/datasets/geotiff/mesh")
async def geotiff_mesh(file:UploadFile=File(...),max_side:int=128):
    import os
    path=await _temp_upload(file,{".tif",".tiff"})
    try:return geotiff_to_mesh(path,max(16,min(max_side,256)))
    except Exception as e: raise HTTPException(422,str(e))
    finally: os.unlink(path)

@router.post("/uncertainty/idw")
def uncertainty(payload:dict):
    samples=[(float(x["x"]),float(x["y"]),float(x["value"])) for x in payload.get("samples",[])]
    return idw_with_uncertainty(samples,float(payload["x"]),float(payload["y"]),float(payload.get("power",2)))

@router.post("/groundwater/darcy")
def groundwater(payload:dict):
    return darcy_flux(float(payload["permeability_m_s"]),float(payload["head_up_m"]),float(payload["head_down_m"]),float(payload["length_m"]),float(payload.get("area_m2",1)))

@router.post("/insar/analyze")
def insar(payload:dict): return analyze_displacement(payload.get("series",[]))

@router.post("/infrastructure/propagate-failure")
def infrastructure(payload:dict): return propagate_failures(payload.get("nodes",[]),payload.get("edges",[]),payload.get("failed_ids",[]))

@router.post("/simulation/lem")
def lem(payload:dict): return limit_equilibrium_screening(float(payload["slope_deg"]),float(payload["friction_deg"]),float(payload.get("cohesion_kpa",0)),float(payload.get("gamma_kn_m3",18)),float(payload.get("height_m",3)),float(payload.get("pore_pressure_ratio",0)))

@router.get("/simulation/fem")
def fem(): return fem_capabilities()

@router.get("/iot/protocols")
def protocols(): return SUPPORTED_PROTOCOLS

@router.post("/iot/normalize/{protocol}")
def normalize(protocol:str,payload:dict):
    if protocol=="mqtt": return parse_mqtt(str(payload.get("topic","geotect/sensor")),payload)
    if protocol=="lorawan": return parse_lorawan(payload)
    if protocol=="modbus": return parse_modbus(str(payload["sensor_id"]),float(payload["register_value"]),float(payload.get("scale",1)),str(payload.get("unit","")),str(payload.get("sensor_type","other")))
    if protocol=="opcua": return parse_opcua(str(payload["node_id"]),float(payload["value"]),str(payload.get("unit","")),str(payload.get("sensor_type","other")))
    raise HTTPException(404,"Unsupported protocol")
