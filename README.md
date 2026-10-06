# GeoTect

**GeoTect is a 3D, data-driven geotechnical CAD and Earth digital-twin platform.** It combines terrain, geology, boreholes, geophysics, IoT telemetry, groundwater, infrastructure, uncertainty and engineering risk in one coordinate-aware workspace.

## What is distinctive now

GeoTect no longer treats CAD as a static drawing. The current architecture makes the spatial model the common interface for field observations, interpretations and simulations.

### Operational in this repository

- **Cesium WebGL 3D CAD workspace** with coordinate-aware boreholes, sensors, geological/geophysical bodies and infrastructure.
- **Actual GeoTIFF DEM → triangulated 3D mesh** upload path. The backend reprojects raster cells to WGS84 and the browser renders the resulting terrain geometry.
- **LAS/LAZ and SEG-Y readers** for scientific-file inspection.
- **PostGIS + TimescaleDB** Docker persistence foundation.
- **MQTT + LoRaWAN ingestion worker** and normalization.
- **Modbus TCP + OPC-UA polling worker** for configured field devices.
- **ERT/seismic/geophysics spatial contract** with provenance and confidence.
- **Uncertainty estimation** with an IDW baseline that exposes confidence/support rather than hiding interpolation uncertainty.
- **Groundwater Darcy-flow screening**.
- **InSAR displacement trend/acceleration analysis**.
- **Infrastructure dependency/failure propagation**.
- **Limit-equilibrium-style slope screening**.
- **FEM adapter contract** that refuses to fabricate results until a validated solver is configured.
- **deck.gl analytical layer builders** for dense sensor/infrastructure overlays and future synchronized section/map views.

## Scientific information states

Every spatial object is one of:

```text
MEASURED    -> direct field/instrument observation
INTERPRETED -> geological/geotechnical interpretation
PREDICTED   -> interpolation, forecast or simulation
```

Confidence and provenance remain attached throughout the pipeline. Predicted geology never silently becomes measured geology.

## Quick start

```bash
docker compose up --build
```

- Web CAD: http://localhost:5173
- API/OpenAPI: http://localhost:8000/docs
- PostgreSQL/PostGIS/TimescaleDB: localhost:5432

Optional MQTT worker:

```bash
docker compose --profile telemetry up --build
```

Optional industrial worker (configure device environment first):

```bash
docker compose --profile industrial up --build
```

## Load a real DEM

Open the web application and choose **Load GeoTIFF DEM**. GeoTect uploads the raster to the API, builds a bounded triangulated mesh, transforms it to EPSG:4326, and renders the actual terrain in Cesium. Large production rasters should later use tiled/streamed terrain instead of browser-scale meshes.

## API groups

```text
/api/v1/workspace/*
/api/v1/datasets/*
/api/v1/geophysics/*
/api/v1/iot/*
/api/v1/telemetry/*
/api/v1/uncertainty/*
/api/v1/groundwater/*
/api/v1/insar/*
/api/v1/infrastructure/*
/api/v1/simulation/*
/api/v1/risk/*
```

## Repository map

```text
apps/
  web/            React + TypeScript + Cesium + deck.gl
  api/            FastAPI scientific/spatial API
services/
  telemetry_worker.py
  industrial_worker.py
infrastructure/
  db/init.sql     PostGIS + TimescaleDB
docs/
  architecture.md
  data-pipeline.md
examples/
```

## What is deliberately not faked

GeoTect is not yet claiming full production inversion, FEM, groundwater PDE solving, point-cloud tiling, SEG-Y voxel rendering or automated engineering sign-off. Interfaces are in place where appropriate, but safety-critical numerical capability should be connected to validated solvers and tested against benchmark/field datasets.

The next engineering depth should focus on: tiled DEM/LAS streaming, ERT/seismic inversion-volume ingestion, borehole fence/section editing, snapping/drafting tools, geological solid construction, kriging/Gaussian-process uncertainty, FEM solver execution, and persisted project/version/review workflows.
