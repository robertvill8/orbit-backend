# Production Deployment Checklist - Orbit V3 Backend

**Platform:** Railway.app
**Date:** 2025-12-27
**Status:** Ready for Deployment

---

## Pre-Deployment Verification

### Local Environment
- [x] Backend running in Docker locally
- [x] All containers healthy (postgres, redis, backend)
- [x] Health check passes: `curl http://localhost:8000/health`
- [x] API docs accessible: `http://localhost:8000/docs`
- [x] Database migrations applied: `docker-compose exec backend alembic current`

### Code Repository
- [x] All code committed to GitHub
- [x] Repository: `voice2task`
- [x] Branch: `main` (or your production branch)
- [x] Docker build succeeds locally
- [x] No sensitive data in repository (.env excluded)

### Secrets & Configuration
- [x] Production SECRET_KEY generated: `e887dbf77cde12bd53a31fc95986395446771e90691d949faec89582e015f44e`
- [x] Anthropic API key available
- [x] Production environment template created: `.env.production`
- [x] CORS origins defined for frontend

---

## Railway Deployment Steps

### 1. Create Railway Account
- [ ] Sign up at https://railway.app
- [ ] Authenticate with GitHub
- [ ] Verify email (if required)

**Time:** 2 minutes

### 2. Create New Project
- [ ] Click "New Project"
- [ ] Select "Deploy from GitHub repo"
- [ ] Choose `voice2task` repository
- [ ] Confirm Railway detected Dockerfile

**Time:** 1 minute

### 3. Add PostgreSQL Database
- [ ] Click "+ New"
- [ ] Select "Database" → "Add PostgreSQL"
- [ ] Wait for provisioning (green status)
- [ ] Verify service name is "Postgres"

**Time:** 2 minutes

### 4. Add Redis Database
- [ ] Click "+ New"
- [ ] Select "Database" → "Add Redis"
- [ ] Wait for provisioning (green status)
- [ ] Verify service name is "Redis"

**Time:** 1 minute

### 5. Configure Backend Environment Variables
- [ ] Click on backend service (GitHub repo)
- [ ] Go to "Variables" tab
- [ ] Click "Raw Editor"
- [ ] Copy/paste from `/backend/PRODUCTION_ENV_VALUES.txt`
- [ ] Update `SECRET_KEY` with: `e887dbf77cde12bd53a31fc95986395446771e90691d949faec89582e015f44e`
- [ ] Verify `DATABASE_URL=${{Postgres.DATABASE_URL}}`
- [ ] Verify `REDIS_URL=${{Redis.REDIS_URL}}`
- [ ] Click "Save"

**Time:** 5 minutes

### 6. Wait for Deployment
- [ ] Go to "Deployments" tab
- [ ] Watch build logs in real-time
- [ ] Wait for "ACTIVE" status with green checkmark
- [ ] Verify no errors in logs

**Time:** 3-5 minutes

### 7. Run Database Migrations
- [ ] Click on backend service
- [ ] Go to "Shell" tab
- [ ] Run: `alembic upgrade head`
- [ ] Verify migrations applied successfully
- [ ] Check for "Running upgrade ... done" messages

**Time:** 1 minute

### 8. Get Production URL
- [ ] Go to backend service
- [ ] Click "Settings" tab
- [ ] Scroll to "Networking"
- [ ] Copy production URL (e.g., `https://your-app.up.railway.app`)
- [ ] Save this URL for frontend configuration

**Time:** 1 minute

---

## Post-Deployment Verification

### Backend Health Checks
- [ ] Health check: `https://your-app.up.railway.app/health`
  - Expected: `{"status":"healthy","version":"1.0.0","environment":"production"}`
- [ ] API docs: `https://your-app.up.railway.app/docs`
  - Expected: Interactive Swagger UI
- [ ] Readiness check: `https://your-app.up.railway.app/health/ready`
  - Expected: `{"status":"ready","database":"connected","redis":"connected"}`

**Time:** 2 minutes

### Review Logs
- [ ] Go to backend service → "Logs" tab
- [ ] Verify no ERROR or CRITICAL messages
- [ ] Check database connection successful
- [ ] Verify LLM provider initialized

**Time:** 2 minutes

---

## Frontend Integration

### Update Vercel Environment Variables
- [ ] Go to https://vercel.com
- [ ] Select `voice-assistant-ui` project
- [ ] Go to "Settings" → "Environment Variables"
- [ ] Add/Update for **Production**:
  ```
  VITE_API_BASE_URL=https://your-app.up.railway.app/api/v1
  VITE_WS_URL=wss://your-app.up.railway.app/ws
  ```
- [ ] Save changes

**Time:** 2 minutes

### Redeploy Frontend
- [ ] Go to "Deployments" tab
- [ ] Click "..." on latest deployment
- [ ] Click "Redeploy"
- [ ] Wait for deployment to complete (1-2 minutes)

**Time:** 3 minutes

---

## End-to-End Testing

### Frontend → Backend Communication
- [ ] Open: `https://voice-assistant-ui.vercel.app`
- [ ] Type a test message in chat
- [ ] Verify message sends (loading indicator)
- [ ] Verify response appears from backend
- [ ] Check Railway logs show request

**Time:** 2 minutes

### WebSocket Connection
- [ ] Open browser DevTools → Network → WS tab
- [ ] Verify WebSocket connection established
- [ ] Send message and verify WS traffic
- [ ] Check connection stays alive (no disconnects)

**Time:** 2 minutes

### Voice Input (If Enabled)
- [ ] Click microphone button
- [ ] Grant microphone permission
- [ ] Record short message
- [ ] Verify audio uploads
- [ ] Verify transcription and response

**Time:** 2 minutes

---

## Monitoring Setup (Optional but Recommended)

### Railway Built-in Monitoring
- [ ] Go to backend service → "Metrics" tab
- [ ] Review CPU usage (should be < 50%)
- [ ] Review Memory usage (should be < 80%)
- [ ] Set up email alerts for high usage

**Time:** 3 minutes

### Error Tracking with Sentry (Optional)
- [ ] Sign up at https://sentry.io (free tier available)
- [ ] Create new project (select FastAPI)
- [ ] Copy DSN
- [ ] Add to Railway env vars: `SENTRY_DSN=your-dsn-here`
- [ ] Redeploy backend
- [ ] Verify errors appear in Sentry

**Time:** 5 minutes

### Uptime Monitoring (Optional)
- [ ] Sign up at https://uptimerobot.com (free tier available)
- [ ] Create new monitor
- [ ] Type: HTTPS
- [ ] URL: `https://your-app.up.railway.app/health`
- [ ] Interval: 5 minutes
- [ ] Alert contacts: Your email
- [ ] Save

**Time:** 3 minutes

---

## Security Hardening

### Verify Security Settings
- [ ] CORS origins set to frontend only (no wildcards)
- [ ] DEBUG=false in production
- [ ] SECRET_KEY is strong and unique
- [ ] Rate limiting enabled
- [ ] HTTPS enforced (Railway auto-provides)
- [ ] Database credentials not exposed
- [ ] API keys not in logs or code

**Time:** 5 minutes

### Review Access Controls
- [ ] Railway project members (add team if needed)
- [ ] GitHub repository access (private recommended)
- [ ] Environment variable visibility
- [ ] Database access restricted to Railway network

**Time:** 2 minutes

---

## Documentation Updates

### Update Project Documentation
- [ ] Record production URL in team docs
- [ ] Document deployment date and version
- [ ] Update README with production endpoints
- [ ] Share access credentials with team (securely)

**Time:** 5 minutes

---

## Backup & Disaster Recovery

### Database Backups
- [ ] Verify Railway auto-backups enabled (default)
- [ ] Test manual backup: `railway connect postgres` → `pg_dump`
- [ ] Document restore procedure
- [ ] Set backup retention policy

**Time:** 5 minutes

### Disaster Recovery Plan
- [ ] Document rollback procedure
- [ ] Test database restore on staging
- [ ] Create incident response plan
- [ ] Document support contacts

**Time:** 10 minutes (can be done after deployment)

---

## Final Verification

### All Systems Green
- [ ] Backend status: ACTIVE (Railway)
- [ ] Frontend status: ACTIVE (Vercel)
- [ ] Database: Connected and healthy
- [ ] Redis: Connected and healthy
- [ ] Health checks: All passing
- [ ] Logs: No errors
- [ ] End-to-end test: Passed
- [ ] Monitoring: Configured

### Performance Baseline
- [ ] Average response time: < 500ms
- [ ] Database query time: < 100ms
- [ ] LLM response time: < 3s
- [ ] WebSocket latency: < 100ms

### Cost Tracking
- [ ] Current Railway usage: Check dashboard
- [ ] Estimated monthly cost: ~$5 (free tier) or ~$25 (pro)
- [ ] LLM API usage: Monitor Anthropic dashboard
- [ ] Set budget alerts

---

## Deployment Complete!

### Your Production URLs

**Backend API:**
```
https://your-app.up.railway.app
```

**API Documentation:**
```
https://your-app.up.railway.app/docs
```

**Frontend:**
```
https://voice-assistant-ui.vercel.app
```

### Next Steps

1. **Monitor for 24 hours**
   - Watch logs for errors
   - Track resource usage
   - Verify stability

2. **Share with stakeholders**
   - Provide production URLs
   - Share access credentials (securely)
   - Demonstrate functionality

3. **Plan next iteration**
   - Review feature backlog
   - Plan scaling strategy
   - Schedule security audit

---

## Support Contacts

**Railway Support:**
- Discord: https://discord.gg/railway
- Email: support@railway.app
- Docs: https://docs.railway.app

**Project Documentation:**
- Quick Start: `/backend/DEPLOYMENT_QUICKSTART.md`
- Railway Guide: `/backend/DEPLOYMENT_RAILWAY.md`
- Alternatives: `/backend/DEPLOYMENT_ALTERNATIVES.md`

---

**Deployment Status:** ✓ Ready
**Platform:** Railway.app
**Total Time:** ~30-40 minutes (including verification)
**Difficulty:** Easy to Medium

---

**Congratulations on your production deployment!**
