# Railway.app Deployment Guide - Orbit V3 Backend

## Overview

This guide provides step-by-step instructions to deploy the Orbit V3 Backend to Railway.app, a modern Platform-as-a-Service (PaaS) with native Docker support.

## Why Railway?

- **Native Docker Compose Support** - Zero configuration needed
- **Managed PostgreSQL 16** with pgvector extension support
- **Managed Redis 7** with persistence
- **Automatic HTTPS** with custom domain support
- **Built-in CI/CD** from GitHub
- **WebSocket Support** for real-time features
- **$5/month free credits** for hobby projects
- **Simple scaling** and monitoring

## Prerequisites

1. GitHub account with your backend code pushed
2. Railway account (sign up at https://railway.app)
3. Anthropic API key (from console.anthropic.com)
4. Production secret key (generate with `openssl rand -hex 32`)

## Deployment Steps

### Step 1: Create Railway Project

1. **Login to Railway**
   - Go to https://railway.app
   - Click "Login" and authenticate with GitHub

2. **Create New Project**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose `voice2task` repository
   - Select `backend/` as root directory (if prompted)

### Step 2: Add PostgreSQL Database

1. **Add PostgreSQL Service**
   - In your Railway project, click "+ New"
   - Select "Database" → "Add PostgreSQL"
   - Railway will provision PostgreSQL 16 instance
   - Note: Railway's PostgreSQL includes pgvector by default

2. **Verify Database**
   - Click on PostgreSQL service
   - Go to "Variables" tab
   - You'll see auto-generated credentials:
     - `DATABASE_URL` (automatically provided)
     - `PGUSER`, `PGPASSWORD`, `PGDATABASE`, etc.

### Step 3: Add Redis Database

1. **Add Redis Service**
   - In your Railway project, click "+ New"
   - Select "Database" → "Add Redis"
   - Railway will provision Redis 7 instance

2. **Verify Redis**
   - Click on Redis service
   - Go to "Variables" tab
   - You'll see `REDIS_URL` (automatically provided)

### Step 4: Configure Backend Service

1. **Add Backend Service**
   - Click "+ New"
   - Select "GitHub Repo"
   - Choose your `voice2task` repository
   - Railway will auto-detect the Dockerfile

2. **Configure Environment Variables**
   - Click on the backend service
   - Go to "Variables" tab
   - Click "RAW Editor" for bulk input
   - Paste the following (replace placeholders):

```bash
# ============================================================================
# APPLICATION SETTINGS
# ============================================================================
APP_NAME=Orbit V3 Backend
APP_VERSION=1.0.0
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING

# ============================================================================
# SERVER CONFIGURATION
# ============================================================================
HOST=0.0.0.0
WORKERS=4

# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================
# Railway auto-injects DATABASE_URL - Reference PostgreSQL service
DATABASE_URL=${{Postgres.DATABASE_URL}}
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10
DATABASE_ECHO=false

# ============================================================================
# REDIS CONFIGURATION
# ============================================================================
# Railway auto-injects REDIS_URL - Reference Redis service
REDIS_URL=${{Redis.REDIS_URL}}
REDIS_MAX_CONNECTIONS=50
SESSION_TTL_SECONDS=86400
MESSAGE_CACHE_TTL_SECONDS=3600

# ============================================================================
# LLM PROVIDER SETTINGS
# ============================================================================
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=<YOUR_ANTHROPIC_API_KEY_HERE>
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
ANTHROPIC_MAX_TOKENS=4096

# ============================================================================
# N8N INTEGRATION
# ============================================================================
N8N_BASE_URL=https://n8n-wsex.sliplane.app
N8N_WEBHOOK_EMAIL_READ=/webhook/email-read
N8N_WEBHOOK_CALENDAR_CREATE=/webhook/calendar-create
N8N_WEBHOOK_OCR_PROCESS=/webhook/ocr-process
N8N_API_KEY=
N8N_TIMEOUT_SECONDS=30
N8N_MAX_RETRIES=3

# ============================================================================
# AUTHENTICATION & SECURITY
# ============================================================================
# CRITICAL: Generate with: openssl rand -hex 32
SECRET_KEY=<YOUR_PRODUCTION_SECRET_KEY_HERE>
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=10080

# CORS Origins - Add your production frontend URL
CORS_ORIGINS=https://voice-assistant-ui.vercel.app,http://localhost:5173,http://localhost:3000

# ============================================================================
# WEBSOCKET SETTINGS
# ============================================================================
WS_HEARTBEAT_INTERVAL=30
WS_MAX_CONNECTIONS_PER_SESSION=5
WS_CONNECTION_TIMEOUT=300

# ============================================================================
# RATE LIMITING
# ============================================================================
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_BURST=20

# ============================================================================
# MONITORING & OBSERVABILITY
# ============================================================================
SENTRY_DSN=
SENTRY_TRACES_SAMPLE_RATE=0.1
PROMETHEUS_ENABLED=true

# ============================================================================
# FEATURE FLAGS
# ============================================================================
FEATURE_VOICE_INPUT=true
FEATURE_PROACTIVE_NOTIFICATIONS=true
FEATURE_BACKGROUND_TASKS=false

# ============================================================================
# NOTIFICATION SETTINGS
# ============================================================================
NOTIFICATION_RETENTION_DAYS=30
```

3. **Critical Values to Replace:**
   - `ANTHROPIC_API_KEY` - Your actual API key from console.anthropic.com
   - `SECRET_KEY` - Generate with `openssl rand -hex 32` in your terminal
   - `CORS_ORIGINS` - Add your production frontend URL

### Step 5: Configure Service Dependencies

1. **Set Service Dependencies**
   - Click on backend service
   - Go to "Settings" tab
   - Scroll to "Service Dependencies"
   - Add dependencies:
     - PostgreSQL service
     - Redis service
   - This ensures DB and Redis start before backend

### Step 6: Run Database Migrations

After first deployment:

1. **Access Railway Shell**
   - Go to backend service
   - Click "Shell" tab (or use Railway CLI)

2. **Run Migrations**
   ```bash
   alembic upgrade head
   ```

   Or using Railway CLI locally:
   ```bash
   railway run alembic upgrade head
   ```

### Step 7: Configure Custom Domain (Optional)

1. **Add Custom Domain**
   - Go to backend service
   - Click "Settings" tab
   - Scroll to "Domains"
   - Click "Generate Domain" for free Railway subdomain
   - Or add your custom domain (requires DNS configuration)

2. **HTTPS Certificate**
   - Railway automatically provisions Let's Encrypt SSL
   - Your backend will be available at: `https://your-app.up.railway.app`

### Step 8: Enable Auto-Deployment

1. **Configure GitHub Integration**
   - Go to backend service
   - Click "Settings" tab
   - Scroll to "Deploy Triggers"
   - Ensure "Deploy on Git Push" is enabled
   - Set branch to `main` or `develop`

2. **Deployment Strategy**
   - Push to `main` → Production deployment
   - Railway will auto-build and deploy

## Post-Deployment Configuration

### 1. Get Production Backend URL

After deployment completes:

1. Go to backend service in Railway dashboard
2. Click "Settings" tab
3. Find "Public Networking" section
4. Your backend URL will be: `https://your-app.up.railway.app`
5. Copy this URL

### 2. Update Frontend Environment Variables

Update your Vercel deployment with the production backend URL:

```bash
# In your frontend repository, update .env.production
VITE_API_BASE_URL=https://your-app.up.railway.app/api/v1
VITE_WS_URL=wss://your-app.up.railway.app/ws
```

Then deploy to Vercel:
```bash
vercel --prod
```

### 3. Update CORS Origins in Backend

In Railway backend service environment variables, update `CORS_ORIGINS`:
```
CORS_ORIGINS=https://voice-assistant-ui.vercel.app,https://your-production-frontend.vercel.app
```

### 4. Verify Health Checks

Test your deployment:

```bash
# Health check
curl https://your-app.up.railway.app/health

# API documentation
curl https://your-app.up.railway.app/docs

# Readiness check (includes DB and Redis connectivity)
curl https://your-app.up.railway.app/health/ready
```

Expected response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "environment": "production"
}
```

## Monitoring & Maintenance

### View Logs

1. **Via Railway Dashboard**
   - Click on backend service
   - Go to "Logs" tab
   - Real-time log streaming

2. **Via Railway CLI**
   ```bash
   railway logs
   ```

### Database Management

1. **Connect to PostgreSQL**
   ```bash
   # Via Railway dashboard
   railway connect postgres

   # Or get connection string
   railway variables | grep DATABASE_URL
   ```

2. **Run Migrations**
   ```bash
   railway run alembic upgrade head
   railway run alembic revision --autogenerate -m "description"
   ```

3. **Database Backups**
   - Railway automatically backs up databases daily
   - Manual backup: Use `pg_dump` via Railway shell

### Scaling

1. **Horizontal Scaling**
   - Go to backend service
   - Click "Settings" → "Scaling"
   - Increase replicas (requires Pro plan)

2. **Vertical Scaling**
   - Railway auto-scales resources
   - Monitor usage in "Metrics" tab

### Resource Monitoring

1. **View Metrics**
   - Go to backend service
   - Click "Metrics" tab
   - Monitor: CPU, Memory, Network, Request rate

2. **Set Alerts**
   - Configure alerts for high CPU/memory usage
   - Set up Sentry for error tracking

## Troubleshooting

### Container Won't Start

**Issue:** Container exits immediately

**Solution:**
1. Check logs: Railway dashboard → Logs tab
2. Verify environment variables are set correctly
3. Ensure `DATABASE_URL` and `REDIS_URL` reference service variables
4. Check Dockerfile health check passes

### Database Connection Errors

**Issue:** `could not connect to server`

**Solution:**
1. Verify PostgreSQL service is running (green status)
2. Check `DATABASE_URL` format: `postgresql+asyncpg://user:pass@host:port/db`
3. Ensure service dependencies are configured
4. Run `railway connect postgres` to test connection

### Migration Failures

**Issue:** Alembic migrations fail

**Solution:**
1. Check if database schema exists
2. Run migrations manually: `railway run alembic upgrade head`
3. Verify PostgreSQL version supports pgvector
4. Check migration files in `alembic/versions/`

### CORS Errors

**Issue:** Frontend can't connect to backend

**Solution:**
1. Verify `CORS_ORIGINS` includes your frontend URL
2. Ensure HTTPS is used (Railway provides automatic SSL)
3. Check frontend is using correct backend URL
4. Test with curl to isolate issue

### 502 Bad Gateway

**Issue:** Railway shows 502 error

**Solution:**
1. Verify app is listening on `0.0.0.0` (not `localhost`)
2. Check app uses Railway's `$PORT` variable (set in command)
3. Ensure health check endpoint `/health` responds
4. Check logs for startup errors

## Cost Estimation

### Free Tier (Hobby)
- **Credits:** $5/month
- **Resources:**
  - Backend: ~$5/month (512MB RAM, shared CPU)
  - PostgreSQL: Included in shared resources
  - Redis: Included in shared resources
- **Total:** Free (within $5 credit)

### Pro Tier (Production)
- **Cost:** ~$20-30/month
- **Resources:**
  - Backend: 1GB RAM, 1 vCPU - $10/month
  - PostgreSQL: 1GB RAM - $10/month
  - Redis: 256MB RAM - $5/month
- **Features:**
  - Custom domains
  - Horizontal scaling
  - Priority support
  - Enhanced monitoring

## Production Checklist

Before going live, ensure:

- [ ] Environment set to `production`
- [ ] Debug mode disabled (`DEBUG=false`)
- [ ] Strong `SECRET_KEY` generated and set
- [ ] Strong database password set
- [ ] CORS origins configured with production frontend URL
- [ ] Log level set to `WARNING` or `ERROR`
- [ ] Sentry DSN configured (optional but recommended)
- [ ] Database migrations applied successfully
- [ ] Health check endpoint responds
- [ ] API documentation accessible at `/docs`
- [ ] WebSocket connection tested
- [ ] Rate limiting enabled
- [ ] Automated backups enabled (Railway Pro)
- [ ] Monitoring and alerts configured

## Railway CLI (Optional)

For advanced operations, install Railway CLI:

```bash
# Install
npm i -g @railway/cli

# Login
railway login

# Link to project
railway link

# View environment variables
railway variables

# Run commands in production context
railway run alembic upgrade head

# View logs
railway logs

# Connect to database
railway connect postgres
```

## Next Steps

1. Deploy backend to Railway following steps above
2. Get production backend URL from Railway dashboard
3. Update frontend environment variables in Vercel
4. Test end-to-end connection
5. Monitor logs and metrics for 24 hours
6. Set up error tracking with Sentry
7. Configure automated backups
8. Plan scaling strategy based on usage

## Support Resources

- Railway Documentation: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- Railway Status: https://status.railway.app
- This Project Docs: `/backend/README.md`

---

**Deployment Date:** 2025-12-27
**Deployed By:** DevOps Agent
**Platform:** Railway.app
**Region:** Auto-selected (usually US-West or EU-West based on location)
