# Alternative Deployment Platforms - Orbit V3 Backend

This document provides deployment guides for alternative platforms if Railway.app doesn't meet your needs.

## Platform Comparison

| Platform | Pros | Cons | Cost (Est.) | Best For |
|----------|------|------|-------------|----------|
| **Railway.app** | Native Docker Compose, managed DB, auto-scaling | Limited free tier | $5-30/mo | Recommended - Easy setup |
| **Render.com** | Native Docker, managed DB, free tier | Slower cold starts | Free-$25/mo | Budget-conscious |
| **Fly.io** | Edge deployment, global CDN, great performance | More complex setup | $0-20/mo | Global audience |
| **DigitalOcean** | Full control, predictable pricing | Manual setup required | $12-48/mo | Custom requirements |
| **AWS ECS** | Enterprise-grade, full AWS ecosystem | Very complex setup | $30-100/mo | Enterprise projects |

---

## Option 1: Render.com

### Overview
Render provides native Docker support with managed PostgreSQL and Redis, making it a strong Railway alternative.

### Pros
- Native Docker support (no modifications needed)
- Managed PostgreSQL with automatic backups
- Managed Redis
- Free tier for small projects
- Auto-deploy from GitHub
- Built-in SSL certificates

### Cons
- Free tier instances spin down after inactivity (cold starts)
- Slower deploy times than Railway
- Limited free tier resources

### Deployment Steps

1. **Sign Up**
   - Go to https://render.com
   - Sign up with GitHub

2. **Create PostgreSQL Database**
   - Click "New +" → "PostgreSQL"
   - Name: `orbit-postgres`
   - Database: `orbit_db`
   - User: `orbit`
   - Region: Choose closest to your users
   - Plan: Free (for testing) or Starter ($7/month)
   - Create Database

3. **Create Redis Instance**
   - Click "New +" → "Redis"
   - Name: `orbit-redis`
   - Plan: Free (for testing) or Starter ($10/month)
   - Create Redis

4. **Create Web Service**
   - Click "New +" → "Web Service"
   - Connect GitHub repository: `voice2task`
   - Root Directory: `backend`
   - Environment: Docker
   - Region: Same as database
   - Plan: Free (testing) or Starter ($7/month)

5. **Configure Environment Variables**
   In the "Environment" section, add:

   ```
   APP_NAME=Orbit V3 Backend
   APP_VERSION=1.0.0
   ENVIRONMENT=production
   DEBUG=false
   LOG_LEVEL=WARNING
   HOST=0.0.0.0
   PORT=10000
   WORKERS=4

   # Database - Use "Internal Database URL" from PostgreSQL service
   DATABASE_URL=[Internal Database URL from Render PostgreSQL]
   DATABASE_POOL_SIZE=20
   DATABASE_MAX_OVERFLOW=10
   DATABASE_ECHO=false

   # Redis - Use "Internal Redis URL" from Redis service
   REDIS_URL=[Internal Redis URL from Render Redis]
   REDIS_MAX_CONNECTIONS=50
   SESSION_TTL_SECONDS=86400
   MESSAGE_CACHE_TTL_SECONDS=3600

   # LLM
   LLM_PROVIDER=anthropic
   ANTHROPIC_API_KEY=[Your API Key]
   ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
   ANTHROPIC_MAX_TOKENS=4096

   # N8N
   N8N_BASE_URL=https://n8n-wsex.sliplane.app
   N8N_WEBHOOK_EMAIL_READ=/webhook/email-read
   N8N_WEBHOOK_CALENDAR_CREATE=/webhook/calendar-create
   N8N_WEBHOOK_OCR_PROCESS=/webhook/ocr-process
   N8N_API_KEY=
   N8N_TIMEOUT_SECONDS=30
   N8N_MAX_RETRIES=3

   # Security
   SECRET_KEY=[Generate with: openssl rand -hex 32]
   JWT_ALGORITHM=HS256
   JWT_EXPIRE_MINUTES=10080
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
   ```

6. **Deploy**
   - Click "Create Web Service"
   - Render will build and deploy your Docker container
   - Wait for deployment to complete (5-10 minutes)

7. **Run Migrations**
   - Go to "Shell" tab in your web service
   - Run: `alembic upgrade head`

8. **Get Production URL**
   - Your backend will be at: `https://your-app.onrender.com`
   - Copy this URL for frontend configuration

### Cost Estimate
- **Free Tier:** PostgreSQL (90 days), Redis (90 days), Web Service (750 hours/month)
- **Paid:** ~$25/month (Starter PostgreSQL $7, Redis $10, Web Service $7)

---

## Option 2: Fly.io

### Overview
Fly.io is a global edge platform that runs Docker containers close to your users worldwide.

### Pros
- Excellent global performance
- Very generous free tier
- Native Docker support
- Built-in load balancing
- Auto-scaling capabilities
- Multiple regions for low latency

### Cons
- Requires Fly.io CLI for setup
- More complex configuration
- Separate PostgreSQL and Redis setup

### Deployment Steps

1. **Install Fly.io CLI**
   ```bash
   # macOS
   brew install flyctl

   # Linux/Windows
   curl -L https://fly.io/install.sh | sh
   ```

2. **Login to Fly.io**
   ```bash
   flyctl auth login
   ```

3. **Create fly.toml Configuration**
   Create `/Users/robertvill/voice2task/backend/fly.toml`:

   ```toml
   app = "orbit-backend"
   primary_region = "sjc"  # Change to region nearest you

   [build]
     dockerfile = "Dockerfile"

   [env]
     APP_NAME = "Orbit V3 Backend"
     ENVIRONMENT = "production"
     DEBUG = "false"
     LOG_LEVEL = "WARNING"
     PORT = "8080"
     WORKERS = "4"

   [http_service]
     internal_port = 8080
     force_https = true
     auto_stop_machines = true
     auto_start_machines = true
     min_machines_running = 1

     [[http_service.checks]]
       interval = "30s"
       timeout = "10s"
       grace_period = "5s"
       method = "GET"
       path = "/health"

   [[services]]
     internal_port = 8080
     protocol = "tcp"

     [[services.ports]]
       port = 80
       handlers = ["http"]

     [[services.ports]]
       port = 443
       handlers = ["tls", "http"]

   [[vm]]
     cpu_kind = "shared"
     cpus = 1
     memory_mb = 1024
   ```

4. **Create PostgreSQL**
   ```bash
   flyctl postgres create --name orbit-postgres
   # Note the connection string
   ```

5. **Attach PostgreSQL**
   ```bash
   flyctl postgres attach orbit-postgres
   # This sets DATABASE_URL automatically
   ```

6. **Create Redis (Upstash)**
   ```bash
   flyctl redis create --name orbit-redis
   # Note the REDIS_URL
   ```

7. **Set Environment Variables**
   ```bash
   flyctl secrets set \
     ANTHROPIC_API_KEY="your-api-key" \
     SECRET_KEY="$(openssl rand -hex 32)" \
     CORS_ORIGINS="https://voice-assistant-ui.vercel.app" \
     LLM_PROVIDER="anthropic" \
     ANTHROPIC_MODEL="claude-3-5-sonnet-20241022" \
     N8N_BASE_URL="https://n8n-wsex.sliplane.app"
   ```

8. **Deploy**
   ```bash
   flyctl deploy
   ```

9. **Run Migrations**
   ```bash
   flyctl ssh console
   alembic upgrade head
   ```

10. **Get Production URL**
    ```bash
    flyctl info
    # Your backend: https://orbit-backend.fly.dev
    ```

### Cost Estimate
- **Free Tier:** 3 shared-cpu-1x VMs, 3GB persistent storage
- **Paid:** ~$5-15/month for basic setup

---

## Option 3: DigitalOcean App Platform

### Overview
DigitalOcean's App Platform provides a managed PaaS with predictable pricing and full control.

### Pros
- Simple Docker deployment
- Managed databases (PostgreSQL, Redis)
- Predictable pricing
- Good documentation
- Auto-scaling capabilities

### Cons
- No free tier (7-day trial)
- Requires credit card upfront
- Less modern than Railway/Render

### Deployment Steps

1. **Sign Up**
   - Go to https://cloud.digitalocean.com
   - Create account (requires credit card)

2. **Create PostgreSQL Database**
   - Navigate to "Databases"
   - Click "Create Database Cluster"
   - Choose PostgreSQL 16
   - Select plan: Basic ($15/month)
   - Choose datacenter region
   - Create

3. **Create Redis Database**
   - Navigate to "Databases"
   - Click "Create Database Cluster"
   - Choose Redis 7
   - Select plan: Basic ($15/month)
   - Create

4. **Create App**
   - Navigate to "Apps"
   - Click "Create App"
   - Choose GitHub and select `voice2task` repository
   - Select `backend/` directory
   - DigitalOcean auto-detects Dockerfile

5. **Configure Environment Variables**
   Add in App settings:
   ```
   [Same as Render configuration above]
   DATABASE_URL=[DigitalOcean PostgreSQL connection string]
   REDIS_URL=[DigitalOcean Redis connection string]
   ```

6. **Configure Resources**
   - Select plan: Basic ($5/month for 512MB RAM)
   - Enable auto-scaling if needed

7. **Deploy**
   - Click "Create Resources"
   - Wait for deployment (5-10 minutes)

8. **Run Migrations**
   - Use DigitalOcean Console or SSH
   - Run: `alembic upgrade head`

### Cost Estimate
- **Minimum:** ~$35/month (App $5 + PostgreSQL $15 + Redis $15)
- **Production:** ~$50-100/month with scaling

---

## Option 4: Self-Hosted (VPS)

### Overview
Deploy to a Virtual Private Server (DigitalOcean Droplet, AWS EC2, Linode, etc.)

### Pros
- Full control over infrastructure
- Most cost-effective for high traffic
- Can run entire Docker Compose stack
- No vendor lock-in

### Cons
- Requires DevOps knowledge
- Manual security updates
- Manual scaling
- Manual backups

### Quick Setup (DigitalOcean Droplet)

1. **Create Droplet**
   - Size: 2GB RAM minimum ($12/month)
   - Image: Docker on Ubuntu 24.04
   - Region: Closest to users
   - Add SSH key

2. **SSH into Server**
   ```bash
   ssh root@your-droplet-ip
   ```

3. **Clone Repository**
   ```bash
   git clone https://github.com/your-username/voice2task.git
   cd voice2task/backend
   ```

4. **Configure Environment**
   ```bash
   cp .env.example .env
   nano .env
   # Edit production values
   ```

5. **Deploy with Docker Compose**
   ```bash
   docker-compose -f docker-compose.yml up -d
   ```

6. **Run Migrations**
   ```bash
   docker-compose exec backend alembic upgrade head
   ```

7. **Configure Nginx Reverse Proxy**
   ```bash
   apt install nginx certbot python3-certbot-nginx

   # Create Nginx config
   nano /etc/nginx/sites-available/orbit-backend
   ```

   Nginx configuration:
   ```nginx
   server {
       listen 80;
       server_name api.yourdomain.com;

       location / {
           proxy_pass http://localhost:8000;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection 'upgrade';
           proxy_set_header Host $host;
           proxy_cache_bypass $http_upgrade;
       }
   }
   ```

8. **Enable HTTPS**
   ```bash
   certbot --nginx -d api.yourdomain.com
   ```

9. **Set Up Auto-Updates**
   ```bash
   # Create update script
   nano /root/update-backend.sh
   ```

   ```bash
   #!/bin/bash
   cd /root/voice2task/backend
   git pull origin main
   docker-compose down
   docker-compose up -d --build
   ```

### Cost Estimate
- **Minimum:** $12/month (2GB Droplet)
- **Production:** $24-48/month (4-8GB Droplet)

---

## Recommendation Summary

**For MVP/Hobby Projects:**
- **Best:** Railway.app (easiest setup, best developer experience)
- **Alternative:** Render.com (good free tier with cold starts)

**For Production (< 10K users):**
- **Best:** Railway.app or Render.com (managed services, auto-scaling)
- **Alternative:** Fly.io (global performance)

**For Production (> 10K users):**
- **Best:** DigitalOcean App Platform or Self-hosted VPS
- **Alternative:** AWS ECS with RDS (enterprise-grade)

**For Global Audience:**
- **Best:** Fly.io (edge deployment in multiple regions)

---

## Migration Between Platforms

If you need to migrate from one platform to another:

1. **Export Database**
   ```bash
   pg_dump $DATABASE_URL > backup.sql
   ```

2. **Export Redis Data** (optional)
   ```bash
   redis-cli --rdb dump.rdb
   ```

3. **Deploy to New Platform** (follow guides above)

4. **Import Database**
   ```bash
   psql $NEW_DATABASE_URL < backup.sql
   ```

5. **Update Frontend Configuration**
   ```bash
   # Update VITE_API_BASE_URL in Vercel
   vercel env add VITE_API_BASE_URL production
   ```

6. **Run Smoke Tests**
   ```bash
   curl https://new-backend-url/health
   curl https://new-backend-url/health/ready
   ```

7. **Update DNS** (if using custom domain)

---

## Support & Resources

- **Railway:** https://docs.railway.app
- **Render:** https://render.com/docs
- **Fly.io:** https://fly.io/docs
- **DigitalOcean:** https://docs.digitalocean.com/products/app-platform
- **Docker Compose:** https://docs.docker.com/compose

---

**Last Updated:** 2025-12-27
