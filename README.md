# GenAI-Powered Secure Code Review Bot

A hybrid security analysis system that combines Static Application Security Testing (SAST) with Large Language Model (LLM) verification to dramatically reduce false positives in automated code security reviews.

## Architecture

**Filter-Verify Pattern:**
1. **SAST (Bandit/ESLint)** - High recall candidate generation
2. **Context Extraction (Tree-sitter)** - Extract relevant code context
3. **Privacy Layer (Presidio)** - Redact PII and secrets
4. **LLM Verification (OpenAI)** - High precision validation
5. **Report** - Only verified findings posted to PRs

## Technology Stack

- **API**: FastAPI
- **Task Queue**: Celery + Redis
- **Database**: PostgreSQL
- **SAST**: Bandit (Python), ESLint (JavaScript)
- **Context**: Tree-sitter
- **Privacy**: Microsoft Presidio
- **LLM**: OpenAI API (GPT-4)
- **Git**: PyGithub

## Quick Start

### Prerequisites
- Docker & Docker Compose
- OpenAI API Key
- GitHub Personal Access Token

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd A-Comprehensive-Guide-to-Building-a-GenAI-Powered-Secure-Code-Review-Bot
```

2. Configure environment variables:
```bash
cp .env.example .env
# Edit .env and add your API keys
```

3. Start services:
```bash
docker-compose up -d
```

4. Verify health:
```bash
curl http://localhost:8000/health
```

## Development Status

### Phase 1: Core Infrastructure ✅
- FastAPI application with health check
- Celery task queue with Redis
- Docker Compose configuration
- Environment configuration

### Phase 2: Python SAST (Bandit) ✅
- OWASP Top 10 configuration
- JSON output parsing
- Normalized finding schema

### Phase 3: JavaScript SAST (ESLint) ✅
- Security plugins (security + no-unsanitized)
- Flat config format
- Unified finding schema

### Phase 4: Context Extraction (Tree-sitter) ✅
- Unified API for Python and JavaScript
- Function/class detection
- Import extraction
- Fallback to line-based context

### Phase 5: Privacy & Sanitization (Presidio) ✅
- Microsoft Presidio for PII detection
- Custom regex for secret detection
- Redaction logging and validation
- File path sanitization

### Phase 6: LLM Verification (OpenAI) ✅
- OpenAI API with structured outputs
- Pydantic models for JSON schema enforcement
- Verification prompt engineering
- Few-shot examples for accuracy
- Batch processing support

### Phase 7: Webhook & Git Integration ✅
- GitHub webhook endpoint with HMAC validation
- Pull request and push event handlers
- GitHub API client for PR comments
- Celery task orchestration for scans
- Automated inline PR comments

### Phase 8-11: In Progress
See `implementation_plan.md` for detailed roadmap.

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
.
├── app/
│   ├── api/          # FastAPI endpoints
│   ├── scanners/     # SAST integrations
│   ├── context/      # Tree-sitter context extraction
│   ├── privacy/      # PII/secret redaction
│   ├── llm/          # LLM verification
│   ├── git/          # GitHub integration
│   ├── tasks/        # Celery tasks
│   └── models/       # Database models
├── configs/          # Tool configurations
├── tests/            # Test suite
└── docs/             # Documentation

```

## License

MIT

## References

Based on research from:
- [LLM-Driven SAST-Genius](https://arxiv.org/abs/2509.15433)
- [OWASP Top 10](https://owasp.org/Top10/2021/)
