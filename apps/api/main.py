from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from models import SiteAnalysisRequest,GeophysicsRequest,TelemetryRequest,SlopeRiskRequest
from science import analyze_site,interpret_geophysics,evaluate_telemetry,slope_screening
from scientific_routes import router as scientific_router

app=FastAPI(title="GeoTect API",version="0.2.0",description="3D geotechnical CAD, geoscience, IoT and uncertainty-aware digital-twin API.")
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_credentials=False,allow_methods=["*"],allow_headers=["*"])
app.include_router(scientific_router)

@app.get("/health")
def health(): return {"status":"ok","service":"geotect-api","version":"0.2.0"}

@app.get("/api/v1/capabilities")
def capabilities():
 return {
  "cad":["cesium_3d_scene","boreholes","geological_bodies","geophysics_volumes","infrastructure_geometry"],
  "terrain":["geotiff","dem","elevation","slope","aspect","las_laz"],
  "geophysics":["ert","seismic","gpr","gravity","magnetics","ip","segy"],
  "geotechnical":["borehole","spt","cpt","soil_properties","rock_mass"],
  "iot":["mqtt","lorawan","modbus","opcua","piezometer","inclinometer","gnss","strain","seepage","weather"],
  "models":["uncertainty","darcy_groundwater","insar_velocity","lem_screening","infrastructure_failure_graph"],
  "persistence":["postgis","timescaledb"],
  "fem":{"status":"external_adapter_required","fake_solver":False}
 }

@app.post("/api/v1/sites/analyze")
def site_analyze(request:SiteAnalysisRequest): return analyze_site(request)

@app.post("/api/v1/geophysics/interpret")
def geophysics_interpret(request:GeophysicsRequest): return interpret_geophysics(request)

@app.post("/api/v1/telemetry/evaluate")
def telemetry_evaluate(request:TelemetryRequest): return evaluate_telemetry(request)

@app.post("/api/v1/risk/slope")
def slope_risk(request:SlopeRiskRequest): return slope_screening(request)
