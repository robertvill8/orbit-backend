# Docker Quick Reference - Orbit V3 Backend

One-page cheat sheet for common Docker commands.

---

## Essential Commands

### Starting & Stopping

```bash
# Start all services
docker compose up -d

# Stop all services
docker compose down

# Restart specific service
docker compose restart backend

# Rebuild and start
docker compose up -d --build
```

### Viewing Status

```bash
# Check service status
docker compose ps

# View logs (follow)
docker compose logs -f backend

# Health check
curl http://localhost:8000/health
```

### Database Migrations

```bash
# Apply migrations
docker compose exec backend alembic upgrade head

# Create migration
docker compose exec backend alembic revision --autogenerate -m "description"

# View migration history
docker compose exec backend alembic history
```

### Debugging

```bash
# Access container shell
docker compose exec backend bash

# View environment variables
docker compose exec backend env

# Test database connection
docker compose exec backend python -c "from app.core.database import engine; print('Connected')"

# View real-time resource usage
docker stats
```

### Data Management

```bash
# Backup database
docker compose exec postgres pg_dump -U orbit orbit_db > backup.sql

# Restore database
docker compose exec -T postgres psql -U orbit orbit_db < backup.sql

# Clear all data (DANGER!)
docker compose down -v
```

---

## File Locations

| File | Purpose |
|------|---------|
| `/Users/robertvill/voice2task/backend/Dockerfile` | Multi-stage build configuration |
| `/Users/robertvill/voice2task/backend/docker-compose.yml` | Service orchestration |
| `/Users/robertvill/voice2task/backend/.env` | Environment variables (DO NOT COMMIT) |
| `/Users/robertvill/voice2task/backend/.env.example` | Environment template |
| `/Users/robertvill/voice2task/backend/.dockerignore` | Build exclusions |

---

## Service URLs

| Service | URL | Description |
|---------|-----|-------------|
| Backend API | http://localhost:8000 | FastAPI application |
| API Docs | http://localhost:8000/docs | Swagger UI |
| ReDoc | http://localhost:8000/redoc | Alternative API docs |
| Health Check | http://localhost:8000/health | Basic health |
| Readiness Check | http://localhost:8000/health/ready | Full health check |
| Metrics | http://localhost:8000/metrics | Prometheus metrics |
| PostgreSQL | localhost:5432 | Database |
| Redis | localhost:6379 | Cache |

---

## Troubleshooting Quick Fixes

### Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>
```

### Container Won't Start

```bash
# View detailed logs
docker compose logs backend

# Check environment variables
docker compose config
```

### Database Connection Error

```bash
# Restart database
docker compose restart postgres

# Check database is healthy
docker compose ps postgres
```

### Build Issues

```bash
# Clear build cache
docker compose build --no-cache

# Clean system
docker system prune -a
```

### Out of Memory

```bash
# Increase Docker memory (Docker Desktop)
# Preferences > Resources > Memory > 8GB

# Or reduce workers in .env
WORKERS=2
```

---

## Production Deployment Steps

```bash
# 1. Update .env for production
ENVIRONMENT=production
DEBUG=false
SECRET_KEY="<generated-key>"

# 2. Build optimized image
docker compose build --no-cache

# 3. Deploy with production config
docker compose up -d

# 4. Run migrations
docker compose exec backend alembic upgrade head

# 5. Verify health
curl http://localhost:8000/health/ready
```

---

## Cleanup Commands

```bash
# Stop and remove containers
docker compose down

# Remove containers and volumes
docker compose down -v

# Remove unused images
docker image prune

# Remove everything (CAUTION!)
docker system prune -a --volumes
```

---

## Environment Variables Quick List

### Required
- `ANTHROPIC_API_KEY` - Claude API key
- `SECRET_KEY` - JWT secret (64 chars)
- `POSTGRES_PASSWORD` - Database password

### Important
- `ENVIRONMENT` - development/staging/production
- `DEBUG` - true/false
- `CORS_ORIGINS` - Frontend URLs
- `SENTRY_DSN` - Error tracking

### Optional
- `WORKERS` - Uvicorn workers (default: 4)
- `DATABASE_POOL_SIZE` - Connection pool (default: 20)
- `REDIS_MAX_CONNECTIONS` - Redis pool (default: 50)

---

## Monitoring Metrics

```bash
# Container resource usage
docker stats orbit_backend

# Disk usage
docker system df

# Container processes
docker compose top backend

# Network usage
docker network inspect orbit_network
```

---

## Common Docker Compose Flags

| Flag | Purpose |
|------|---------|
| `-d` | Run in background (detached) |
| `--build` | Rebuild images |
| `--no-cache` | Build without cache |
| `--scale backend=3` | Run 3 backend instances |
| `-f` | Follow logs |
| `--tail=100` | Show last 100 log lines |
| `-v` | Remove volumes |

---

## Security Checklist

- [ ] Change default passwords
- [ ] Use environment-specific `.env` files
- [ ] Never commit `.env` to git
- [ ] Generate strong `SECRET_KEY`
- [ ] Enable HTTPS in production
- [ ] Restrict CORS origins
- [ ] Set up firewall rules
- [ ] Use non-root user (already configured)
- [ ] Regular security updates
- [ ] Monitor logs for anomalies

---

## Performance Tuning

### Database Optimization

```bash
# Increase connection pool
DATABASE_POOL_SIZE=50
DATABASE_MAX_OVERFLOW=20
```

### Redis Optimization

```bash
# Increase max connections
REDIS_MAX_CONNECTIONS=100

# Adjust memory policy in docker-compose.yml
command: redis-server --maxmemory 1gb --maxmemory-policy allkeys-lru
```

### Backend Optimization

```bash
# More workers (1-2x CPU cores)
WORKERS=8

# Adjust resource limits in docker-compose.yml
resources:
  limits:
    cpus: '4.0'
    memory: 4G
```

---

## Backup Automation

```bash
# Add to crontab (crontab -e)
0 2 * * * cd /Users/robertvill/voice2task/backend && docker compose exec -T postgres pg_dump -U orbit orbit_db | gzip > /Users/robertvill/voice2task/backups/orbit_db_$(date +\%Y\%m\%d).sql.gz

# Keep last 7 days
0 3 * * * find /Users/robertvill/voice2task/backups -name "*.sql.gz" -mtime +7 -delete
```

---

**Last Updated**: 2025-12-27
