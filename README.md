# GeoTect

**GeoTect is a computational 3D geotechnical CAD and Earth digital-twin platform.** It combines terrain, boreholes, geology, geophysics, IoT telemetry, groundwater, infrastructure, uncertainty and numerical engineering models in one editable, coordinate-aware workspace.

## Implemented capabilities

### 3D geotechnical CAD

The React/Cesium workspace is now an authoring environment, not only a viewer.

- draw **faults, strata, boreholes, roads, foundations, tunnels, excavations and section traces**;
- scene/depth-based coordinate picking to snap authored vertices onto visible terrain/geometry;
- polygon extrusion for strata, foundations and excavations;
- 3D distance measurement;
- select authored features and edit name, information state, confidence, elevation and extrusion depth;
- delete features;
- undo/redo history;
- clipping-plane toggle;
- geological fence/section generation from an authored section trace;
- borehole correlation suggestions;
- project save/version history in PostgreSQL;
- latest project version restored in the web client.

### Terrain and point clouds

- GeoTIFF/DEM ingestion with CRS transformation through Rasterio.
- GeoTIFF -> bounded triangulated 3D mesh -> Cesium WebGL rendering.
- LAS/LAZ parsing.
- Automatic spatial LAS/LAZ tiling into compressed point tiles plus `tileset.json`, downloadable as a ZIP.
- deck.gl analytical layer builders for dense overlays.

### Geophysics

- ERT regularized log-resistivity inversion from a supplied survey sensitivity/Jacobian matrix.
- Seismic trace reconstruction into an x-y-depth amplitude volume using IDW interpolation and time-depth conversion.
- SEG-Y inspection through ObsPy.
- Spatial contracts for ERT, seismic, GPR, IP, gravity and magnetics.
- Geological/geophysical bodies carry information state, confidence and provenance rather than being treated as unquestioned ground truth.

### Geological modelling

- closed triangulated geological prism/stratum generation;
- editable/extruded strata in the CAD workspace;
- borehole fence views and correlation suggestions;
- separate **measured**, **interpreted** and **predicted** states.

### Groundwater

- Darcy-flow screening;
- heterogeneous 2D steady-state groundwater PDE solution using finite differences for `div(K grad h)=0`;
- hydraulic head and Darcy flux fields returned to the digital-twin layer.

### Numerical engineering

- slope/limit-equilibrium-style screening;
- executable **2D linear-elastic triangular FEM** using scikit-fem;
- gravity body loading and optional surface pressure;
- nodal displacement output suitable for visualization;
- infrastructure dependency/failure propagation.

### Monitoring and time-domain data

- MQTT;
- LoRaWAN network-server uplinks;
- Modbus TCP;
- OPC-UA;
- PostGIS spatial persistence;
- TimescaleDB telemetry storage;
- InSAR displacement velocity and acceleration flagging.

## CAD workflow

```text
Field / instrument / raster data
            |
            v
     Spatial normalization
   CRS + provenance + time
            |
            v
  PostGIS / TimescaleDB
            |
      +-----+------+
      |            |
 measured      interpreted
      |            |
      +-----+------+
            |
        GeoTect CAD
            |
  draw / edit / correlate
 section / extrude / measure
            |
            v
     versioned project
            |
 +----------+-----------+
 |          |           |
 ERT     groundwater    FEM
 |          |           |
 +----------+-----------+
            |
     predicted outputs
            |
        digital twin
```

## Quick start

```bash
docker compose up --build
```

- GeoTect CAD: http://localhost:5173
- API + OpenAPI: http://localhost:8000/docs
- PostgreSQL/PostGIS/TimescaleDB: localhost:5432

Optional field telemetry:

```bash
docker compose --profile telemetry up --build
docker compose --profile industrial up --build
```

## Major computational endpoints

```text
POST /api/v1/geophysics/ert/invert
POST /api/v1/geophysics/seismic/reconstruct
POST /api/v1/groundwater/pde
POST /api/v1/simulation/fem/elastic
POST /api/v1/simulation/lem
POST /api/v1/datasets/geotiff/mesh
POST /api/v1/datasets/las/tiles
POST /api/v1/cad/solids/extrude
POST /api/v1/cad/sections/fence
POST /api/v1/cad/boreholes/correlate
POST /api/v1/cad/projects
POST /api/v1/cad/projects/{id}/versions
```

## Engineering fidelity

GeoTect now contains **real executable baseline numerical methods**, but "implemented" does not mean every solver is equivalent to a specialist commercial package.

- The ERT inversion core performs regularized inversion when supplied a physically valid sensitivity/Jacobian matrix; full electrode-geometry forward modelling can be supplied by pyGIMLi, SimPEG or validated vendor workflows.
- Seismic reconstruction currently uses spatial trace interpolation and constant-velocity time-depth conversion; migration/tomography should be added for survey-specific production interpretation.
- The groundwater module solves a 2D steady heterogeneous PDE; transient, unsaturated and density-dependent systems require additional equations.
- The FEM module executes small-strain isotropic linear elasticity. Nonlinear soil constitutive laws, staged construction, contact, consolidation and dynamic response require validated extensions.
- Borehole correlations are suggestions and remain unverified until a geologist/geotechnical engineer accepts them.

This boundary is intentional: GeoTect records the method and assumptions rather than presenting a baseline numerical result as a signed engineering design.

## CI

GitHub Actions runs:

- Python API/scientific tests;
- React/TypeScript production build.

See `docs/computational-kernels.md` and `docs/data-pipeline.md` for implementation details.
