-- Sentinel AI — AlloyDB (PostgreSQL) transactional schema
-- System of record for users, assets, work orders and audit.

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE users (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username      VARCHAR(64) UNIQUE NOT NULL,
    password_hash VARCHAR(128) NOT NULL,
    role          VARCHAR(16) NOT NULL CHECK (role IN ('admin','commander','responder','hospital','citizen')),
    org           VARCHAR(128),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE districts (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(64) UNIQUE NOT NULL,
    lat         DOUBLE PRECISION NOT NULL,
    lng         DOUBLE PRECISION NOT NULL,
    elevation_m DOUBLE PRECISION NOT NULL,
    population  INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE hospitals (
    id           SERIAL PRIMARY KEY,
    name         VARCHAR(128) UNIQUE NOT NULL,
    district_id  INTEGER NOT NULL REFERENCES districts(id),
    lat          DOUBLE PRECISION NOT NULL,
    lng          DOUBLE PRECISION NOT NULL,
    total_beds   INTEGER NOT NULL,
    icu_beds     INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE ambulances (
    id           SERIAL PRIMARY KEY,
    callsign     VARCHAR(32) UNIQUE NOT NULL,
    hospital_id  INTEGER REFERENCES hospitals(id),
    status       VARCHAR(16) NOT NULL DEFAULT 'available'
                 CHECK (status IN ('available','dispatched','at_scene','transporting','out_of_service')),
    lat          DOUBLE PRECISION,
    lng          DOUBLE PRECISION,
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE incidents (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    firestore_id VARCHAR(32),                 -- link to real-time doc
    type         VARCHAR(16) NOT NULL,
    severity     VARCHAR(16) NOT NULL DEFAULT 'MEDIUM',
    status       VARCHAR(16) NOT NULL DEFAULT 'open'
                 CHECK (status IN ('open','dispatched','on_scene','resolved','closed')),
    district_id  INTEGER REFERENCES districts(id),
    lat          DOUBLE PRECISION,
    lng          DOUBLE PRECISION,
    description  TEXT,
    source       VARCHAR(32) NOT NULL DEFAULT 'manual',
    reporter_id  UUID REFERENCES users(id),
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    resolved_at  TIMESTAMPTZ
);
CREATE INDEX idx_incidents_status ON incidents(status);
CREATE INDEX idx_incidents_created ON incidents(created_at DESC);

CREATE TABLE work_orders (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    incident_id  UUID REFERENCES incidents(id),
    priority     VARCHAR(16) NOT NULL,
    assigned_org VARCHAR(128),
    payload      JSONB NOT NULL DEFAULT '{}'::jsonb,
    status       VARCHAR(16) NOT NULL DEFAULT 'dispatched',
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ
);

CREATE TABLE audit_log (
    id         BIGSERIAL PRIMARY KEY,
    actor      VARCHAR(64) NOT NULL,          -- username or agent name
    action     VARCHAR(64) NOT NULL,
    entity     VARCHAR(64),
    entity_id  VARCHAR(64),
    detail     JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_audit_created ON audit_log(created_at DESC);
