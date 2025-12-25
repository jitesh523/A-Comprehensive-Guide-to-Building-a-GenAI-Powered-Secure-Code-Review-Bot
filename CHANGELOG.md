# Changelog

All notable changes to the Secure Code Review Bot will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-12-25

### Added
- Health checks for all Docker services (API, Celery, Redis, PostgreSQL)
- Resource limits (CPU and memory) for all services in docker-compose.yml
- Restart policies for production reliability
- Caching configuration in .env.example (ENABLE_CACHING, CACHE_TTL_LLM, CACHE_TTL_SCAN)
- UPGRADE_GUIDE.md with comprehensive migration instructions
- CHANGELOG.md to track version changes
- Optimized Docker build with better layer caching
- Upgraded pip, setuptools, and wheel during Docker build

### Changed
- **BREAKING**: Upgraded Python from 3.11 to 3.12
- **BREAKING**: Updated all Python dependencies to latest stable versions:
  - FastAPI: 0.109.0 → 0.115.5
  - Pydantic: 2.5.3 → 2.10.3
  - OpenAI SDK: 1.10.0 → 1.58.1
  - SQLAlchemy: 2.0.25 → 2.0.36
  - Cryptography: 42.0.0 → 44.0.0
  - Celery: 5.3.6 → 5.4.0
  - Redis: 5.0.1 → 5.2.0
  - Tree-sitter: 0.21.0 → 0.23.2
  - Presidio: 2.2.354 → 2.2.360
  - pytest: 7.4.4 → 8.3.4
  - And many more (see requirements.txt)
- Updated JavaScript/TypeScript dependencies:
  - ESLint: 9.0.0 → 9.16.0
  - TypeScript: 5.0.0 → 5.7.2
  - @typescript-eslint/parser: 6.0.0 → 8.18.0
- Upgraded Go from 1.21.5 to 1.23.5 in Dockerfile
- Modernized Python type hints to use Python 3.12 syntax:
  - `Optional[str]` → `str | None`
  - `List[str]` → `list[str]`
  - `Dict[str, Any]` → `dict[str, Any]`
- Increased Celery worker concurrency from 2 to 4
- APP_VERSION bumped to 2.0.0
- Enhanced docker-compose.yml with proper health check dependencies

### Fixed
- Removed duplicate REDIS configuration in config.py
- Fixed typo in .env.example (NOTIFICATION_MIN_SEVERITY value)
- Improved Docker build efficiency with multi-stage approach

### Removed
- Removed `from typing import Optional, List` imports (using native Python 3.12 syntax)

## [1.0.0] - 2024-12-18

### Added
- Initial release of Secure Code Review Bot
- Multi-language support (Python, JavaScript, TypeScript, Go, Rust)
- AI-powered verification using GPT-4
- Intelligent auto-fix suggestions
- Privacy-safe scanning with PII/secret redaction
- CI/CD integration (GitHub Actions, GitLab CI, Jenkins)
- CLI tool for local scanning
- Docker and docker-compose support
- PostgreSQL database for scan history
- Redis for caching and task queue
- Celery for async task processing
- Comprehensive test suite
- Documentation (README, API docs, deployment guide, usage examples)

---

## Migration Notes

### Upgrading from 1.0.0 to 2.0.0

**Important**: This is a major version upgrade with breaking changes. Please follow the [UPGRADE_GUIDE.md](UPGRADE_GUIDE.md) for detailed migration instructions.

**Key Breaking Changes**:
1. Python 3.12 required (was 3.11)
2. Docker images must be rebuilt
3. Some dependency APIs may have changed

**Recommended Steps**:
1. Backup your `.env` file and database
2. Review UPGRADE_GUIDE.md
3. Test in a staging environment first
4. Follow the upgrade procedure step-by-step

---

## Upcoming Features (Planned)

See [implementation_plan.md](implementation_plan.md) for the complete roadmap:

- **Phase 3**: Java and C/C++ language support
- **Phase 4**: Multi-LLM providers (Anthropic Claude, Google Gemini)
- **Phase 5**: Enhanced auto-fix with test validation
- **Phase 6**: Advanced security features (SCA, container scanning, compliance)
- **Phase 7**: Performance optimization
- **Phase 8**: Enhanced observability with OpenTelemetry
- **Phase 9**: VS Code extension and web dashboard
- **Phase 10**: 90%+ test coverage
- **Phase 11**: Kubernetes and Terraform deployment
