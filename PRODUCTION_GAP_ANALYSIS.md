# PRODUCTION GAP ANALYSIS

## Component Inventory

| Component | Current State | Status |
|-----------|--------------|--------|
| Agent Data | PostgreSQL persistence via repositories | DONE |
| Detection Alerts | PostgreSQL persistence via AlertRepository | DONE |
| Metrics | In-memory counters (Prometheus client available) | ACCEPTED |
| Event Backend | Memory/Kafka abstraction + contract tests + fail-fast | DONE |
| Search Backend | Memory/ES abstraction + contract tests + fail-fast | DONE |
| Cache Backend | Memory/Redis abstraction + contract tests + fail-fast | DONE |
| Vector Store | Memory only (pgvector for future) | BLOCKED — no Docker |
| API Auth | SHA-256 hashed API keys, production-only enforcement | DONE |
| Rate Limiting | Sliding window (60 RPM, 10 RPS per IP) | DONE |
| CORS | Configurable origins via DIP_CORS_ORIGINS | DONE |
| Dashboard | React skeleton (8 pages) | ACCEPTED |
| Docker | Compose defined (not testable — virtualization disabled) | BLOCKED |
| Logging | Structured JSON, get_logger() everywhere | DONE |
| Shutdown | Graceful drain with 30s timeout | DONE |
| Configuration | Settings class with env vars | DONE |
| Data Retention | Configurable purge via /pipeline/retention/purge | DONE |

## Blocked Items (require hardware/infra changes)
- Docker virtualization: BIOS-level, not fixable in software
- Real Kafka/ES/Redis integration tests: need Docker
- Full-stack E2E tests: need Docker
