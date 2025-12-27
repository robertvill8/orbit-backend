# Production Deployment Quick Start - Orbit V3 Backend

This guide gets your backend deployed to production in under 15 minutes using Railway.app.

## Prerequisites

- [x] Backend running locally with Docker Compose
- [x] GitHub account
- [x] Anthropic API key (from console.anthropic.com)
- [ ] Railway account (sign up at https://railway.app)

## Option A: Deploy via Railway Dashboard (Recommended - No CLI Required)

### Step 1: Create Railway Account (2 minutes)

1. Go to https://railway.app
2. Click "Login with GitHub"
3. Authorize Railway to access your repositories

### Step 2: Create New Project (1 minute)

1. Click "New Project"
2. Select "Deploy from GitHub repo"
3. Choose your `voice2task` repository
4. Railway will auto-detect the Dockerfile in `/backend`

### Step 3: Add PostgreSQL Database (1 minute)

1. In your project dashboard, click "+ New"
2. Select "Database" → "Add PostgreSQL"
3. Railway provisions PostgreSQL 16 with pgvector automatically
4. No configuration needed - Railway auto-connects it

### Step 4: Add Redis Cache (1 minute)

1. Click "+ New" again
2. Select "Database" → "Add Redis"
3. Railway provisions Redis 7 automatically
4. No configuration needed - Railway auto-connects it

### Step 5: Configure Backend Environment Variables (5 minutes)

1. Click on your backend service (the one from GitHub)
2. Go to "Variables" tab
3. Click "Raw Editor"
4. **Generate Required Secrets First:**

   ```bash
   # In your terminal, generate a secure secret key:
   openssl rand -hex 32
   # Copy the output - you'll need this as SECRET_KEY
   ```

5. **Paste this configuration** (replace placeholders):

```bash
APP_NAME=Orbit V3 Backend
APP_VERSION=1.0.0
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING
HOST=0.0.0.0
WORKERS=4

# Database - Railway auto-injects this
DATABASE_URL=${{Postgres.DATABASE_URL}}
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10
DATABASE_ECHO=false

# Redis - Railway auto-injects this
REDIS_URL=${{Redis.REDIS_URL}}
REDIS_MAX_CONNECTIONS=50
SESSION_TTL_SECONDS=86400
MESSAGE_CACHE_TTL_SECONDS=3600

# LLM - REPLACE WITH YOUR ACTUAL API KEY
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-api03-YOUR_ACTUAL_KEY_HERE
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
ANTHROPIC_MAX_TOKENS=4096

# n8n Integration
N8N_BASE_URL=https://n8n-wsex.sliplane.app
N8N_WEBHOOK_EMAIL_READ=/webhook/email-read
N8N_WEBHOOK_CALENDAR_CREATE=/webhook/calendar-create
N8N_WEBHOOK_OCR_PROCESS=/webhook/ocr-process
N8N_API_KEY=
N8N_TIMEOUT_SECONDS=30
N8N_MAX_RETRIES=3

# Security - REPLACE WITH OUTPUT FROM: openssl rand -hex 32
SECRET_KEY=PASTE_YOUR_GENERATED_SECRET_KEY_HERE
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=10080

# CORS - Update with your actual frontend URL
CORS_ORIGINS=https://voice-assistant-ui.vercel.app

# WebSocket
WS_HEARTBEAT_INTERVAL=30
WS_MAX_CONNECTIONS_PER_SESSION=5
WS_CONNECTION_TIMEOUT=300

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_BURST=20

# Features
FEATURE_VOICE_INPUT=true
FEATURE_PROACTIVE_NOTIFICATIONS=true
FEATURE_BACKGROUND_TASKS=false

# Monitoring (optional)
PROMETHEUS_ENABLED=true
```

6. Click "Save" - Railway will automatically redeploy with new variables

### Step 6: Wait for Deployment (3-5 minutes)

1. Railway will build your Docker image
2. Watch the "Deployments" tab for progress
3. You'll see logs streaming in real-time
4. Wait for status to show "ACTIVE" with green checkmark

### Step 7: Run Database Migrations (1 minute)

1. Go to your backend service
2. Click "Shell" tab
3. Run this command:

```bash
alembic upgrade head
```

4. You should see migration messages and "Running upgrade... done"

### Step 8: Get Your Production URL (1 minute)

1. Go to your backend service
2. Click "Settings" tab
3. Scroll to "Networking"
4. Find "Public Networking" section
5. You'll see a URL like: `https://your-app-name.up.railway.app`
6. **Copy this URL** - you'll need it for the frontend

### Step 9: Verify Deployment (2 minutes)

Test these endpoints in your browser or with curl:

```bash
# Health check (should return: {"status":"healthy"})
https://your-app.up.railway.app/health

# API documentation (should open Swagger UI)
https://your-app.up.railway.app/docs

# Readiness check (tests DB and Redis connections)
https://your-app.up.railway.app/health/ready
```

All should return successful responses.

### Step 10: Update Frontend Configuration (3 minutes)

1. Go to your Vercel dashboard (https://vercel.com)
2. Select your `voice-assistant-ui` project
3. Go to "Settings" → "Environment Variables"
4. Add or update these variables for **Production**:

```bash
VITE_API_BASE_URL=https://your-app.up.railway.app/api/v1
VITE_WS_URL=wss://your-app.up.railway.app/ws
```

5. Trigger a new deployment:
   - Go to "Deployments" tab
   - Click "..." on latest deployment
   - Click "Redeploy"

6. Wait for Vercel to redeploy (1-2 minutes)

### Step 11: Test End-to-End (2 minutes)

1. Open your frontend: `https://voice-assistant-ui.vercel.app`
2. Try sending a message in the chat
3. Verify you get a response from the backend
4. Check Railway logs to see the request coming through

**Congratulations!** Your backend is now live in production!

---

## Option B: Deploy via Railway CLI (For Advanced Users)

### Prerequisites

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Navigate to backend directory
cd /Users/robertvill/voice2task/backend
```

### Quick Deploy

```bash
# Link to Railway project (or create new one)
railway link

# Upload environment variables from .env.production
railway variables --file .env.production

# Deploy
railway up

# Run migrations
railway run alembic upgrade head

# Get deployment URL
railway status
```

**Done!** Follow Step 10-11 above to update frontend.

---

## Automated Deployment Script (Easiest)

We've created a script that automates the entire process:

```bash
cd /Users/robertvill/voice2task/backend

# Make sure you have Railway CLI installed
npm i -g @railway/cli

# Login to Railway
railway login

# Edit .env.production with your actual values
nano .env.production
# Update: ANTHROPIC_API_KEY, SECRET_KEY, CORS_ORIGINS

# Run the deployment script
./deploy-to-railway.sh
```

The script will:
- ✓ Validate your configuration
- ✓ Test Docker build locally
- ✓ Upload environment variables
- ✓ Deploy to Railway
- ✓ Run database migrations
- ✓ Verify health checks
- ✓ Provide you with the deployment URL

---

## Post-Deployment Checklist

After deployment, verify:

- [ ] Health check responds: `/health`
- [ ] API docs accessible: `/docs`
- [ ] Readiness check passes: `/health/ready`
- [ ] Frontend can connect to backend
- [ ] Messages send and receive successfully
- [ ] WebSocket connection establishes
- [ ] No errors in Railway logs
- [ ] CORS allows frontend domain
- [ ] Database migrations applied
- [ ] Redis cache is working

---

## Monitoring Your Deployment

### View Logs

**Railway Dashboard:**
1. Go to your backend service
2. Click "Logs" tab
3. Real-time log streaming

**Railway CLI:**
```bash
railway logs
```

### Monitor Resources

**Railway Dashboard:**
1. Go to your backend service
2. Click "Metrics" tab
3. View CPU, Memory, Network usage

### Database Access

**Via Railway Dashboard:**
1. Click PostgreSQL service
2. Click "Connect" tab
3. Copy connection string

**Via Railway CLI:**
```bash
railway connect postgres
```

---

## Troubleshooting

### Issue: Container won't start

**Solution:**
1. Check logs in Railway dashboard
2. Verify all environment variables are set
3. Ensure `DATABASE_URL` uses format: `postgresql+asyncpg://...`
4. Check health check endpoint is responding

### Issue: Database connection failed

**Solution:**
1. Verify PostgreSQL service is running (green status)
2. Check `DATABASE_URL` references PostgreSQL service: `${{Postgres.DATABASE_URL}}`
3. Run migrations: `railway run alembic upgrade head`

### Issue: Frontend CORS error

**Solution:**
1. Update `CORS_ORIGINS` to include your frontend URL
2. Ensure frontend URL uses HTTPS
3. Redeploy backend after changing CORS_ORIGINS

### Issue: 502 Bad Gateway

**Solution:**
1. Verify app listens on `0.0.0.0` (not `localhost`)
2. Check app uses Railway's `$PORT` variable
3. Verify health check passes: curl `/health`

---

## Scaling & Performance

### Current Setup (Free Tier)
- **Resources:** 512MB RAM, shared CPU
- **Cost:** $5/month credit (free for hobby)
- **Capacity:** ~100-500 requests/minute

### Scaling Up (When Needed)

**Vertical Scaling:**
1. Go to backend service → "Settings"
2. Increase RAM/CPU allocation
3. Recommended: 1GB RAM, 1 vCPU ($10/month)

**Horizontal Scaling:**
1. Go to backend service → "Settings" → "Scaling"
2. Increase replica count
3. Railway load balances automatically
4. Note: Requires Pro plan

---

## Cost Breakdown

### Free Tier (Hobby)
- **Monthly Credit:** $5
- **Backend:** Included
- **PostgreSQL:** Included
- **Redis:** Included
- **Total:** **FREE** (within credit limit)

### Pro Tier (Production)
- **Backend (1GB RAM):** ~$10/month
- **PostgreSQL (1GB):** ~$10/month
- **Redis (256MB):** ~$5/month
- **Total:** **~$25/month**

---

## Next Steps

1. **Set up monitoring:**
   - Configure Sentry for error tracking (optional)
   - Enable Prometheus metrics
   - Set up uptime monitoring

2. **Configure backups:**
   - Railway auto-backs up databases daily
   - Consider additional backup strategy for critical data

3. **Set up CI/CD:**
   - Railway auto-deploys on git push to main
   - Configure deployment webhooks for notifications

4. **Add custom domain:**
   - Go to backend service → Settings → Domains
   - Add your custom domain
   - Update DNS records as instructed

5. **Security hardening:**
   - Enable rate limiting
   - Review CORS settings
   - Rotate SECRET_KEY periodically
   - Monitor API usage

---

## Support & Documentation

- **Railway Docs:** https://docs.railway.app
- **Railway Discord:** https://discord.gg/railway
- **This Project:** `/backend/README.md`
- **API Docs:** `https://your-app.up.railway.app/docs`

---

**Estimated Total Time:** 15-20 minutes

**Deployment Date:** 2025-12-27

**Platform:** Railway.app

**Status:** Production Ready ✓
