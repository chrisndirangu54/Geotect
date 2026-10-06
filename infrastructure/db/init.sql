CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS timescaledb;

CREATE TABLE IF NOT EXISTS telemetry_raw (
  sensor_id text NOT NULL,
  observed_at timestamptz NOT NULL,
  value double precision NOT NULL,
  unit text NOT NULL,
  quality double precision NOT NULL DEFAULT 1.0,
  meta jsonb NOT NULL DEFAULT '{}'::jsonb,
  PRIMARY KEY(sensor_id,observed_at)
);
SELECT create_hypertable('telemetry_raw','observed_at',if_not_exists=>TRUE);

CREATE INDEX IF NOT EXISTS telemetry_sensor_time_idx ON telemetry_raw(sensor_id,observed_at DESC);
