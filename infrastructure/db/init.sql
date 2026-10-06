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

CREATE TABLE IF NOT EXISTS projects (
  id text PRIMARY KEY,
  name text NOT NULL,
  crs text NOT NULL DEFAULT 'EPSG:4326',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS project_versions (
  project_id text NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  version integer NOT NULL,
  message text NOT NULL DEFAULT '',
  author text NOT NULL DEFAULT 'local-user',
  scene jsonb NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY(project_id,version)
);
