# Canonical Event Envelope

## Schema

```json
{
  "event_id": "evt_<uuid>",
  "event_version": "1.0",
  "event_type": "string",
  "timestamp": "ISO8601 UTC",
  "source": "string",
  "producer": "string",
  "tenant_id": "string | null",
  "trace_id": "string",
  "run_id": "string | null",
  "task_id": "string | null",
  "agent_id": "string | null",
  "session_id": "string | null",
  "severity": "debug | info | warning | error | critical",
  "payload": {},
  "metadata": {},
  "schema_version": "1.0"
}
```

## Fields

| Field | Required | Description |
|-------|----------|-------------|
| event_id | Yes (auto) | Unique event identifier |
| event_version | Yes | Schema version for this event type |
| event_type | Yes | Type of event (e.g., LOGIN_FAILED, TOOL_CALL) |
| timestamp | Yes (auto) | UTC timestamp of event creation |
| source | Yes | Source system (e.g., auth_service, agent_runtime) |
| producer | Yes | Specific producer within the source |
| tenant_id | No | Multi-tenant isolation |
| trace_id | Yes (auto) | Distributed trace correlation |
| run_id | No | Agent run identifier |
| task_id | No | Task identifier |
| agent_id | No | Agent identifier |
| session_id | No | Session identifier |
| severity | Yes | Event severity level |
| payload | Yes | Event-specific data |
| metadata | Yes | Additional metadata |
| schema_version | Yes | Envelope schema version |

## Event Types

### Security Events
- LOGIN_FAILED
- LOGIN_SUCCESS
- PORT_SCAN
- FIREWALL_BLOCK
- AUTHORIZATION_FAILURE

### Application Events
- REQUEST
- RESPONSE
- ERROR
- DATABASE_QUERY

### Agent Events
- AGENT_STARTED
- AGENT_STOPPED
- AGENT_STEP
- TOOL_CALL
- TOOL_RESULT
- MODEL_REQUEST
- MODEL_RESPONSE
- RETRIEVAL
- TASK_COMPLETED
- TASK_FAILED
