from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

def test_slope_screening_returns_factor_of_safety():
    r = client.post("/api/v1/risk/slope", json={
        "slope_deg": 32,
        "friction_angle_deg": 28,
        "cohesion_kpa": 8,
        "unit_weight_kn_m3": 18,
        "failure_depth_m": 3,
        "saturation": 0.7,
        "rainfall_24h_mm": 80
    })
    assert r.status_code == 200
    body = r.json()
    assert "factor_of_safety_screening" in body
    assert 0 <= body["risk_score"] <= 1
