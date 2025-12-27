# ============================================================================
# MULTI-STAGE DOCKERFILE FOR FASTAPI BACKEND
# ============================================================================
# Stage 1: Builder - Install dependencies and compile Python packages
# Stage 2: Runtime - Minimal image with only runtime dependencies
# ============================================================================

# ============================================================================
# STAGE 1: BUILDER
# ============================================================================
FROM python:3.11-slim AS builder

# Set working directory
WORKDIR /build

# Install build dependencies
# - build-essential: gcc, g++, make for compiling Python packages
# - libpq-dev: PostgreSQL client library headers
# - curl: for health checks in build stage
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements files first for better layer caching
# This layer will only rebuild if requirements.txt changes
COPY requirements.txt .

# Create virtual environment and install dependencies
# Using --no-cache-dir to reduce image size
# Install all dependencies in a virtual environment
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir --upgrade pip setuptools wheel && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# ============================================================================
# STAGE 2: RUNTIME
# ============================================================================
FROM python:3.11-slim AS runtime

# Set environment variables
# PYTHONUNBUFFERED: Prevents Python from buffering stdout/stderr
# PYTHONDONTWRITEBYTECODE: Prevents Python from writing .pyc files
# PATH: Add virtual environment to PATH
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Install only runtime dependencies (no build tools)
# libpq5: PostgreSQL client library (runtime only)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Create non-root user for security
# - Create system user 'appuser' with no home directory
# - Add to 'appuser' group
# - No shell access for security
RUN groupadd -r appuser && \
    useradd -r -g appuser -u 1001 -s /sbin/nologin appuser

# Copy application code
# Copy in order of least to most frequently changed for better caching
COPY --chown=appuser:appuser alembic.ini .
COPY --chown=appuser:appuser alembic ./alembic
COPY --chown=appuser:appuser app ./app

# Create directory for logs and set permissions
RUN mkdir -p /app/logs && \
    chown -R appuser:appuser /app/logs

# Switch to non-root user
USER appuser

# Expose application port
EXPOSE 8000

# Health check endpoint
# Checks /health endpoint every 30 seconds
# Waits 40 seconds before starting checks (allows app to initialize)
# Considers unhealthy after 3 consecutive failures
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command for production
# Can be overridden in docker-compose.yml or at runtime
# Uses 4 workers for production (adjust based on CPU cores)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

# ============================================================================
# USAGE NOTES:
# ============================================================================
# Build: docker build -t orbit-backend:latest .
# Run: docker run -p 8000:8000 --env-file .env orbit-backend:latest
# Dev: Override CMD in docker-compose.yml with --reload flag
#
# .dockerignore should contain:
# __pycache__
# *.pyc
# *.pyo
# *.pyd
# .Python
# env/
# venv/
# .venv/
# .env
# .env.local
# *.log
# .git
# .gitignore
# .pytest_cache
# .coverage
# htmlcov/
# dist/
# build/
# *.egg-info
# node_modules/
# .vscode/
# .idea/
# *.swp
# *.swo
# .DS_Store
# ============================================================================
