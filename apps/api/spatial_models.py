from datetime import datetime, timezone
from typing import Literal
from pydantic import BaseModel, Field

class Point3D(BaseModel):
    lon: float
    lat: float
    elevation_m: float

class BoreholeInterval(BaseModel):
    from_m: float = Field(ge=0)
    to_m: float = Field(gt=0)
    lithology: str
    confidence: float = Field(ge=0,le=1)

class Borehole3D(BaseModel):
    id: str
    collar: Point3D
    total_depth_m: float = Field(gt=0)
    intervals: list[BoreholeInterval]

class Sensor3D(BaseModel):
    id: str
    type: str
    position: Point3D
    status: Literal["normal","warning","critical"] = "normal"
    value: float
    unit: str
    observed_at: datetime

class Infrastructure3D(BaseModel):
    id: str
    type: str
    name: str
    positions: list[Point3D]
    criticality: float = Field(ge=0,le=1)

class GeoBody3D(BaseModel):
    id: str
    name: str
    kind: Literal["geology","ert","seismic","uncertainty","groundwater","insar"]
    state: Literal["measured","interpreted","predicted"]
    confidence: float = Field(ge=0,le=1)
    positions: list[Point3D]
    values: list[float] | None = None

class ScenePayload(BaseModel):
    site_id: str
    crs: str = "EPSG:4326"
    center: Point3D
    boreholes: list[Borehole3D] = []
    sensors: list[Sensor3D] = []
    infrastructure: list[Infrastructure3D] = []
    bodies: list[GeoBody3D] = []

def demo_scene() -> ScenePayload:
    now=datetime.now(timezone.utc)
    c=Point3D(lon=36.8219,lat=-1.2921,elevation_m=1795)
    return ScenePayload(
      site_id="demo-slope-001",center=c,
      boreholes=[
        Borehole3D(id="BH-01",collar=Point3D(lon=36.8178,lat=-1.2910,elevation_m=1788),total_depth_m=55,intervals=[
          BoreholeInterval(from_m=0,to_m=7,lithology="lateritic soil",confidence=.94),
          BoreholeInterval(from_m=7,to_m=25,lithology="weathered basalt",confidence=.82),
          BoreholeInterval(from_m=25,to_m=55,lithology="competent basalt",confidence=.72)]),
        Borehole3D(id="BH-02",collar=Point3D(lon=36.8244,lat=-1.2940,elevation_m=1808),total_depth_m=72,intervals=[
          BoreholeInterval(from_m=0,to_m=5,lithology="colluvium",confidence=.91),
          BoreholeInterval(from_m=5,to_m=31,lithology="fractured basalt",confidence=.69),
          BoreholeInterval(from_m=31,to_m=72,lithology="competent basalt",confidence=.76)])
      ],
      sensors=[
        Sensor3D(id="PZ-04",type="piezometer",position=Point3D(lon=36.8232,lat=-1.2902,elevation_m=1797),status="warning",value=18.4,unit="kPa",observed_at=now),
        Sensor3D(id="INC-02",type="inclinometer",position=Point3D(lon=36.8198,lat=-1.2948,elevation_m=1780),status="normal",value=2.1,unit="mm",observed_at=now)
      ],
      infrastructure=[
        Infrastructure3D(id="RD-01",type="road",name="Access road",criticality=.72,positions=[
          Point3D(lon=36.815,lat=-1.295,elevation_m=1772),Point3D(lon=36.821,lat=-1.292,elevation_m=1790),Point3D(lon=36.828,lat=-1.289,elevation_m=1811)])
      ],
      bodies=[
        GeoBody3D(id="GEO-01",name="Weathered basalt",kind="geology",state="interpreted",confidence=.78,positions=[
          Point3D(lon=36.817,lat=-1.290,elevation_m=1760),Point3D(lon=36.826,lat=-1.290,elevation_m=1762),Point3D(lon=36.827,lat=-1.296,elevation_m=1750),Point3D(lon=36.818,lat=-1.296,elevation_m=1754)]),
        GeoBody3D(id="ERT-01",name="Conductive ERT anomaly",kind="ert",state="interpreted",confidence=.66,positions=[
          Point3D(lon=36.819,lat=-1.291,elevation_m=1740),Point3D(lon=36.824,lat=-1.291,elevation_m=1742),Point3D(lon=36.824,lat=-1.294,elevation_m=1735),Point3D(lon=36.819,lat=-1.294,elevation_m=1737)],values=[48,52,39,44]),
        GeoBody3D(id="UNC-01",name="Low-control subsurface",kind="uncertainty",state="predicted",confidence=.42,positions=[
          Point3D(lon=36.825,lat=-1.289,elevation_m=1720),Point3D(lon=36.830,lat=-1.289,elevation_m=1720),Point3D(lon=36.830,lat=-1.295,elevation_m=1712),Point3D(lon=36.825,lat=-1.295,elevation_m=1712)])
      ])
