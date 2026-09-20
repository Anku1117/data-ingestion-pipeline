# DIP — Data Ingestion Platform

A production-grade, event-driven Data Ingestion Platform designed for traditional data engineering, security analytics, AI agents, agent harnesses, RAG systems, and future autonomous engineering systems.

## Architecture

```
DATA SOURCES → INGESTION LAYER → SCHEMA VALIDATION → NORMALIZATION → KAFKA → PROCESSORS → CANONICAL EVENT STORE
```

## Tech Stack

- **Backend**: Python, FastAPI, Pydantic
- **Streaming**: Apache Kafka
- **Database**: PostgreSQL
- **Search**: Elasticsearch
- **Frontend**: React
- **Testing**: pytest
- **Infrastructure**: Docker, Docker Compose
- **Observability**: Prometheus, Grafana
- **CI**: GitHub Actions

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the API
uvicorn services.ingestion.main:app --reload

# Run tests
pytest
```

## Development

```bash
# Install dev dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run linting
ruff check .
ruff format --check .

# Run type checking
mypy .

# Run tests with coverage
pytest --cov=services --cov-report=html
```

## Project Structure

```
DIP/
├── services/
│   ├── ingestion/       # API ingestion layer
│   ├── processor/       # Event processing engine
│   ├── detector/        # Threat/anomaly detection
│   └── agent_data/      # Agent telemetry & training data
├── infrastructure/      # Docker, Kafka, Postgres configs
├── libraries/           # Shared libraries (schemas, logging, config)
├── tests/               # Unit, integration, contract, e2e tests
├── docs/                # Architecture, API, event docs
├── dashboard/           # React frontend
├── scripts/             # Utility scripts
└── .github/workflows/   # CI/CD pipelines
```

## License

Private — All rights reserved.
