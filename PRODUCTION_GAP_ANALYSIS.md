# PRODUCTION GAP ANALYSIS

## Component Inventory

| Component | Current | Problem | Requirement | Status |
|-----------|---------|---------|-------------|--------|
| Agent Data | In-memory dicts | Lost on restart, not shared | PostgreSQL persistence | TODO |
| Detection Alerts | In-memory list (capped) | Lost on restart | PostgreSQL/Redis | TODO |
| Metrics | In-memory counters | Lost on restart, not shared | Prometheus client | TODO |
| Event Backend | Memory/Kafka abstraction | Kafka untested with real broker | Real Kafka + contract tests | TODO |
| Search Backend | Memory/ES abstraction | ES untested with real instance | Real ES + contract tests | TODO |
| Cache Backend | Memory/Redis abstraction | Redis untested | Real Redis + contract tests | TODO |
| Vector Store | Memory only | No persistence | pgvector | TODO |
| API Auth | None | Open endpoints | API key auth | TODO |
| Rate Limiting | None | No protection | Redis-backed | TODO |
| CORS | `*` in debug, empty in prod | Prod blocks all | Configurable origins | TODO |
| Dashboard | React skeleton | Minimal functionality | Production dashboard | TODO |
| Docker | Compose defined | Not tested (virtualization) | Validate config | TODO |
| Logging | Structured JSON | No sensitive data audit | Verify no leaks | TODO |
| Shutdown | Basic lifespan | No drain logic | Graceful shutdown | TODO |
| Configuration | Settings class | No prod/test profiles | Profile separation | TODO |
| Data Retention | None | Unlimited growth | Configurable retention | TODO |

## Phase 1: Persistent Agent Data — IN PROGRESS

### Models Needed
- `AgentRunRecord` — run_id, agent_id, task_id, status, timestamps
- `AgentStepRecord` — step_id, run_id, step_type, sequence, data
- `AgentEvaluationRecord` — evaluation_id, run_id, scores
- `AgentTaskRecord` — task_id, agent_id, description

### Repositories Needed
- `AgentRunRepository` (abstract + SQLAlchemy)
- `AgentStepRepository` (abstract + SQLAlchemy)
- `AgentEvaluationRepository` (abstract + SQLAlchemy)

### Service Changes
- `AgentDataService` — replace dict storage with repository calls
- `agents.py` route — inject session, use repositories

## Phase 2-12: Pending

See STAGE_B_REPORT.md for infrastructure status.
