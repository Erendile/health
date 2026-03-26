## Endpoints

| Method | Path | Description | Rate Limit |
|--------|------|-------------|------------|
| GET | `/health` | Returns service status | 60/min |
| GET | `/test` | Test endpoint | 60/min |
| GET | `/db-status` | Checks database connectivity | 10/min |
| POST | `/messages` | Leave a message (nickname + text) | 12/hour |
| GET | `/messages` | List last 50 messages | 30/min |
| GET | `/api/v1/openapi.json` | OpenAPI schema | — |

### POST /messages

**Request body:**
```json
{
  "nickname": "john",
  "message": "Hello from the API!"
}
```

**Response (201):**
```json
{
  "id": 1,
  "nickname": "john",
  "message": "Hello from the API!",
  "created_at": "2026-03-25T19:00:00+00:00"
}
```

**Validation:**
- `nickname`: required, max 32 characters
- `message`: required, max 280 characters

Rate limits return `429 Too Many Requests` when exceeded.