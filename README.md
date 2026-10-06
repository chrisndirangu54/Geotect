# GeoTect

GeoTect is a **computational 3D geotechnical CAD, Earth digital twin and ground-engineering operating system**.

It combines editable 3D subsurface geometry, terrain, boreholes, geology, geophysics, IoT, numerical modelling, monitoring, enterprise workflows and domain-specific engineering modules in one coordinate-aware platform.

## Current platform scope

### 3D geotechnical CAD
- Cesium WebGL workspace
- editable faults, strata, boreholes, roads, foundations, tunnels, excavations and section traces
- terrain/depth picking and snapping
- extrusion, clipping, measurement
- undo/redo
- geological fence sections
- borehole-correlation suggestions
- project version history

### Scientific data
- GeoTIFF DEM -> 3D terrain
- LAS/LAZ ingestion and tiling
- SEG-Y inspection
- ERT inversion
- seismic volume reconstruction
- MASW interpretation baseline
- gravity/magnetic linear potential-field inversion
- InSAR trend analysis
- raster/NDVI/point-cloud change detection
- uncertainty and probabilistic modelling

### Numerical engineering
- groundwater PDE
- Darcy flow
- 2D linear-elastic FEM
- slope/LEM screening
- Monte Carlo probability-of-failure screening
- bearing capacity
- elastic settlement
- retaining-wall earth pressure
- pile capacity
- liquefaction screening
- cut/fill volumes
- mine bench geometry
- tunnel convergence

### Investigation intelligence
- uncertainty-aware investigation-location ranking
- borehole/CPT/geophysics/sensor method recommendations
- natural-language CAD command planning
- risk-change explanations

### Live digital twin
- MQTT
- LoRaWAN
- Modbus
- OPC-UA
- TimescaleDB telemetry
- asset health scoring
- 4D event history
- automated risk rules
- emergency events
- offline edge gateway and buffered alarms

### Enterprise
- Firebase authentication
- RBAC and super-admin control plane
- encrypted API credentials
- model/provider registry
- organizations and memberships
- engineering approval workflows
- audit logs
- client portal layer filtering
- usage metering and quota logic
- plugin registry
- compute-job queue and worker
- read-only client views

### Domain templates
- tailings dams
- highways / road cuts
- foundations
- open-pit mining
- underground mining
- tunnels
- infrastructure corridors
- ESG/environment
- emergency response

### Reports and interoperability
- engineering report data packages
- borehole logs
- GeoJSON
- LandXML
- IFC semantic manifest
- OGC 3D Tiles manifest generation
- webhook notifications
- connector-ready email/SMS/WhatsApp/Slack/Teams notifications

## Quick start

```bash
cp .env.example .env
docker compose up --build
```

Optional services:

```bash
docker compose --profile telemetry up --build
docker compose --profile industrial up --build
docker compose --profile compute up --build
```

Web CAD: `http://localhost:5173`

API/OpenAPI: `http://localhost:8000/docs`

## Vendor interoperability

GeoTect now includes an Integration Hub for:

- Esri ArcGIS Feature Services and ArcGIS REST workflows;
- Seequent Evo geoscience objects, block models, files, workspaces and compute-task APIs;
- Archicad through a secure local Automation API bridge;
- Micromine Origin & Beyond through a secure MMpy bridge;
- Micromine Nexus / Alastri governed data exchange;
- OGC API Features;
- GeoServer;
- QGIS/PostGIS/GeoPackage/GeoJSON workflows.

Desktop integrations use one-time bridge tokens. Cloud credentials remain encrypted in the GeoTect secret vault.

See `docs/vendor-integrations.md`.

## Open standards and governance

GeoTect now supports geotechnical/BIM/Earth-observation interoperability through DIGGS 3.0, AGS crosswalks, IFC 4.3 geotechnical manifests, IDS validation, STAC, SensorThings, BCF/openCDE, GeoParquet, Zarr, COPC and E57 exchange contracts.

The engineering layer also includes constitutive-model screening, hydro-mechanical coupling, transient/unsaturated groundwater, consolidation, seismic Newmark response, rock mechanics, tailings and slope-radar analytics, evidence-aware engineering agents, project risk/assumption registers and immutable released revisions.

The installable Field console supports offline records, GNSS, speech notes, camera/media, Bluetooth discovery, sample chain of custody and instrument calibration.

See `docs/open-standards-and-governance.md`.

## Security

The bootstrap super administrator is configured through:

```text
GEOTECT_SUPER_ADMIN_EMAIL=chrisndirangu54@gmail.com
```

The email itself is **not authentication**. Firebase Admin verifies the user's ID token server-side before GeoTect assigns super-admin privileges.

Provider secrets are encrypted at rest using `GEOTECT_MASTER_KEY` and are never returned to the browser in plaintext.

See `docs/admin-security.md`.

## Platform Hub

The web application now exposes a Platform Hub for:

- AI CAD Copilot
- design calculations
- site-investigation optimization
- mine/construction/ESG/emergency modules
- 4D digital-twin playback
- remote compute jobs
- plugin discovery

See `docs/platform-expansion.md`.

## Engineering fidelity

GeoTect includes real executable baseline numerical methods, but the presence of a calculation does not imply regulator approval or equivalence with every specialist commercial solver.

Each engineering result should preserve its method, assumptions, data state and confidence. Higher-order constitutive behaviour, survey-specific inversion physics, code-specific design checks and signed engineering decisions still require competent validation.
