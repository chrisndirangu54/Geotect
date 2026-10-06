import math
from statistics import mean
from models import SiteAnalysisRequest, GeophysicsRequest, TelemetryRequest, SlopeRiskRequest

def _band(score: float) -> str:
    if score < 0.25: return "low"
    if score < 0.50: return "moderate"
    if score < 0.75: return "high"
    return "critical"

def slope_screening(r: SlopeRiskRequest):
    beta = math.radians(max(r.slope_deg, 0.1))
    phi = math.radians(r.friction_angle_deg)
    normal_stress = r.unit_weight_kn_m3 * r.failure_depth_m * math.cos(beta) ** 2
    pore_pressure = r.saturation * normal_stress * min(1.0, 0.35 + r.rainfall_24h_mm / 200.0)
    effective_normal = max(normal_stress - pore_pressure, 0.01)
    resisting = r.cohesion_kpa + effective_normal * math.tan(phi)
    driving = max(r.unit_weight_kn_m3 * r.failure_depth_m * math.sin(beta) * math.cos(beta), 0.01)
    factor_of_safety = resisting / driving
    risk = max(0.0, min(1.0, (1.5 - factor_of_safety) / 1.0))
    return {
        "factor_of_safety_screening": round(factor_of_safety, 3),
        "risk_score": round(risk, 3),
        "risk_band": _band(risk),
        "assumptions": [
            "infinite-slope style screening approximation",
            "homogeneous material",
            "screening only; not a signed geotechnical design",
        ],
    }

def evaluate_telemetry(r: TelemetryRequest):
    alerts = []
    health_scores = []
    for x in r.readings:
        status = "normal"
        score = 0.0
        if x.critical_threshold is not None and x.value >= x.critical_threshold:
            status, score = "critical", 1.0
        elif x.warning_threshold is not None and x.value >= x.warning_threshold:
            status, score = "warning", 0.6
        health_scores.append(score)
        if status != "normal":
            alerts.append({"sensor_id": x.sensor_id, "status": status, "value": x.value, "unit": x.unit})
    aggregate = mean(health_scores) if health_scores else 0.0
    return {"site_id": r.site_id, "telemetry_risk": round(aggregate, 3), "alerts": alerts}

def interpret_geophysics(r: GeophysicsRequest):
    interpretations = []
    for obs in r.observations:
        if obs.method == "ert":
            label = "conductive zone" if obs.value < 100 else "resistive zone"
        elif obs.method == "seismic":
            label = "lower-velocity material" if obs.value < 1500 else "competent/high-velocity material"
        elif obs.method == "gpr":
            label = "reflector/anomaly requiring spatial interpretation"
        else:
            label = "geophysical anomaly requiring joint inversion/context"
        interpretations.append({
            "method": obs.method,
            "depth_m": obs.depth_m,
            "interpretation": label,
            "confidence": round(obs.provenance.confidence * 0.75, 2),
            "status": "interpreted_not_verified",
        })
    return {"site_id": r.site_id, "interpretations": interpretations}

def analyze_site(r: SiteAnalysisRequest):
    terrain_score = min(1.0, r.terrain.slope_deg / 45.0) * 0.45
    rainfall_score = min(1.0, r.terrain.rainfall_24h_mm / 150.0) * 0.20
    uncertainty = 0.5 if not r.materials else 1.0 - mean(m.confidence for m in r.materials)
    uncertainty_score = uncertainty * 0.20
    telemetry = evaluate_telemetry(TelemetryRequest(site_id=r.site_id, readings=r.sensors))
    telemetry_score = telemetry["telemetry_risk"] * 0.10
    esg_score = r.esg_sensitivity * 0.05
    total = min(1.0, terrain_score + rainfall_score + uncertainty_score + telemetry_score + esg_score)
    return {
        "site_id": r.site_id,
        "risk_score": round(total, 3),
        "risk_band": _band(total),
        "uncertainty_score": round(uncertainty, 3),
        "telemetry": telemetry,
        "drivers": {
            "terrain": round(terrain_score, 3),
            "rainfall": round(rainfall_score, 3),
            "model_uncertainty": round(uncertainty_score, 3),
            "telemetry": round(telemetry_score, 3),
            "esg_sensitivity": round(esg_score, 3),
        },
        "status": "screening_model",
    }
