from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from models import SiteAnalysisRequest, GeophysicsRequest, TelemetryRequest, SlopeRiskRequest
from science import analyze_site, interpret_geophysics, evaluate_telemetry, slope_screening

app = FastAPI(
    title="GeoTect API",
    version="0.1.0",
    description="Geoscience, geotechnical, IoT and uncertainty-aware digital-twin API.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok", "service": "geotect-api", "version": "0.1.0"}

@app.get("/api/v1/capabilities")
def capabilities():
    return {
        "terrain": ["elevation", "slope", "aspect", "dem"],
        "geophysics": ["ert", "seismic", "gpr", "gravity", "magnetics", "ip"],
        "geotechnical": ["borehole", "spt", "cpt", "soil_properties", "rock_mass"],
        "iot": ["piezometer", "inclinometer", "gnss", "strain", "seepage", "weather"],
        "risk": ["slope", "flood", "subsidence", "erosion", "infrastructure_failure"],
        "principles": ["provenance", "uncertainty", "temporal_state", "human_review"],
    }

@app.post("/api/v1/sites/analyze")
def site_analyze(request: SiteAnalysisRequest):
    return analyze_site(request)

@app.post("/api/v1/geophysics/interpret")
def geophysics_interpret(request: GeophysicsRequest):
    return interpret_geophysics(request)

@app.post("/api/v1/telemetry/evaluate")
def telemetry_evaluate(request: TelemetryRequest):
    return evaluate_telemetry(request)

@app.post("/api/v1/risk/slope")
def slope_risk(request: SlopeRiskRequest):
    return slope_screening(request)
