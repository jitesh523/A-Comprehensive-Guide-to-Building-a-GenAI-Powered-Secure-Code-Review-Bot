# Upgrade Guide for Secure Code Review Bot v2.0

## Overview
This guide covers the upgrade from v1.0 to v2.0, including:
- Python 3.11 → 3.12
- All dependency updates
- Docker configuration enhancements
- Modern type hint syntax

## Prerequisites
- Docker and Docker Compose installed
- Backup of your current `.env` file
- Backup of your database (if in production)

## Upgrade Steps

### Step 1: Backup Current Setup
```bash
# Backup environment file
cp .env .env.backup

# Backup database (if using production data)
docker exec secure-code-review-postgres pg_dump -U postgres secure_code_review > backup_$(date +%Y%m%d).sql

# Stop current services
docker-compose down
```

### Step 2: Pull Latest Changes
```bash
git pull origin main
```

### Step 3: Update Dependencies
```bash
# The requirements.txt and package.json have been updated
# Docker will install these automatically on rebuild
```

### Step 4: Rebuild Docker Images
```bash
# Rebuild with no cache to ensure fresh install
docker-compose build --no-cache

# Or rebuild specific services
docker-compose build --no-cache api celery_worker
```

### Step 5: Update Environment Variables
```bash
# Compare your .env with .env.example
# New variables in v2.0:
# - LLM_PROVIDER (optional, defaults to openai)
# - ANTHROPIC_API_KEY (optional)
# - GOOGLE_API_KEY (optional)

# Copy new template if needed
cp .env.example .env.new
# Then manually merge your existing values
```

### Step 6: Start Services
```bash
# Start all services
docker-compose up -d

# Check service health
docker-compose ps
docker-compose logs -f api
```

### Step 7: Verify Upgrade
```bash
# Test health endpoint
curl http://localhost:8000/health

# Check version
curl http://localhost:8000/version

# Run tests
docker-compose exec api pytest tests/ -v
```

## What's New in v2.0

### Dependency Updates
- **FastAPI**: 0.109.0 → 0.115.5
- **Pydantic**: 2.5.3 → 2.10.3
- **OpenAI SDK**: 1.10.0 → 1.58.1
- **SQLAlchemy**: 2.0.25 → 2.0.36
- **Cryptography**: 42.0.0 → 44.0.0
- **Python**: 3.11 → 3.12
- **Go**: 1.21.5 → 1.23.5
- **ESLint**: 9.0.0 → 9.16.0
- **TypeScript**: 5.0.0 → 5.7.2

### Infrastructure Improvements
- ✅ Health checks for all services
- ✅ Resource limits (CPU, memory)
- ✅ Restart policies
- ✅ Optimized Docker build layers
- ✅ Better dependency management

### Code Improvements
- ✅ Modern Python 3.12 type hints
- ✅ Removed duplicate configuration
- ✅ Version bumped to 2.0.0

## Rollback Procedure

If you encounter issues:

```bash
# Stop new version
docker-compose down

# Restore environment
cp .env.backup .env

# Restore database (if needed)
cat backup_YYYYMMDD.sql | docker exec -i secure-code-review-postgres psql -U postgres secure_code_review

# Checkout previous version
git checkout v1.0  # or your previous commit

# Rebuild and start
docker-compose build
docker-compose up -d
```

## Common Issues

### Issue: Docker build fails
**Solution**: Clear Docker cache and rebuild
```bash
docker system prune -a
docker-compose build --no-cache
```

### Issue: Health checks failing
**Solution**: Check logs and increase start_period
```bash
docker-compose logs api
# Edit docker-compose.yml and increase start_period if needed
```

### Issue: Database connection errors
**Solution**: Ensure PostgreSQL is healthy
```bash
docker-compose logs postgres
docker-compose restart postgres
```

## Testing Checklist

- [ ] Health endpoint responds
- [ ] Database connection works
- [ ] Redis connection works
- [ ] Celery workers are running
- [ ] GitHub webhook works
- [ ] LLM verification works
- [ ] All tests pass

## Support

If you encounter issues:
1. Check the logs: `docker-compose logs -f`
2. Verify environment variables: `docker-compose config`
3. Open an issue on GitHub with logs and error messages

## Next Steps

After successful upgrade:
- Review new features in implementation_plan.md
- Consider enabling multi-LLM providers (Phase 4)
- Plan for additional language support (Phase 3)
