# DIP Architecture Overview

## System Architecture

```
DATA SOURCES → INGESTION LAYER → APACHE KAFKA → PROCESSORS → CANONICAL EVENT STORE
```

## Components

### Ingestion Layer (FastAPI)
- REST API for event ingestion
- Schema validation
- Event envelope creation
- Request tracking

### Apache Kafka
- Event streaming backbone
- Topic-based routing
- Consumer groups for parallel processing
- Dead Letter Queue for failed events

### Processing Engine
- Event validation
- Normalization
- Transformation
- Enrichment
- Routing

### Canonical Event Store
- PostgreSQL for structured storage
- Elasticsearch for search and analytics

### Detection Layer
- Rule-based threat detection
- AI/ML anomaly detection

### Agent Data Platform
- Agent trajectories
- Training datasets
- Evaluation datasets
- RAG infrastructure

## Data Flow

1. Events arrive via REST API or adapters
2. Events are validated against schemas
3. Events are wrapped in canonical envelope
4. Events are published to Kafka topics
5. Processors consume and enrich events
6. Events are stored in canonical event store
7. Detection engines analyze events
8. Agent data platform processes agent telemetry

## Design Principles

- **Event-First**: All data flows through canonical event envelope
- **Schema-First**: Clear schemas before processing logic
- **Modular**: Independent, testable components
- **Observable**: Structured logging, metrics, health checks
- **Extensible**: New sources via adapters, not core changes
