-- DIP Database Initialization

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Events table
CREATE TABLE IF NOT EXISTS events (
    event_id VARCHAR(64) PRIMARY KEY,
    event_version VARCHAR(16) NOT NULL DEFAULT '1.0',
    event_type VARCHAR(255) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    source VARCHAR(255) NOT NULL,
    producer VARCHAR(255) NOT NULL,
    tenant_id VARCHAR(64),
    trace_id VARCHAR(64) NOT NULL,
    run_id VARCHAR(64),
    task_id VARCHAR(64),
    agent_id VARCHAR(64),
    session_id VARCHAR(64),
    severity VARCHAR(16) NOT NULL DEFAULT 'info',
    payload JSONB NOT NULL DEFAULT '{}',
    metadata JSONB NOT NULL DEFAULT '{}',
    schema_version VARCHAR(16) NOT NULL DEFAULT '1.0',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_events_event_type ON events (event_type);
CREATE INDEX IF NOT EXISTS idx_events_source ON events (source);
CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events (timestamp);
CREATE INDEX IF NOT EXISTS idx_events_trace_id ON events (trace_id);
CREATE INDEX IF NOT EXISTS idx_events_tenant_id ON events (tenant_id) WHERE tenant_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_events_agent_id ON events (agent_id) WHERE agent_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_events_severity ON events (severity);

-- Dead Letter Queue table
CREATE TABLE IF NOT EXISTS dead_letter_queue (
    id BIGSERIAL PRIMARY KEY,
    event_id VARCHAR(64) NOT NULL,
    event_data JSONB NOT NULL,
    error_reason TEXT NOT NULL,
    error_count INTEGER NOT NULL DEFAULT 1,
    first_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved BOOLEAN NOT NULL DEFAULT FALSE,
    resolved_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_dlq_event_id ON dead_letter_queue (event_id);
CREATE INDEX IF NOT EXISTS idx_dlq_resolved ON dead_letter_queue (resolved) WHERE NOT resolved;

-- Idempotency tracking
CREATE TABLE IF NOT EXISTS idempotency_keys (
    key VARCHAR(128) PRIMARY KEY,
    event_id VARCHAR(64) NOT NULL,
    processed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_idempotency_expires ON idempotency_keys (expires_at);
