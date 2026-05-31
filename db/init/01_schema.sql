-- db/init/01_schema.sql
-- Telemetry metadata schema. Waveform bytes never enter Postgres (see ADR-005);
-- this DB stores only metadata, file pointers, and per-window labels for
-- query-able access from the agent loop and downstream services.
--
-- Postgres runs every *.sql in /docker-entrypoint-initdb.d on first boot ONLY.
-- To re-apply after edits during development:
--   docker compose down -v && docker compose up -d
-- The -v flag drops the named pgdata volume; do not run on shared state.

CREATE TABLE dataset (
  id                  TEXT        PRIMARY KEY,
  source_doi          TEXT        NOT NULL,
  source_paper_doi    TEXT,
  source_archive      TEXT        NOT NULL,
  source_archive_md5  TEXT        NOT NULL,
  fetched_at          TIMESTAMPTZ NOT NULL,
  manifest_path       TEXT        NOT NULL
);

CREATE TABLE run (
  id              TEXT  PRIMARY KEY,
  dataset_id      TEXT  NOT NULL REFERENCES dataset(id) ON DELETE CASCADE,
  regime          TEXT  NOT NULL,
  n_windows       INT   NOT NULL,
  window_samples  INT   NOT NULL,
  sample_rate_hz  INT   NOT NULL,
  rawspace_path   TEXT  NOT NULL,
  classspace_path TEXT  NOT NULL,
  notes           JSONB,
  UNIQUE (dataset_id, regime)
);

CREATE TABLE window (
  run_id  TEXT NOT NULL REFERENCES run(id) ON DELETE CASCADE,
  idx     INT  NOT NULL,
  label   TEXT NOT NULL,
  PRIMARY KEY (run_id, idx)
);

-- Hot-path query: "windows of class L in run R" (e.g. 100 random keyhole windows in pandiyan/D1).
-- The PK index on (run_id, idx) does not help filter by label.
CREATE INDEX window_run_label_idx ON window (run_id, label);
