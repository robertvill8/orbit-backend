# Orbit v3.0 Backend

AI-Enhanced Productivity Workspace - Production-Ready Backend Service

**Status:** Phase 1 Complete - Core Infrastructure Ready
**Version:** 1.0.0

## Overview

Orbit v3 is an intelligent personal productivity workspace that unifies email, calendar, tasks, and documents with AI-powered assistance. This backend provides:

- **Claude-Powered AI Agent** with tool use for intelligent task extraction and assistance
- **Email Management** with IMAP sync, threading, and AI-powered draft generation
- **Calendar Integration** with CalDAV sync and natural language event creation
- **Task Management** with Kanban boards, sub-tasks, and intelligent prioritization
- **Document Processing** with OCR, summarization, and semantic search (pgvector)
- **Knowledge Graph** with relationship detection across all entities
- **Real-time WebSocket Notifications** for proactive agent updates
- **Activity Audit Log** for complete transparency
- **n8n Integration Layer** for workflow automation

## Tech Stack

- **Python**: 3.11+
- **Framework**: FastAPI 0.115.0 (async ASGI)
- **Database**: PostgreSQL 16 with **pgvector** extension
- **Cache**: Redis 7.x (caching, pub/sub, rate limiting)
- **LLM**: Anthropic Claude 3.5 Sonnet (primary agent)
- **Embeddings**: OpenAI text-embedding-3-small (semantic search)
- **Integration**: n8n workflows (email, calendar, OCR)
- **Testing**: Pytest with 70%+ coverage target
- **Monitoring**: Prometheus metrics, Structlog JSON logging, Sentry error tracking

## Project Structure

```
backend/
├── app/
│   ├── main.py                 # FastAPI application entry point
│   ├── core/
│   │   ├── config.py          # Pydantic Settings configuration
│   │   ├── logging.py         # Structured logging setup
│   │   ├── security.py        # JWT authentication
│   │   └── redis.py           # Redis client
│   ├── db/
│   │   └── base.py            # SQLAlchemy async engine
│   ├── models/                # SQLAlchemy ORM models
│   │   ├── user.py
│   │   ├── session.py
│   │   ├── message.py
│   │   ├── task.py
│   │   ├── activity.py
│   │   └── integration.py
│   ├── schemas/               # Pydantic request/response schemas
│   ├── services/              # Business logic layer
│   │   ├── agent/            # LLM orchestration
│   │   ├── task/             # Task management
│   │   ├── activity/         # Activity logging
│   │   ├── integration/      # n8n client
│   │   ├── notification/     # WebSocket manager
│   │   └── session/          # Session management
│   ├── api/v1/routes/        # FastAPI route handlers
│   └── utils/                # Shared utilities
├── tests/                    # Pytest test suite
├── alembic/                  # Database migrations
├── db/                       # Database initialization scripts
├── .env.example              # Environment variable template
├── requirements.txt          # Python dependencies
├── Dockerfile                # Container image
├── docker-compose.yml        # Local development stack
└── README.md                 # This file
```

## Quick Start

### Prerequisites

- Python 3.11 or higher
- PostgreSQL 16
- Redis 7
- Docker and Docker Compose (optional)

### Installation

1. **Clone the repository:**
```bash
cd /Users/robertvill/voice2task/backend
```

2. **Create and activate virtual environment:**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

4. **Configure environment variables:**
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Start database services (Docker Compose):**
```bash
docker-compose up -d postgres redis
```

6. **Run database migrations:**
```bash
alembic upgrade head
```

7. **Start the development server:**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

- API Documentation: `http://localhost:8000/docs`
- Alternative Docs: `http://localhost:8000/redoc`
- Health Check: `http://localhost:8000/health`

## Environment Variables

Copy `.env.example` to `.env` and configure the following:

### Required

```bash
# Database
DATABASE_URL="postgresql+asyncpg://user:password@localhost:5432/agent_cockpit"

# Redis
REDIS_URL="redis://localhost:6379/0"

# LLM Provider (choose one)
OPENAI_API_KEY="sk-proj-..."
# or
ANTHROPIC_API_KEY="sk-ant-..."

# Security
SECRET_KEY="generate-with-openssl-rand-hex-32"
```

### Optional

```bash
# Application
ENVIRONMENT="development"  # development, staging, production
DEBUG=true
LOG_LEVEL="INFO"

# n8n Integration
N8N_BASE_URL="https://your-n8n-instance.com"

# Feature Flags
FEATURE_VOICE_INPUT=true
FEATURE_PROACTIVE_NOTIFICATIONS=true
```

## Database Setup

### Using Docker Compose (Recommended for Development)

```bash
# Start PostgreSQL and Redis
docker-compose up -d postgres redis

# Verify services are running
docker-compose ps

# View logs
docker-compose logs -f postgres redis
```

### Manual Setup

1. **Install PostgreSQL 16:**
```bash
# macOS
brew install postgresql@16

# Ubuntu/Debian
sudo apt-get install postgresql-16
```

2. **Create database and user:**
```bash
psql -U postgres
CREATE DATABASE agent_cockpit;
CREATE USER agent_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE agent_cockpit TO agent_user;
\q
```

3. **Run SQL schema:**
```bash
psql -U agent_user -d agent_cockpit -f db/init.sql
```

### Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history
```

## Development Workflow

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/unit/services/test_agent_service.py

# Run with verbose output
pytest -v

# Run only fast tests (skip integration tests)
pytest -m "not integration"
```

### Code Quality

```bash
# Format code with black
black app tests

# Sort imports
isort app tests

# Type checking with mypy
mypy app

# Linting with flake8
flake8 app tests

# Run all checks
make lint  # (requires Makefile)
```

### Pre-commit Hooks

```bash
# Install pre-commit hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

## API Documentation

### Base URL
- Development: `http://localhost:8000`
- Production: `https://api.yourdomain.com`

### API Prefix
All endpoints are prefixed with `/api/v1`

### Authentication
```http
Authorization: Bearer <jwt_token>
```

### Key Endpoints

#### Health & Monitoring
- `GET /health` - Liveness probe
- `GET /health/ready` - Readiness probe
- `GET /metrics` - Prometheus metrics

#### Sessions
- `POST /api/v1/sessions` - Create session
- `GET /api/v1/sessions/{session_id}` - Get session
- `PATCH /api/v1/sessions/{session_id}` - Update session
- `DELETE /api/v1/sessions/{session_id}` - Terminate session

#### Chat & Agent
- `POST /api/v1/chat/message` - Send message to agent
- `POST /api/v1/chat/voice` - Upload voice message
- `GET /api/v1/chat/history/{session_id}` - Get conversation history
- `POST /api/v1/chat/stream` - Streaming chat (SSE)

#### Tasks
- `GET /api/v1/tasks` - List tasks (with filters)
- `POST /api/v1/tasks` - Create task
- `GET /api/v1/tasks/{task_id}` - Get task details
- `PATCH /api/v1/tasks/{task_id}` - Update task
- `POST /api/v1/tasks/{task_id}/complete` - Mark complete
- `DELETE /api/v1/tasks/{task_id}` - Delete task
- `GET /api/v1/tasks/statistics` - Get statistics

#### Activities
- `GET /api/v1/activities` - List activities
- `POST /api/v1/activities` - Log activity
- `GET /api/v1/activities/{activity_id}` - Get activity details
- `GET /api/v1/activities/search?q={query}` - Search activities

#### WebSocket
- `WS /api/v1/ws/{session_id}` - WebSocket connection for real-time notifications

See [API_CONTRACTS.md](/API_CONTRACTS.md) for complete API specifications.

## Deployment

### Docker

```bash
# Build image
docker build -t agent-cockpit-backend:latest .

# Run container
docker run -d \
  -p 8000:8000 \
  --env-file .env \
  --name agent-backend \
  agent-cockpit-backend:latest
```

### Docker Compose (Production)

```bash
# Start all services
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose logs -f backend

# Scale backend
docker-compose up -d --scale backend=3
```

### Environment-specific Deployment

#### Development
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Production (with Gunicorn)
```bash
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile -
```

## Architecture Decisions

### Why Async SQLAlchemy?
- Non-blocking I/O for database operations
- Better performance for I/O-bound LLM and API calls
- Scales better with concurrent requests

### Why Pydantic v2?
- Runtime validation of all API requests
- Automatic OpenAPI schema generation
- Type safety throughout the application

### Why Redis for Sessions?
- Fast in-memory access for hot session data
- Built-in expiration (TTL) for session management
- Pub/Sub for WebSocket notifications

### Why n8n for Integrations?
- Low-code workflow management
- Non-technical team members can modify integrations
- Decouples external API complexity from backend code

## Monitoring & Observability

### Structured Logging
All logs are JSON-formatted with structured context:

```python
logger.info(
    "user_action",
    user_id="123",
    action="task_created",
    task_id="456",
    duration_ms=150
)
```

### Prometheus Metrics
Available at `/metrics`:
- `http_requests_total` - Total HTTP requests by endpoint
- `http_request_duration_seconds` - Request latency histogram
- `llm_requests_total` - LLM API calls
- `llm_tokens_used_total` - Token usage (cost tracking)
- `websocket_connections_active` - Active WebSocket connections

### Error Tracking
Configure Sentry DSN in `.env` for automatic error reporting:

```bash
SENTRY_DSN="https://your-sentry-dsn@sentry.io/project"
```

## Troubleshooting

### Database Connection Issues

```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Test connection
psql -U agent_user -d agent_cockpit -h localhost

# View logs
docker-compose logs postgres
```

### Redis Connection Issues

```bash
# Check Redis is running
docker-compose ps redis

# Test connection
redis-cli ping

# View logs
docker-compose logs redis
```

### Migration Issues

```bash
# Reset database (WARNING: deletes all data)
alembic downgrade base
alembic upgrade head

# Check migration status
alembic current
alembic history
```

## Testing Strategy

### Unit Tests
- Test business logic in isolation
- Mock external dependencies (LLM, n8n, Redis)
- Fast execution (< 1 second per test)

### Integration Tests
- Test API endpoints end-to-end
- Use test database (auto-created/destroyed)
- Test real database queries

### Coverage Requirements
- Minimum 90% code coverage
- 100% coverage for critical paths (auth, payment, data loss)

## Performance Targets

| Metric | Target | Critical Threshold |
|--------|--------|-------------------|
| API Response Time (P95) | < 500ms | < 1000ms |
| LLM Response Time (P95) | < 5s | < 10s |
| WebSocket Latency | < 100ms | < 250ms |
| Database Query Time (P95) | < 50ms | < 100ms |

## Security

### Authentication
- JWT tokens with 7-day expiration
- Refresh tokens stored in Redis
- HttpOnly cookies for web clients

### Rate Limiting
- 100 requests per minute per session
- Token bucket algorithm backed by Redis
- Separate limits for LLM endpoints

### Input Validation
- All inputs validated with Pydantic
- SQL injection prevention via ORM
- XSS prevention via output sanitization

### Secrets Management
- Never commit secrets to Git
- Use environment variables
- Rotate secrets regularly

## Contributing

1. Create a feature branch: `git checkout -b feature/my-feature`
2. Write code following PEP 8 style guide
3. Add tests (maintain 90%+ coverage)
4. Run linters: `make lint`
5. Submit pull request with description

## License

Proprietary - All rights reserved

## Support

- Documentation: `/docs` endpoint
- Issues: GitHub Issues
- Email: support@yourdomain.com

---

Built with ❤️ using FastAPI, SQLAlchemy, and modern Python best practices.
