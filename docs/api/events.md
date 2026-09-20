# Events API

## POST /events

Submit a new event for ingestion.

### Request

```json
{
  "event_type": "LOGIN_FAILED",
  "source": "auth_service",
  "producer": "auth_v1",
  "payload": {
    "user_id": "u123",
    "ip_address": "10.0.0.1"
  },
  "severity": "warning",
  "metadata": {
    "region": "us-east-1"
  }
}
```

### Response (202 Accepted)

```json
{
  "event_id": "evt_abc123",
  "status": "accepted",
  "timestamp": "2025-01-01T00:00:00Z"
}
```

### Validation Rules

- `event_type`: Required, 1-255 characters
- `source`: Required, 1-255 characters
- `producer`: Required, 1-255 characters
- `severity`: Optional, defaults to "info"
- `payload`: Optional, defaults to {}
- `metadata`: Optional, defaults to {}

### Error Responses

- 422: Validation error
- 500: Internal server error
