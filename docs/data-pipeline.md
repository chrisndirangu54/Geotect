# GeoTect data and simulation pipeline

## Shared spatial contract

Every object that appears in the engineering workspace is coordinate-aware and carries a semantic state:

- **measured**: direct instrument/field observation;
- **interpreted**: geological or engineering interpretation;
- **predicted**: interpolation, forecast or simulation result.

The state is not cosmetic. It controls confidence, provenance and review requirements.

## Terrain

GeoTIFF files can be uploaded to `POST /api/v1/datasets/geotiff/mesh`. Rasterio reads the raster in its native CRS, samples it to a bounded mesh size, reprojects mesh vertices to EPSG:4326, triangulates the grid and returns vertices/indices. The React/Cesium CAD workspace converts those geodetic vertices into Earth-centered Cartesian geometry and renders the actual DEM as a WebGL primitive.

LAS/LAZ and SEG-Y currently have production parsers for metadata/shape inspection. Point-cloud decimation/tiling and seismic voxelization are the next processing step; the API does not pretend they are already volumetric CAD layers.

## Geophysics

ERT/seismic/GPR/gravity/magnetics/IP use a common interpreted-volume contract. Values, provenance and confidence remain attached to the geometry. The current demo supplies a real coordinate-aware ERT body; future inversion workers can replace it without changing the frontend contract.

## Telemetry

`services/telemetry_worker.py` consumes MQTT JSON. ChirpStack-style LoRaWAN uplinks can travel over the same broker and are normalized through the LoRaWAN adapter.

`services/industrial_worker.py` provides deployment-specific polling for Modbus TCP and OPC-UA. These workers are Docker Compose profiles and are intentionally disabled until a real broker/device endpoint is configured.

## Persistence

PostGIS stores 3D spatial objects using SRID 4326. TimescaleDB stores time-series telemetry in a hypertable. Raw files should be stored in object storage and referenced by immutable URI/checksum rather than inserted into relational rows.

## Scientific models

Currently executable:
- transparent slope/LEM screening;
- Darcy groundwater flux screening;
- IDW estimate + support-derived uncertainty;
- InSAR displacement velocity/acceleration flag;
- directed infrastructure dependency/failure propagation.

FEM is an explicit external solver interface. GeoTect will not invent FEM outputs. A validated OpenSees, FEniCSx or commercial solver adapter must be connected before the FEM route can execute analyses.
