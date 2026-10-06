from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from models import SiteAnalysisRequest,GeophysicsRequest,TelemetryRequest,SlopeRiskRequest
from science import analyze_site,interpret_geophysics,evaluate_telemetry,slope_screening
from scientific_routes import router as scientific_router
from cad_routes import router as cad_router
from admin_routes import router as admin_router
from db import init_db

@asynccontextmanager
async def lifespan(app:FastAPI):
    try: await init_db()
    except Exception as exc: print(f"GeoTect DB initialization warning: {exc}")
    yield

app=FastAPI(title="GeoTect API",version="0.4.0",description="Computational 3D geotechnical CAD, Earth digital twin and secure administration API.",lifespan=lifespan)
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_credentials=False,allow_methods=["*"],allow_headers=["*"])
app.include_router(scientific_router);app.include_router(cad_router);app.include_router(admin_router)

@app.get("/health")
def health(): return {"status":"ok","service":"geotect-api","version":"0.4.0"}

@app.get("/api/v1/capabilities")
def capabilities():
 return {"cad":["draw_edit","fault","stratum","borehole","road","foundation","tunnel","excavation","section","measurement","undo_redo","versioning","clipping"],
 "terrain":["geotiff_mesh","las_laz_tiling"],"geophysics":["ert_inversion","seismic_volume","gpr","gravity","magnetics","ip","segy"],
 "iot":["mqtt","lorawan","modbus","opcua"],"models":["groundwater_pde","insar","lem","linear_elastic_fem","infrastructure_failure"],
 "persistence":["postgis","timescaledb","project_versions"],
 "admin":["firebase_verified_auth","rbac","encrypted_api_keys","model_registry","system_settings","audit_log"]}

@app.post("/api/v1/sites/analyze")
def site_analyze(request:SiteAnalysisRequest): return analyze_site(request)
@app.post("/api/v1/geophysics/interpret")
def geophysics_interpret(request:GeophysicsRequest): return interpret_geophysics(request)
@app.post("/api/v1/telemetry/evaluate")
def telemetry_evaluate(request:TelemetryRequest): return evaluate_telemetry(request)
@app.post("/api/v1/risk/slope")
def slope_risk(request:SlopeRiskRequest): return slope_screening(request)
