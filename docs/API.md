# API Documentation

## Endpoints

### Health Check
```
GET /health
```

**Response**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "service": "secure-code-review-bot"
}
```

### GitHub Webhook
```
POST /webhook/github
```

**Headers**:
- `X-GitHub-Event`: Event type (pull_request, push, ping)
- `X-Hub-Signature-256`: HMAC-SHA256 signature

**Supported Events**:
- `pull_request` (opened, synchronize)
- `push` (main/master branch)
- `ping`

**Example Payload** (pull_request):
```json
{
  "action": "opened",
  "number": 42,
  "pull_request": {
    "number": 42,
    "head": {
      "sha": "abc123def456"
    }
  },
  "repository": {
    "full_name": "owner/repo"
  }
}
```

**Response**:
```json
{
  "message": "Scan queued",
  "pr_number": 42,
  "repo": "owner/repo"
}
```

## Interactive Documentation

Visit `/docs` for Swagger UI with interactive API testing.

Visit `/redoc` for ReDoc documentation.
