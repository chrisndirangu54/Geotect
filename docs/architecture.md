# GeoTect architecture

GeoTect treats a project as a **4D state model** rather than a static CAD drawing.

## State layers

- **Measured** — observations directly produced by instruments, field logging or validated datasets.
- **Interpreted** — geological/geotechnical meaning assigned to observations.
- **Predicted** — model outputs, interpolations, forecasts and scenario simulations.

Every interpreted or predicted entity must retain links to its source observations, model/version, timestamp and confidence.

## Planned persistence

- PostgreSQL + PostGIS for projects, geometry and scientific metadata.
- TimescaleDB or equivalent hypertables for high-frequency telemetry.
- Object storage for GeoTIFF, LAS/LAZ, SEG-Y, GLB/3D Tiles and large rasters.
- Redis/message broker for event-driven ingestion and model execution.

## Instrument adapters

Adapters normalize vendor-specific protocols into the GeoTect telemetry contract:

```text
field instrument
  -> MQTT / LoRaWAN / Modbus / OPC-UA / HTTP
  -> adapter
  -> normalized SensorReading
  -> quality checks
  -> temporal store
  -> risk engine / digital twin
```

## Safety boundary

Automated output is advisory until reviewed according to project governance. No AI-generated lithological boundary, failure surface or engineering recommendation becomes verified engineering data without an explicit review state transition.
