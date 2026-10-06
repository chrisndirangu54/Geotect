from pathlib import Path
from tempfile import NamedTemporaryFile,mkdtemp
from fastapi import APIRouter,UploadFile,File,HTTPException,BackgroundTasks
from fastapi.responses import FileResponse
from spatial_models import demo_scene
from readers import inspect_dataset
from terrain_mesh import geotiff_to_mesh
from las_tiler import tile_las
from uncertainty import idw_with_uncertainty
from hydro import darcy_flux
from groundwater_pde import solve_steady_groundwater
from ert_inversion import invert_ert
from seismic_volume import reconstruct_volume
from fem_solver import solve_linear_elasticity
from insar import analyze_displacement
from infrastructure_risk import propagate_failures
from simulation import limit_equilibrium_screening
from iot_adapters import parse_mqtt,parse_lorawan,parse_modbus,parse_opcua,SUPPORTED_PROTOCOLS
import shutil,os

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
    path=await _temp_upload(file,{".tif",".tiff",".las",".laz",".sgy",".segy"})
    try:return inspect_dataset(path)
    except Exception as e: raise HTTPException(422,str(e))
    finally: os.unlink(path)

@router.post("/datasets/geotiff/mesh")
async def geotiff_mesh(file:UploadFile=File(...),max_side:int=128):
    path=await _temp_upload(file,{".tif",".tiff"})
    try:return geotiff_to_mesh(path,max(16,min(max_side,256)))
    except Exception as e: raise HTTPException(422,str(e))
    finally: os.unlink(path)

@router.post("/datasets/las/tiles")
async def las_tiles(background_tasks:BackgroundTasks,file:UploadFile=File(...),max_points_per_tile:int=50000):
    path=await _temp_upload(file,{".las",".laz"});out=mkdtemp(prefix="geotect-tiles-")
    try:
        tile_las(path,out,max_points_per_tile)
        archive=shutil.make_archive(out,"zip",out)
        background_tasks.add_task(lambda: (shutil.rmtree(out,ignore_errors=True),os.path.exists(path) and os.unlink(path),os.path.exists(archive) and os.unlink(archive)))
        return FileResponse(archive,media_type="application/zip",filename="geotect-las-tiles.zip",background=background_tasks)
    except Exception as e:
        shutil.rmtree(out,ignore_errors=True)
        if os.path.exists(path):os.unlink(path)
        raise HTTPException(422,str(e))

@router.post("/geophysics/ert/invert")
def ert(payload:dict):
    try:return invert_ert(payload["sensitivity"],payload["apparent_resistivity"],float(payload.get("regularization",1)),float(payload.get("reference_resistivity",100)),int(payload.get("iterations",6)))
    except Exception as e: raise HTTPException(422,str(e))

@router.post("/geophysics/seismic/reconstruct")
def seismic(payload:dict):
    try:return reconstruct_volume(payload["traces"],int(payload.get("nx",32)),int(payload.get("ny",32)),float(payload.get("velocity_m_s",1800)))
    except Exception as e: raise HTTPException(422,str(e))

@router.post("/uncertainty/idw")
def uncertainty(payload:dict):
    samples=[(float(x["x"]),float(x["y"]),float(x["value"])) for x in payload.get("samples",[])]
    return idw_with_uncertainty(samples,float(payload["x"]),float(payload["y"]),float(payload.get("power",2)))

@router.post("/groundwater/darcy")
def groundwater(payload:dict):
    return darcy_flux(float(payload["permeability_m_s"]),float(payload["head_up_m"]),float(payload["head_down_m"]),float(payload["length_m"]),float(payload.get("area_m2",1)))

@router.post("/groundwater/pde")
def groundwater_pde(payload:dict):
    try:return solve_steady_groundwater(int(payload.get("nx",30)),int(payload.get("ny",20)),float(payload.get("dx_m",5)),float(payload.get("dy_m",5)),payload.get("k",1e-5),float(payload.get("left_head_m",100)),float(payload.get("right_head_m",90)),bool(payload.get("top_no_flow",True)),bool(payload.get("bottom_no_flow",True)),float(payload.get("tolerance",1e-5)),int(payload.get("max_iterations",20000)))
    except Exception as e: raise HTTPException(422,str(e))

@router.post("/simulation/fem/elastic")
def fem(payload:dict):
    try:return solve_linear_elasticity(float(payload.get("width_m",100)),float(payload.get("height_m",50)),int(payload.get("nx",30)),int(payload.get("ny",15)),float(payload["young_pa"]),float(payload["poisson"]),float(payload.get("density_kg_m3",2000)),float(payload.get("gravity_m_s2",9.81)),float(payload.get("top_pressure_pa",0)))
    except Exception as e: raise HTTPException(422,str(e))

@router.post("/insar/analyze")
def insar(payload:dict): return analyze_displacement(payload.get("series",[]))

@router.post("/infrastructure/propagate-failure")
def infrastructure(payload:dict): return propagate_failures(payload.get("nodes",[]),payload.get("edges",[]),payload.get("failed_ids",[]))

@router.post("/simulation/lem")
def lem(payload:dict): return limit_equilibrium_screening(float(payload["slope_deg"]),float(payload["friction_deg"]),float(payload.get("cohesion_kpa",0)),float(payload.get("gamma_kn_m3",18)),float(payload.get("height_m",3)),float(payload.get("pore_pressure_ratio",0)))

@router.get("/iot/protocols")
def protocols(): return SUPPORTED_PROTOCOLS

@router.post("/iot/normalize/{protocol}")
def normalize(protocol:str,payload:dict):
    if protocol=="mqtt": return parse_mqtt(str(payload.get("topic","geotect/sensor")),payload)
    if protocol=="lorawan": return parse_lorawan(payload)
    if protocol=="modbus": return parse_modbus(str(payload["sensor_id"]),float(payload["register_value"]),float(payload.get("scale",1)),str(payload.get("unit","")),str(payload.get("sensor_type","other")))
    if protocol=="opcua": return parse_opcua(str(payload["node_id"]),float(payload["value"]),str(payload.get("unit","")),str(payload.get("sensor_type","other")))
    raise HTTPException(404,"Unsupported protocol")
