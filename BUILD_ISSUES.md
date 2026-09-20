# DIP Build Issues

## ISSUE-001

Status: OPEN
Component: Infrastructure
Severity: Medium

### Problem

Docker cannot start because hardware virtualization is disabled in BIOS.

### Impact

Containerized local development unavailable. Kafka, Elasticsearch, Redis run as local/test backends only.

### Current workaround

Run PostgreSQL locally. Use `DIP_EVENT_BACKEND=memory`, `DIP_SEARCH_BACKEND=memory`, `DIP_CACHE_BACKEND=memory`.

### Resolution

Enable virtualization/WSL2 when the development machine is ready for it.

---

## ISSUE-002

Status: OPEN
Component: Runtime
Severity: Low

### Problem

Machine has Python 3.11.9 but project targets Python 3.12 in pyproject.toml and CI.

### Impact

Code works on 3.11. CI runs on 3.12. Minor version difference. No blocking incompatibilities found so far.

### Current workaround

Develop and test locally on 3.11. CI remains authoritative on 3.12.

### Resolution

Install Python 3.12 or verify 3.11 compatibility long-term.

---

## ISSUE-003

Status: OPEN
Component: Kafka
Severity: Medium

### Problem

No real Kafka broker available locally. Docker unavailable.

### Impact

Kafka integration can only be tested via unit tests with memory backend.

### Current workaround

`DIP_EVENT_BACKEND=memory` provides same interface for development and testing.

### Resolution

When Docker/WSL2 available, run real Kafka broker and switch to `DIP_EVENT_BACKEND=kafka`.

---

## ISSUE-004

Status: OPEN
Component: Elasticsearch
Severity: Medium

### Problem

No Elasticsearch instance available locally.

### Impact

Search functionality only available via memory backend.

### Current workaround

`DIP_SEARCH_BACKEND=memory` for local development.

### Resolution

When Docker available, run Elasticsearch container.
