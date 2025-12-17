# Deployment Guide

## Prerequisites

- Docker & Docker Compose
- OpenAI API Key
- GitHub Personal Access Token
- Domain with HTTPS (for production webhooks)

## Local Development

### 1. Clone Repository
```bash
git clone https://github.com/jitesh523/A-Comprehensive-Guide-to-Building-a-GenAI-Powered-Secure-Code-Review-Bot.git
cd A-Comprehensive-Guide-to-Building-a-GenAI-Powered-Secure-Code-Review-Bot
```

### 2. Configure Environment
```bash
cp .env.example .env
```

Edit `.env` and add your API keys:
```bash
OPENAI_API_KEY=sk-your-openai-key
GITHUB_TOKEN=ghp_your-github-token
GITHUB_WEBHOOK_SECRET=your-random-secret
```

### 3. Start Services
```bash
docker-compose up -d
```

### 4. Verify
```bash
curl http://localhost:8000/health
```

## Production Deployment

### Option 1: Docker Compose (Simple)

1. **Set up server** (Ubuntu 22.04 recommended)
2. **Install Docker**:
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

3. **Clone and configure** (same as local)

4. **Set up reverse proxy** (nginx):
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

5. **Enable HTTPS** with Let's Encrypt:
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### Option 2: Kubernetes (Scalable)

See `k8s/` directory for Kubernetes manifests (future enhancement).

## GitHub Webhook Setup

1. Go to repository **Settings** → **Webhooks** → **Add webhook**
2. **Payload URL**: `https://your-domain.com/webhook/github`
3. **Content type**: `application/json`
4. **Secret**: (same as `GITHUB_WEBHOOK_SECRET` in `.env`)
5. **Events**: Select "Pull requests" and "Pushes"
6. **Active**: ✓

## Monitoring

### Logs
```bash
# API logs
docker-compose logs -f api

# Worker logs
docker-compose logs -f celery_worker

# All logs
docker-compose logs -f
```

### Health Check
```bash
curl https://your-domain.com/health
```

## Scaling

### Horizontal Scaling
```yaml
# docker-compose.yml
celery_worker:
  # ... existing config
  deploy:
    replicas: 3  # Run 3 workers
```

### Resource Limits
```yaml
celery_worker:
  # ... existing config
  deploy:
    resources:
      limits:
        cpus: '1'
        memory: 2G
```

## Security Checklist

- [ ] HTTPS enabled (Let's Encrypt)
- [ ] Webhook secret configured
- [ ] API keys in environment variables (not code)
- [ ] CORS configured for production domains
- [ ] Rate limiting enabled (nginx/cloudflare)
- [ ] Database backups configured
- [ ] Logs rotated (logrotate)

## Troubleshooting

### Webhook not triggering
- Check webhook delivery in GitHub settings
- Verify HMAC signature validation
- Check server logs

### LLM verification failing
- Verify OpenAI API key
- Check API quota/billing
- Review error logs

### High costs
- Reduce findings limit (currently 10 per PR)
- Filter by file extensions
- Adjust SAST sensitivity

## Cost Optimization

- **LLM**: ~$0.01-0.02 per PR (10 findings)
- **Infrastructure**: ~$10-20/month (small VPS)
- **Total**: ~$30-50/month for 100 PRs

## Backup & Recovery

### Database Backup
```bash
docker-compose exec postgres pg_dump -U postgres secure_code_review > backup.sql
```

### Restore
```bash
docker-compose exec -T postgres psql -U postgres secure_code_review < backup.sql
```
