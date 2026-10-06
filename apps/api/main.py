from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from models import SiteAnalysisRequest,GeophysicsRequest,TelemetryRequest,SlopeRiskRequest
from science import analyze_site,interpret_geophysics,evaluate_telemetry,slope_screening
from scientific_routes import router as scientific_router
from cad_routes import router as cad_router
from admin_routes import router as admin_router
from platform_routes import router as platform_router
from integration_routes import router as integration_router
from standards_routes import router as standards_router
from operations_routes import router as operations_router
from production_routes import router as production_router
from nonlinear_routes import router as nonlinear_router
from db import init_db
from rate_limit import RateLimitMiddleware

@asynccontextmanager
async def lifespan(app:FastAPI):
    try: await init_db()
    except Exception as exc: print(f"GeoTect DB initialization warning: {exc}")
    yield

app=FastAPI(title="GeoTect API",version="0.6.0",description="Computational 3D geotechnical CAD, Earth digital twin and secure administration API.",lifespan=lifespan)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_credentials=False,allow_methods=["*"],allow_headers=["*"])
app.include_router(scientific_router);app.include_router(cad_router);app.include_router(admin_router);app.include_router(platform_router);app.include_router(integration_router);app.include_router(standards_router);app.include_router(operations_router);app.include_router(production_router);app.include_router(nonlinear_router)

@app.get("/health")
def health(): return {"status":"ok","service":"geotect-api","version":"0.6.0"}

@app.get("/api/v1/capabilities")
def capabilities():
 return {"cad":["draw_edit","fault","stratum","borehole","road","foundation","tunnel","excavation","section","measurement","undo_redo","versioning","clipping"],
 "terrain":["geotiff_mesh","las_laz_tiling"],"geophysics":["ert_inversion","seismic_volume","gpr","gravity","magnetics","ip","segy"],
 "iot":["mqtt","lorawan","modbus","opcua"],"models":["groundwater_pde","insar","lem","linear_elastic_fem","infrastructure_failure"],
 "persistence":["postgis","timescaledb","project_versions"],
 "admin":["firebase_verified_auth","rbac","encrypted_api_keys","model_registry","system_settings","audit_log"],
 "platform":["organizations","asset_health","workflows","4d_events","compute_jobs","plugins","copilot","investigation_optimization","design_tools","reports","interop","emergency","esg","mine","construction","corridor"],
 "integrations":["esri_arcgis","seequent_evo","archicad_bridge","micromine_bridge","micromine_nexus","autodesk_aps","civil3d","revit","bentley_itwin","openground","trimble_connect","datamine_studio","deswik","maptek","plaxis","geostudio","modflow_flopy","ogc_api_features","geoserver","qgis"],
 "standards":["diggs_3","ags_crosswalk","ifc_4_3_geotechnical","ids","stac","sensorthings","bcf","opencde","geoparquet","zarr","copc","e57"],
 "advanced_engineering":["mohr_coulomb","hoek_brown","hardening_soil","cam_clay","hydro_mechanical","transient_groundwater","unsaturated","consolidation","newmark","rock_mechanics","tailings","inverse_velocity","pile_groups"],
 "field":["pwa_offline","gnss","speech_notes","camera_media","bluetooth","samples","chain_of_custody","calibration"],
 "enterprise":["saml_config","oidc","scim","data_residency","cmek_refs","rate_limits","retention","marketplace"]}

@app.post("/api/v1/sites/analyze")
def site_analyze(request:SiteAnalysisRequest): return analyze_site(request)
@app.post("/api/v1/geophysics/interpret")
def geophysics_interpret(request:GeophysicsRequest): return interpret_geophysics(request)
@app.post("/api/v1/telemetry/evaluate")
def telemetry_evaluate(request:TelemetryRequest): return evaluate_telemetry(request)
@app.post("/api/v1/risk/slope")
def slope_risk(request:SlopeRiskRequest): return slope_screening(request)
