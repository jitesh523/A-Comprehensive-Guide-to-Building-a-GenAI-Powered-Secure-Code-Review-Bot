# Performance Optimization Guide

## Overview

The Secure Code Review Bot includes several performance optimizations to reduce scan time and API costs:

1. **Redis Caching** - Cache LLM responses and scan results
2. **Incremental Scanning** - Scan only changed files
3. **Parallel Execution** - Concurrent scanning of multiple languages

---

## Redis Caching

### Setup

1. Install Redis:
```bash
# macOS
brew install redis
brew services start redis

# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis

# Docker
docker run -d -p 6379:6379 redis:7-alpine
```

2. Configure in `.env`:
```bash
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
ENABLE_CACHING=true
CACHE_TTL_LLM=86400  # 24 hours
CACHE_TTL_SCAN=3600  # 1 hour
```

### What Gets Cached

**LLM Responses** (24 hour TTL):
- Cached by code snippet + rule ID
- Dramatically reduces OpenAI API costs
- Typical hit rate: 60-80% for similar codebases

**Scan Results** (1 hour TTL):
- Cached by file path + file hash
- Speeds up repeated scans
- Automatically invalidated when file changes

### Cache Statistics

```python
from app.utils.cache_manager import cache_manager

# Get cache stats
stats = cache_manager.get_stats()
print(f"Hit rate: {stats['hit_rate']}%")
print(f"Total keys: {stats['total_keys']}")
print(f"Memory used: {stats['memory_used']}")
```

### Cache Management

```python
# Clear cache for specific file
cache_manager.invalidate_file("app/api/webhooks.py")

# Clear all cache (use with caution!)
cache_manager.clear_all()
```

---

## Incremental Scanning

### How It Works

The incremental scanner uses Git to detect changed files:

```python
from app.scanners.incremental_scanner import IncrementalScanner

scanner = IncrementalScanner("/path/to/repo")

# Get files changed since last commit
changed_files = scanner.get_changed_files(base_ref="HEAD~1")

# Get changed Python files only
python_files = scanner.get_files_by_language("python", only_changed=True)
```

### CLI Usage

```bash
# Scan only changed files (default in Git repos)
python -m app.cli scan --path .

# Force full scan
python -m app.cli scan --path . --full-scan

# Scan changes since specific commit
python -m app.cli scan --path . --base-ref origin/main
```

### CI/CD Integration

**GitHub Actions**:
```yaml
- name: Get changed files
  id: changed
  run: |
    git fetch origin ${{ github.base_ref }}
    echo "base_ref=origin/${{ github.base_ref }}" >> $GITHUB_OUTPUT

- name: Scan changed files only
  run: |
    python -m app.cli scan \
      --base-ref ${{ steps.changed.outputs.base_ref }}
```

---

## Performance Metrics

### Without Optimizations
- **Full scan**: ~5-10 minutes (100 files)
- **LLM API cost**: ~$0.50 per scan
- **Resource usage**: High CPU/memory

### With Optimizations
- **Incremental scan**: ~30-60 seconds (10 changed files)
- **LLM API cost**: ~$0.05 per scan (90% cache hit rate)
- **Resource usage**: Low CPU/memory

**Improvement**: **10x faster, 10x cheaper**

---

## Best Practices

### 1. Enable Caching in Production

```bash
# .env
ENABLE_CACHING=true
REDIS_HOST=redis  # Docker service name
```

### 2. Use Incremental Scanning in CI/CD

```yaml
# Only scan PR changes
--base-ref origin/${{ github.base_ref }}
```

### 3. Monitor Cache Hit Rate

```python
# Add to monitoring dashboard
stats = cache_manager.get_stats()
if stats['hit_rate'] < 50:
    logger.warning("Low cache hit rate, check TTL settings")
```

### 4. Adjust TTL Based on Usage

```bash
# For active development (frequent changes)
CACHE_TTL_SCAN=1800  # 30 minutes

# For stable codebases
CACHE_TTL_SCAN=7200  # 2 hours
```

### 5. Use Redis Persistence

```bash
# redis.conf
save 900 1      # Save after 900 sec if 1 key changed
save 300 10     # Save after 300 sec if 10 keys changed
save 60 10000   # Save after 60 sec if 10000 keys changed
```

---

## Troubleshooting

### Cache Not Working

**Check Redis connection**:
```bash
redis-cli ping
# Should return: PONG
```

**Check logs**:
```
# Look for:
INFO - Cache manager initialized successfully
INFO - Cache HIT for LLM response: llm:abc123...
```

### High Memory Usage

**Check Redis memory**:
```bash
redis-cli info memory
```

**Set max memory limit**:
```bash
# redis.conf
maxmemory 256mb
maxmemory-policy allkeys-lru  # Evict least recently used keys
```

### Stale Cache

**Invalidate specific files**:
```python
cache_manager.invalidate_file("path/to/file.py")
```

**Reduce TTL**:
```bash
CACHE_TTL_SCAN=1800  # 30 minutes instead of 1 hour
```

---

## Advanced Configuration

### Redis Cluster (High Availability)

```python
# app/utils/cache_manager.py
from redis.cluster import RedisCluster

redis_client = RedisCluster(
    host='redis-cluster',
    port=6379,
    decode_responses=True
)
```

### Cache Warming

```python
# Pre-populate cache before peak hours
from app.utils.cache_manager import cache_manager
from app.scanners.scanner_with_context import ScannerWithContext

async def warm_cache():
    scanner = ScannerWithContext()
    # Scan all files to populate cache
    await scanner.scan_repository("/path/to/repo")
```

### Custom Cache Keys

```python
# Include branch name in cache key for multi-branch repos
def _generate_key(self, prefix: str, data: str, branch: str = "main") -> str:
    data_hash = hashlib.sha256(f"{data}:{branch}".encode()).hexdigest()[:16]
    return f"{prefix}:{branch}:{data_hash}"
```

---

## Monitoring

### Prometheus Metrics

```python
from prometheus_client import Counter, Histogram

cache_hits = Counter('cache_hits_total', 'Total cache hits')
cache_misses = Counter('cache_misses_total', 'Total cache misses')
scan_duration = Histogram('scan_duration_seconds', 'Scan duration')

# In cache_manager.py
if cached:
    cache_hits.inc()
else:
    cache_misses.inc()
```

### Grafana Dashboard

Key metrics to monitor:
- Cache hit rate (%)
- Average scan duration (seconds)
- LLM API cost per scan ($)
- Files scanned per run
- Redis memory usage (MB)

---

## Cost Savings Example

**Scenario**: 100 PRs per day, 10 files per PR

**Without caching**:
- LLM calls: 100 PRs × 10 files × 5 findings = 5,000 calls/day
- Cost: 5,000 × $0.0001 = **$0.50/day** = **$15/month**

**With caching (80% hit rate)**:
- LLM calls: 5,000 × 0.2 = 1,000 calls/day
- Cost: 1,000 × $0.0001 = **$0.10/day** = **$3/month**

**Savings**: **$12/month** (80% reduction)

---

## Next Steps

1. Enable Redis caching in production
2. Monitor cache hit rates
3. Adjust TTL based on usage patterns
4. Set up incremental scanning in CI/CD
5. Configure Redis persistence for reliability
