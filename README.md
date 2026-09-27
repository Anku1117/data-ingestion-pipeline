# DIP — Data Ingestion Platform

A production-grade, event-driven Data Ingestion Platform designed for traditional data engineering, security analytics, AI agents, agent harnesses, RAG systems, and future autonomous engineering systems.

## Architecture

```
Client → POST /events → Pydantic Validation → EventService → Repository → SQLAlchemy → PostgreSQL
```

## Tech Stack

- **Backend**: Python, FastAPI, Pydantic v2
- **Database**: PostgreSQL, SQLAlchemy 2.x (async), Alembic
- **Streaming**: Apache Kafka (Phase 5+)
- **Search**: Elasticsearch (Phase 12+)
- **Testing**: pytest, pytest-asyncio
- **Infrastructure**: Docker, Docker Compose
- **CI**: GitHub Actions

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Start PostgreSQL (via Docker)
docker compose up postgres -d

# Run database migrations
alembic upgrade head

# Run the API
uvicorn services.ingestion.main:app --reload

# Run tests
pytest
```

## Development

```bash
# Run linting
ruff check .
ruff format --check .

# Run type checking
mypy --ignore-missing-imports libraries/ services/

# Run tests with coverage
pytest --cov=services --cov=libraries --cov-report=html
```

## Database

### Migrations

```bash
# Apply all migrations
alembic upgrade head

# Create a new migration
alembic revision --autogenerate -m "description"

# Rollback one step
alembic downgrade -1

# Show current version
alembic current
```

### Schema

The `events` table stores all ingested events with:
- Primary key: `event_id` (unique constraint prevents duplicates)
- Indexes on: `event_type`, `source`, `timestamp`, `trace_id`, `severity`
- Partial indexes on: `tenant_id`, `agent_id`, `run_id` (WHERE NOT NULL)
- JSONB columns for: `payload`, `metadata`

### Repository Pattern

```
EventRepository (abstract)
    └── SQLAlchemyEventRepository (implementation)
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /health | Liveness check |
| GET | /ready | Readiness check (verifies DB connection) |
| POST | /events | Create and persist an event |

### POST /events

**Request:**
```json
{
  "event_type": "LOGIN_FAILED",
  "source": "auth_service",
  "producer": "auth_v1",
  "payload": {"user_id": "u123"},
  "severity": "info"
}
```

**Response (201 Created):**
```json
{
  "event_id": "evt_abc123",
  "status": "created",
  "timestamp": "2025-01-01T00:00:00Z"
}
```

**Error Responses:**
- `409 Conflict`: Duplicate event_id
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Database failure

## Project Structure

```
DIP/
├── services/
│   ├── ingestion/           # FastAPI application
│   │   ├── main.py          # App factory, lifespan
│   │   ├── service.py       # Application service layer
│   │   ├── schemas.py       # API request/response models
│   │   └── routes/          # HTTP route handlers
│   ├── processor/           # Event processing (Phase 6+)
│   ├── detector/            # Threat detection (Phase 13+)
│   └── agent_data/          # Agent telemetry (Phase 9+)
├── libraries/
│   ├── database/            # SQLAlchemy, models, repositories
│   │   ├── session.py       # Engine, session factory
│   │   ├── models.py        # SQLAlchemy ORM models
│   │   └── repositories/    # Repository pattern
│   ├── schemas/             # Canonical event envelope
│   ├── configuration/       # pydantic-settings
│   ├── logging/             # Structured logging
│   └── observability/       # Metrics collector
├── alembic/                 # Database migrations
│   ├── env.py               # Async migration runner
│   └── versions/            # Migration scripts
├── tests/
│   ├── unit/                # Fast isolated tests
│   ├── integration/         # API + database tests
│   ├── contract/            # Schema contract tests
│   └── e2e/                 # End-to-end tests
├── infrastructure/          # Docker, Postgres, Kafka configs
├── docs/                    # Architecture documentation
└── .github/workflows/       # CI/CD pipelines
```

## License

Private — All rights reserved.
