# GeoTect

**GeoTect** is an uncertainty-aware geotechnical and geoscience digital-twin platform that combines terrain, subsurface geology, geophysics, IoT telemetry, climate, infrastructure and ESG context in one engineering workspace.

## MVP

The first release supports a complete data path:

1. ingest terrain / DEM metadata and site context;
2. ingest boreholes and geophysical observations;
3. register IoT sensors and telemetry;
4. fuse observations into a site digital-twin snapshot;
5. compute transparent risk indicators with confidence;
6. visualize the resulting terrain, subsurface layers, sensors and risk state in a React engineering dashboard.

> GeoTect deliberately separates **measured**, **interpreted** and **predicted** information. Inferred geology and risk estimates always carry provenance and confidence rather than being presented as ground truth.

## Architecture

```text
apps/
  web/                  React + TypeScript engineering workspace
  api/                  FastAPI service
packages/
  geotect_core/         shared scientific/domain models
services/
  ingestion/            instrument and file ingestion adapters
  risk/                 transparent baseline risk models
examples/
  site_demo.json        representative site payload
```

## Core data domains

- Terrain: elevation, slope, aspect, DEM/DSM/LiDAR metadata
- Geology: lithology, structures, weathering, stratigraphy
- Geotechnical: boreholes, SPT/CPT, density, porosity, cohesion, friction angle
- Geophysics: ERT, seismic, GPR, gravity, magnetics and IP
- Hydrogeology: groundwater, pore pressure, permeability and drainage
- IoT: piezometers, inclinometers, GNSS, strain, seepage and weather stations
- Climate: rainfall, temperature, evaporation and wind
- Infrastructure: roads, foundations, dams, tunnels, pits and pipelines
- ESG: water, land disturbance, biodiversity, settlements and compliance context
- Risk: slope, flood, subsidence, seismic, erosion and infrastructure-failure indicators

## Quick start

### API

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Open http://localhost:8000/docs.

### Web

```bash
cd apps/web
npm install
npm run dev
```

The UI expects the API at `http://localhost:8000` by default. Override with `VITE_API_URL`.

### Docker

```bash
docker compose up --build
```

## API surface

- `GET /health`
- `GET /api/v1/capabilities`
- `POST /api/v1/sites/analyze`
- `POST /api/v1/geophysics/interpret`
- `POST /api/v1/telemetry/evaluate`
- `POST /api/v1/risk/slope`

The initial numerical models are intentionally transparent screening models, **not substitutes for signed geotechnical design**. Future solver adapters can integrate PLAXIS, OpenSees, FEniCSx, GeoStudio-compatible workflows or other validated numerical engines without changing the core data contract.

## Scientific design principles

1. **Provenance first** — every observation records source, time and quality.
2. **Uncertainty is data** — confidence is stored and propagated.
3. **Time matters** — telemetry and digital-twin state are temporal, not static.
4. **Open adapters** — instruments connect through normalized interfaces (MQTT, LoRaWAN, Modbus, OPC-UA, HTTP).
5. **Physics before decoration** — visual layers must map to defensible measurements, interpretations or calculations.
6. **Human-in-the-loop** — automated geological interpretation is reviewable and cannot silently become "verified geology".

## Roadmap

- CesiumJS / deck.gl 3D terrain and subsurface volumes
- GeoTIFF, LAS/LAZ, GeoJSON, SEG-Y and common borehole formats
- PostGIS + TimescaleDB persistence
- MQTT/LoRaWAN/Modbus/OPC-UA gateways
- kriging / Gaussian-process uncertainty volumes
- rainfall-infiltration and pore-pressure coupling
- limit-equilibrium and FEM slope adapters
- InSAR deformation ingestion
- groundwater flow
- 4D construction/mining history
- ESG impact accounting and auditable compliance trails
- role-based project collaboration and engineering approvals

## Status

GeoTect is currently an early engineering MVP scaffold. Interfaces marked as models or screening calculations should be validated against field data and jurisdiction-specific engineering standards before safety-critical use.
