# Docker Deployment Guide for Orbit V3 Backend

Comprehensive guide for deploying the FastAPI backend using Docker and Docker Compose.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Development Deployment](#development-deployment)
4. [Production Deployment](#production-deployment)
5. [Environment Configuration](#environment-configuration)
6. [Database Migrations](#database-migrations)
7. [Monitoring & Health Checks](#monitoring--health-checks)
8. [Scaling](#scaling)
9. [Troubleshooting](#troubleshooting)
10. [Backup & Restore](#backup--restore)

---

## Prerequisites

### System Requirements

- **Docker Engine**: 20.10+ ([Install Docker](https://docs.docker.com/engine/install/))
- **Docker Compose**: 2.0+ ([Install Compose](https://docs.docker.com/compose/install/))
- **System Resources**:
  - Minimum: 4GB RAM, 2 CPU cores, 10GB disk space
  - Recommended: 8GB RAM, 4 CPU cores, 20GB disk space

### Verification

```bash
# Check Docker version
docker --version
# Expected: Docker version 20.10.x or higher

# Check Docker Compose version
docker compose version
# Expected: Docker Compose version v2.x.x or higher

# Verify Docker is running
docker ps
# Should show container list (may be empty)
```

---

## Quick Start

Get the backend running in under 5 minutes:

```bash
# 1. Navigate to backend directory
cd /Users/robertvill/voice2task/backend

# 2. Copy environment template
cp .env.example .env

# 3. Edit .env and add your ANTHROPIC_API_KEY
# (Use nano, vim, or your preferred editor)
nano .env
# Set: ANTHROPIC_API_KEY="sk-ant-api03-YOUR-KEY-HERE"

# 4. Start all services
docker compose up -d

# 5. Run database migrations
docker compose exec backend alembic upgrade head

# 6. Verify services are running
docker compose ps

# 7. Test health endpoint
curl http://localhost:8000/health

# 8. View API documentation
open http://localhost:8000/docs
```

Expected output from step 6:
```
NAME              IMAGE                    STATUS         PORTS
orbit_backend     backend-backend          Up             0.0.0.0:8000->8000/tcp
orbit_postgres    pgvector/pgvector:pg16   Up (healthy)   0.0.0.0:5432->5432/tcp
orbit_redis       redis:7-alpine           Up (healthy)   0.0.0.0:6379->6379/tcp
```

---

## Development Deployment

### Starting Services

```bash
# Start all services in background
docker compose up -d

# Start with live logs
docker compose up

# Start specific service
docker compose up -d backend

# Rebuild and start (after code changes)
docker compose up -d --build
```

### Hot Reload

The development configuration automatically enables hot reload:
- Code changes in `app/`, `alembic/`, and `tests/` are mounted as volumes
- Uvicorn watches for changes and auto-reloads
- No container restart needed for code changes

### Viewing Logs

```bash
# Follow all logs
docker compose logs -f

# Follow specific service
docker compose logs -f backend

# View last 100 lines
docker compose logs --tail=100 backend

# View logs since 1 hour ago
docker compose logs --since 1h backend
```

### Accessing Container Shell

```bash
# Open bash shell in backend container
docker compose exec backend bash

# Run Python shell with app context
docker compose exec backend python

# One-off command
docker compose exec backend ls -la /app
```

### Stopping Services

```bash
# Stop all services (keeps data)
docker compose down

# Stop and remove volumes (DELETES ALL DATA!)
docker compose down -v

# Stop specific service
docker compose stop backend
```

---

## Production Deployment

### Pre-Deployment Checklist

Before deploying to production, complete these steps:

#### 1. Security Configuration

```bash
# Generate secure SECRET_KEY
openssl rand -hex 32

# Generate secure database password
openssl rand -base64 32
```

Update `.env`:
```bash
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING

# Use generated values
SECRET_KEY="<generated-secret-key>"
POSTGRES_PASSWORD="<generated-password>"

# Update database URL with new password
DATABASE_URL="postgresql+asyncpg://orbit:<generated-password>@localhost:5432/orbit_db"
```

#### 2. Update docker-compose.yml for Production

Edit `/Users/robertvill/voice2task/backend/docker-compose.yml`:

```yaml
# Comment out hot reload volumes (lines 200-204)
# volumes:
#   - ./app:/app/app:ro
#   - ./alembic:/app/alembic:ro
#   - ./tests:/app/tests:ro

# Comment out --reload flag (line 120)
# command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
# (This will use the Dockerfile CMD with 4 workers)
```

#### 3. Configure External Services

```bash
# Update .env with production values
CORS_ORIGINS="https://your-production-frontend.com"
SENTRY_DSN="https://your-sentry-dsn@sentry.io/project-id"
ANTHROPIC_API_KEY="sk-ant-api03-PRODUCTION-KEY"
```

#### 4. Resource Limits

Adjust resource limits in `docker-compose.yml` based on your server:

```yaml
deploy:
  resources:
    limits:
      cpus: '4.0'      # Increase for production
      memory: 4G       # Increase for production
    reservations:
      cpus: '1.0'
      memory: 1G
```

### Building for Production

```bash
# Build optimized images
docker compose build --no-cache

# Verify image size
docker images | grep orbit

# Expected sizes (approximate):
# orbit_backend: 400-500 MB (multi-stage build optimization)
```

### Deploying to Production

```bash
# 1. Pull latest code
git pull origin main

# 2. Build images
docker compose build --no-cache

# 3. Stop existing services (if running)
docker compose down

# 4. Start with new images
docker compose up -d

# 5. Run migrations
docker compose exec backend alembic upgrade head

# 6. Verify health
curl http://localhost:8000/health/ready

# 7. Check logs for errors
docker compose logs -f backend
```

### Zero-Downtime Deployment (Advanced)

For zero-downtime deployments, use this strategy:

```bash
# 1. Start new containers with different names
docker compose -p orbit-blue up -d

# 2. Wait for health checks
sleep 30
curl http://localhost:8000/health/ready

# 3. Switch traffic (update reverse proxy config)
# Example for Nginx:
# upstream backend {
#     server localhost:8000;  # New deployment
# }

# 4. Stop old deployment
docker compose -p orbit-green down
```

---

## Environment Configuration

### Required Variables

These must be set in `.env`:

```bash
# LLM API Key (REQUIRED)
ANTHROPIC_API_KEY="sk-ant-api03-..."

# Security (REQUIRED)
SECRET_KEY="<64-char-hex-string>"

# Database (REQUIRED if using custom settings)
POSTGRES_USER="orbit"
POSTGRES_PASSWORD="secure_password"
POSTGRES_DB="orbit_db"
```

### Optional Variables

```bash
# Feature Flags
FEATURE_VOICE_INPUT=true
FEATURE_PROACTIVE_NOTIFICATIONS=true

# Performance Tuning
DATABASE_POOL_SIZE=20
REDIS_MAX_CONNECTIONS=50
WORKERS=4

# Monitoring
SENTRY_DSN="https://..."
PROMETHEUS_ENABLED=true
```

### Environment-Specific Files

```bash
# Development
.env

# Staging
.env.staging

# Production
.env.production
```

Load specific environment:

```bash
# Copy staging config
cp .env.staging .env
docker compose up -d
```

---

## Database Migrations

### Running Migrations

```bash
# Apply all pending migrations
docker compose exec backend alembic upgrade head

# Apply specific migration
docker compose exec backend alembic upgrade <revision_id>

# Rollback one migration
docker compose exec backend alembic downgrade -1

# Rollback to specific version
docker compose exec backend alembic downgrade <revision_id>
```

### Creating Migrations

```bash
# Auto-generate migration from model changes
docker compose exec backend alembic revision --autogenerate -m "Add user roles"

# Create empty migration
docker compose exec backend alembic revision -m "Custom migration"

# View migration history
docker compose exec backend alembic history

# View current version
docker compose exec backend alembic current
```

### Migration Best Practices

1. **Always test migrations on staging first**
2. **Create database backup before production migrations**
3. **Review auto-generated migrations** (may miss complex changes)
4. **Use transactions** (enabled by default in Alembic)
5. **Never edit applied migrations** (create new one instead)

---

## Monitoring & Health Checks

### Health Endpoints

```bash
# Basic health check (always returns 200)
curl http://localhost:8000/health

# Readiness check (verifies DB, Redis, n8n)
curl http://localhost:8000/health/ready

# Metrics (Prometheus format)
curl http://localhost:8000/metrics
```

### Container Health Status

```bash
# Check health status
docker compose ps

# View health check logs
docker inspect orbit_backend --format='{{json .State.Health}}' | jq

# Watch health status in real-time
watch -n 5 'docker compose ps'
```

### Prometheus Metrics

Access metrics at `http://localhost:8000/metrics`:

Key metrics to monitor:
- `http_requests_total` - Total HTTP requests
- `http_request_duration_seconds` - Request latency
- `database_connections_active` - Active DB connections
- `redis_commands_total` - Redis operations

### Log Aggregation

```bash
# Export logs to file
docker compose logs backend > backend.log

# Send logs to external service
docker compose logs -f backend | logger -t orbit-backend

# Configure log driver in docker-compose.yml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

---

## Scaling

### Horizontal Scaling

Scale the backend service to multiple instances:

```bash
# Run 3 backend instances
docker compose up -d --scale backend=3

# Verify instances
docker compose ps

# Load balance with Nginx
# Add Nginx service to docker-compose.yml
```

Example Nginx configuration:

```nginx
upstream backend {
    least_conn;
    server orbit_backend_1:8000;
    server orbit_backend_2:8000;
    server orbit_backend_3:8000;
}

server {
    listen 80;
    location / {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Vertical Scaling

Increase resources for containers:

```yaml
# docker-compose.yml
deploy:
  resources:
    limits:
      cpus: '8.0'      # Increase CPUs
      memory: 8G       # Increase RAM
```

Apply changes:

```bash
docker compose up -d --force-recreate
```

---

## Troubleshooting

### Common Issues

#### 1. Container Won't Start

```bash
# Check logs for errors
docker compose logs backend

# Common causes:
# - Missing environment variable
# - Database connection failed
# - Port already in use
```

**Solution:**
```bash
# Verify .env file has all required variables
grep "ANTHROPIC_API_KEY" .env

# Check if port 8000 is in use
lsof -i :8000

# Kill conflicting process
kill -9 <PID>
```

#### 2. Database Connection Error

```bash
# Error: "could not connect to server"
```

**Solution:**
```bash
# Check if postgres is healthy
docker compose ps postgres

# Restart postgres
docker compose restart postgres

# Wait for health check
sleep 10
docker compose exec backend python -c "from app.core.database import engine; print('Connected')"
```

#### 3. Migration Failed

```bash
# Error: "Target database is not up to date"
```

**Solution:**
```bash
# Check current version
docker compose exec backend alembic current

# View migration history
docker compose exec backend alembic history

# Force stamp to specific version (if needed)
docker compose exec backend alembic stamp head
```

#### 4. Out of Memory

```bash
# Error: "FATAL: insufficient resources"
```

**Solution:**
```bash
# Increase Docker memory limit
# Docker Desktop > Preferences > Resources > Memory > 8GB

# Or reduce worker count
# .env: WORKERS=2
```

#### 5. Build Fails

```bash
# Error during docker build
```

**Solution:**
```bash
# Clear build cache
docker compose build --no-cache

# Prune old images
docker system prune -a

# Check disk space
df -h
```

### Debug Commands

```bash
# Run interactive shell
docker compose exec backend bash

# Test database connection
docker compose exec backend python -c "from app.core.database import engine; print(engine)"

# Test Redis connection
docker compose exec backend python -c "from app.core.redis import redis_manager; print(redis_manager)"

# Check Python packages
docker compose exec backend pip list

# View environment variables
docker compose exec backend env | grep -E "(DATABASE|REDIS|ANTHROPIC)"
```

---

## Backup & Restore

### Database Backup

```bash
# Create backup directory
mkdir -p /Users/robertvill/voice2task/backups

# Backup database
docker compose exec postgres pg_dump -U orbit orbit_db > backups/orbit_db_$(date +%Y%m%d_%H%M%S).sql

# Compressed backup
docker compose exec postgres pg_dump -U orbit orbit_db | gzip > backups/orbit_db_$(date +%Y%m%d_%H%M%S).sql.gz

# Backup with custom format (faster restore)
docker compose exec postgres pg_dump -U orbit -Fc orbit_db > backups/orbit_db_$(date +%Y%m%d_%H%M%S).dump
```

### Database Restore

```bash
# Restore from SQL file
docker compose exec -T postgres psql -U orbit orbit_db < backups/orbit_db_20231215_120000.sql

# Restore from compressed file
gunzip -c backups/orbit_db_20231215_120000.sql.gz | docker compose exec -T postgres psql -U orbit orbit_db

# Restore from custom format
docker compose exec postgres pg_restore -U orbit -d orbit_db /backups/orbit_db_20231215_120000.dump
```

### Volume Backup

```bash
# Backup postgres volume
docker run --rm \
  -v orbit_postgres_data:/data \
  -v /Users/robertvill/voice2task/backups:/backup \
  alpine tar czf /backup/postgres_data_$(date +%Y%m%d).tar.gz -C /data .

# Backup redis volume
docker run --rm \
  -v orbit_redis_data:/data \
  -v /Users/robertvill/voice2task/backups:/backup \
  alpine tar czf /backup/redis_data_$(date +%Y%m%d).tar.gz -C /data .
```

### Volume Restore

```bash
# Restore postgres volume
docker run --rm \
  -v orbit_postgres_data:/data \
  -v /Users/robertvill/voice2task/backups:/backup \
  alpine sh -c "cd /data && tar xzf /backup/postgres_data_20231215.tar.gz"
```

### Automated Backups

Create a cron job for daily backups:

```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * cd /Users/robertvill/voice2task/backend && docker compose exec -T postgres pg_dump -U orbit orbit_db | gzip > /Users/robertvill/voice2task/backups/orbit_db_$(date +\%Y\%m\%d).sql.gz

# Keep only last 7 days
0 3 * * * find /Users/robertvill/voice2task/backups -name "orbit_db_*.sql.gz" -mtime +7 -delete
```

---

## Production Checklist

Before going live:

- [ ] Change `SECRET_KEY` to cryptographically secure value
- [ ] Change `POSTGRES_PASSWORD` to strong password
- [ ] Set `ENVIRONMENT=production`
- [ ] Set `DEBUG=false`
- [ ] Set `LOG_LEVEL=WARNING`
- [ ] Configure `SENTRY_DSN` for error tracking
- [ ] Update `CORS_ORIGINS` with production frontend URL
- [ ] Set production `ANTHROPIC_API_KEY`
- [ ] Comment out volume mounts for hot reload
- [ ] Comment out `--reload` flag in backend command
- [ ] Review and adjust resource limits
- [ ] Enable HTTPS/TLS (use reverse proxy)
- [ ] Set up automated database backups
- [ ] Configure monitoring and alerting
- [ ] Test database migrations on staging
- [ ] Review rate limiting settings
- [ ] Set up log aggregation
- [ ] Configure firewall rules
- [ ] Test disaster recovery procedure

---

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Redis Documentation](https://redis.io/documentation)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)

---

## Support

For issues or questions:
1. Check logs: `docker compose logs -f backend`
2. Review health status: `curl http://localhost:8000/health/ready`
3. Consult troubleshooting section above
4. Open issue on GitHub repository

---

**Last Updated**: 2025-12-27
**Version**: 1.0.0
