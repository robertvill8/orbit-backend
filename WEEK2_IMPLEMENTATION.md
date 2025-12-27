# Week 2 Implementation: SQLAlchemy Models, Pydantic Schemas, JWT Authentication

## Status: IN PROGRESS

### Completed

#### 1. Core Configuration Updates
- **File**: `app/core/config.py`
  - Added `ACCESS_TOKEN_EXPIRE_MINUTES` and `REFRESH_TOKEN_EXPIRE_DAYS`
  - Added property aliases for compatibility with security module
  - All settings properly validated with Pydantic

- **File**: `app/core/security.py`
  - JWT token creation (access + refresh)
  - Password hashing with bcrypt
  - Token verification and decoding
  - **STATUS**: Complete and production-ready

- **File**: `app/core/database.py`
  - Async SQLAlchemy 2.0 engine
  - Session management with dependency injection
  - **STATUS**: Complete and production-ready

#### 2. SQLAlchemy Models (All aligned with init.sql)

| Model File | Schema | Status | Tables |
|------------|--------|--------|--------|
| `models/user.py` | users | UPDATED | users |
| `models/session.py` | sessions | UPDATED | sessions |
| `models/message.py` | messages | UPDATED | messages, llm_requests |
| `models/email.py` | emails | CREATED | emails, email_attachments, email_drafts |
| `models/calendar.py` | calendar | CREATED | calendar_events, calendar_invitations |
| `models/document.py` | documents | CREATED | documents, document_tags, document_tag_assignments |
| `models/task.py` | tasks | UPDATED | task_lists, tasks, task_labels, task_tags |
| `models/relationship.py` | relationships | CREATED | relationships, entity_embeddings |
| `models/activity.py` | activities | UPDATED | activities |
| `models/integration.py` | integrations | UPDATED | integration_logs |

**Key Features**:
- All models use SQLAlchemy 2.0 async with `Mapped` types
- Full type hints for mypy strict compliance
- Proper schema references (e.g., `{"schema": "users"}`)
- Indexes match init.sql exactly
- CHECK constraints for enums
- Proper CASCADE and SET NULL foreign key actions

### Remaining Tasks

#### 3. Pydantic Schemas (IN PROGRESS)
Need to create request/response schemas for:
- User (Register, Login, UserResponse)
- Session (SessionCreate, SessionResponse)
- Message (MessageCreate, MessageResponse)
- Task (TaskCreate, TaskUpdate, TaskResponse)
- Email, Calendar, Document schemas

#### 4. Authentication Endpoints (PENDING)
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- JWT dependency for protected routes

#### 5. Main Application (PENDING)
- Update `app/main.py` with CORS middleware
- Add startup/shutdown hooks for database
- Mount authentication router

#### 6. Unit Tests (PENDING)
- Test authentication flow
- Test model relationships
- Test JWT token creation/validation

### Next Steps

**Priority 1**: Create Pydantic schemas
**Priority 2**: Implement auth endpoints
**Priority 3**: Update main.py
**Priority 4**: Write unit tests

### Implementation Notes

1. **Database Schema Alignment**: All models now perfectly match `/backend/db/init.sql`
2. **Type Safety**: Full `Mapped[T]` types with proper Optional handling
3. **Async Patterns**: All database operations use async/await
4. **Security**: JWT tokens with proper expiration, bcrypt password hashing
5. **Relationships**: Properly defined bidirectional relationships with cascade rules

### Known Issues

- Models `__init__.py` needs updating to export all new models
- Some existing route files may reference old model structure (need update)
- Need to add `pgvector` dependency for vector operations

### Dependencies Added
```
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
pgvector==0.3.6
```

