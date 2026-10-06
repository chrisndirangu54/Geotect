from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field

Confidence = float

class Provenance(BaseModel):
    source: str
    observed_at: Optional[datetime] = None
    method: str = "field"
    confidence: Confidence = Field(ge=0.0, le=1.0, default=1.0)

class Terrain(BaseModel):
    mean_elevation_m: float
    slope_deg: float = Field(ge=0.0, le=90.0)
    aspect_deg: Optional[float] = Field(default=None, ge=0.0, lt=360.0)
    rainfall_24h_mm: float = Field(default=0.0, ge=0.0)

class Material(BaseModel):
    name: str
    material_type: Literal["soil", "rock", "fill", "unknown"]
    porosity: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    friction_angle_deg: Optional[float] = Field(default=None, ge=0.0, le=60.0)
    cohesion_kpa: Optional[float] = Field(default=None, ge=0.0)
    unit_weight_kn_m3: Optional[float] = Field(default=None, gt=0.0)
    permeability_m_s: Optional[float] = Field(default=None, ge=0.0)
    confidence: Confidence = Field(default=0.7, ge=0.0, le=1.0)

class SensorReading(BaseModel):
    sensor_id: str
    sensor_type: Literal["piezometer", "inclinometer", "gnss", "strain", "seepage", "weather", "other"]
    value: float
    unit: str
    observed_at: datetime
    warning_threshold: Optional[float] = None
    critical_threshold: Optional[float] = None
    provenance: Provenance

class SiteAnalysisRequest(BaseModel):
    site_id: str
    terrain: Terrain
    materials: list[Material] = []
    sensors: list[SensorReading] = []
    infrastructure_type: Optional[str] = None
    esg_sensitivity: float = Field(default=0.5, ge=0.0, le=1.0)

class GeophysicalObservation(BaseModel):
    method: Literal["ert", "seismic", "gpr", "gravity", "magnetics", "ip"]
    value: float
    unit: str
    depth_m: Optional[float] = Field(default=None, ge=0.0)
    provenance: Provenance

class GeophysicsRequest(BaseModel):
    site_id: str
    observations: list[GeophysicalObservation]

class TelemetryRequest(BaseModel):
    site_id: str
    readings: list[SensorReading]

class SlopeRiskRequest(BaseModel):
    slope_deg: float = Field(ge=0.0, le=90.0)
    friction_angle_deg: float = Field(gt=0.0, le=60.0)
    cohesion_kpa: float = Field(default=0.0, ge=0.0)
    unit_weight_kn_m3: float = Field(default=18.0, gt=0.0)
    failure_depth_m: float = Field(default=2.0, gt=0.0)
    saturation: float = Field(default=0.0, ge=0.0, le=1.0)
    rainfall_24h_mm: float = Field(default=0.0, ge=0.0)
