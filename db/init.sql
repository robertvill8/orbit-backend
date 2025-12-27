-- =============================================================================
-- Orbit v3.0 Database Initialization Script
-- =============================================================================

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgvector";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- =============================================================================
-- SCHEMA: users
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS users;

CREATE TABLE users.users (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  email VARCHAR(255) UNIQUE NOT NULL,
  name VARCHAR(255),
  avatar_url TEXT,
  preferences JSONB DEFAULT '{}',
  imap_config JSONB,
  smtp_config JSONB,
  caldav_config JSONB,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users.users(email);

-- =============================================================================
-- SCHEMA: sessions (conversation context)
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS sessions;

CREATE TABLE sessions.sessions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users.users(id) ON DELETE CASCADE,
  context_data JSONB DEFAULT '{}',
  last_activity TIMESTAMP DEFAULT NOW(),
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_sessions_user ON sessions.sessions(user_id);
CREATE INDEX idx_sessions_last_activity ON sessions.sessions(last_activity DESC);

-- =============================================================================
-- SCHEMA: messages (chat history)
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS messages;

CREATE TABLE messages.messages (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  session_id UUID REFERENCES sessions.sessions(id) ON DELETE CASCADE,
  role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant')),
  content TEXT NOT NULL,
  message_type VARCHAR(20) NOT NULL CHECK (message_type IN ('text', 'audio')),
  audio_url TEXT,
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_messages_session ON messages.messages(session_id);
CREATE INDEX idx_messages_created ON messages.messages(created_at DESC);

-- LLM request tracking (for cost monitoring)
CREATE TABLE messages.llm_requests (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  message_id UUID REFERENCES messages.messages(id) ON DELETE SET NULL,
  user_id UUID REFERENCES users.users(id) ON DELETE CASCADE,
  model VARCHAR(100) NOT NULL,
  input_tokens INT NOT NULL,
  output_tokens INT NOT NULL,
  total_cost DECIMAL(10, 6),
  latency_ms INT,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_llm_requests_user ON messages.llm_requests(user_id, created_at DESC);
CREATE INDEX idx_llm_requests_created ON messages.llm_requests(created_at DESC);

-- =============================================================================
-- SCHEMA: emails
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS emails;

CREATE TABLE emails.emails (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users.users(id) ON DELETE CASCADE,
  message_id VARCHAR(255) UNIQUE NOT NULL,
  thread_id VARCHAR(255),
  subject TEXT,
  from_email VARCHAR(255) NOT NULL,
  from_name VARCHAR(255),
  to_emails TEXT[],
  cc_emails TEXT[],
  bcc_emails TEXT[],
  body_text TEXT,
  body_html TEXT,
  has_attachments BOOLEAN DEFAULT FALSE,
  is_read BOOLEAN DEFAULT FALSE,
  is_archived BOOLEAN DEFAULT FALSE,
  folder VARCHAR(100) DEFAULT 'INBOX',
  date TIMESTAMP NOT NULL,
  synced_at TIMESTAMP DEFAULT NOW(),
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_emails_user ON emails.emails(user_id);
CREATE INDEX idx_emails_thread ON emails.emails(thread_id);
CREATE INDEX idx_emails_date ON emails.emails(date DESC);
CREATE INDEX idx_emails_folder ON emails.emails(folder);
CREATE INDEX idx_emails_unread ON emails.emails(is_read) WHERE is_read = FALSE;

-- Fulltext search index on subject and body
CREATE INDEX idx_emails_search ON emails.emails USING GIN(
  to_tsvector('english', COALESCE(subject, '') || ' ' || COALESCE(body_text, ''))
);

-- Email attachments
CREATE TABLE emails.email_attachments (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  email_id UUID REFERENCES emails.emails(id) ON DELETE CASCADE,
  document_id UUID,
  filename VARCHAR(255) NOT NULL,
  content_type VARCHAR(100),
  size_bytes INT,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_attachments_email ON emails.email_attachments(email_id);

-- Email drafts
CREATE TABLE emails.email_drafts (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users.users(id) ON DELETE CASCADE,
  reply_to_email_id UUID REFERENCES emails.emails(id) ON DELETE SET NULL,
  to_emails TEXT[] NOT NULL,
  cc_emails TEXT[],
  bcc_emails TEXT[],
  subject TEXT NOT NULL,
  body TEXT NOT NULL,
  status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'discarded')),
  created_by VARCHAR(10) DEFAULT 'user' CHECK (created_by IN ('user', 'agent')),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_drafts_user ON emails.email_drafts(user_id);
CREATE INDEX idx_drafts_status ON emails.email_drafts(status);

-- =============================================================================
-- SCHEMA: calendar
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS calendar;

CREATE TABLE calendar.calendar_events (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users.users(id) ON DELETE CASCADE,
  event_id VARCHAR(255) UNIQUE NOT NULL,
  title TEXT NOT NULL,
  description TEXT,
  location TEXT,
  start_time TIMESTAMP NOT NULL,
  end_time TIMESTAMP NOT NULL,
  all_day BOOLEAN DEFAULT FALSE,
  attendees JSONB DEFAULT '[]',
  recurrence_rule TEXT,
  reminder_minutes INT,
  calendar_color VARCHAR(7),
  synced_at TIMESTAMP DEFAULT NOW(),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_events_user ON calendar.calendar_events(user_id);
CREATE INDEX idx_events_start ON calendar.calendar_events(start_time);
CREATE INDEX idx_events_range ON calendar.calendar_events(user_id, start_time, end_time);

-- Calendar invitations
CREATE TABLE calendar.calendar_invitations (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  event_id UUID REFERENCES calendar.calendar_events(id) ON DELETE CASCADE,
  invitee_email VARCHAR(255) NOT NULL,
  status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'declined', 'tentative')),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(event_id, invitee_email)
);

CREATE INDEX idx_invitations_event ON calendar.calendar_invitations(event_id);

-- =============================================================================
-- SCHEMA: tasks
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS tasks;

-- Task lists (Kanban columns)
CREATE TABLE tasks.task_lists (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users.users(id) ON DELETE CASCADE,
  name VARCHAR(100) NOT NULL,
  position INT NOT NULL,
  color VARCHAR(7),
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(user_id, name)
);

CREATE INDEX idx_lists_user ON tasks.task_lists(user_id, position);

-- Tasks
CREATE TABLE tasks.tasks (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users.users(id) ON DELETE CASCADE,
  list_id UUID REFERENCES tasks.task_lists(id) ON DELETE CASCADE,
  parent_id UUID REFERENCES tasks.tasks(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  description TEXT,
  priority VARCHAR(10) DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high')),
  status VARCHAR(20) DEFAULT 'open' CHECK (status IN ('backlog', 'open', 'in_progress', 'waiting', 'done', 'pending', 'dismissed')),
  due_date TIMESTAMP,
  completed_at TIMESTAMP,
  vertical_position INT NOT NULL DEFAULT 0,
  created_by VARCHAR(10) DEFAULT 'user' CHECK (created_by IN ('user', 'agent')),
  extracted_from TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_tasks_user ON tasks.tasks(user_id);
CREATE INDEX idx_tasks_list ON tasks.tasks(list_id, vertical_position);
CREATE INDEX idx_tasks_status ON tasks.tasks(status);
CREATE INDEX idx_tasks_parent ON tasks.tasks(parent_id);
CREATE INDEX idx_tasks_due ON tasks.tasks(due_date) WHERE due_date IS NOT NULL;

-- Task labels
CREATE TABLE tasks.task_labels (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users.users(id) ON DELETE CASCADE,
  name VARCHAR(50) NOT NULL,
  color VARCHAR(7) NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(user_id, name)
);

-- Task-Label many-to-many
CREATE TABLE tasks.task_tags (
  task_id UUID REFERENCES tasks.tasks(id) ON DELETE CASCADE,
  label_id UUID REFERENCES tasks.task_labels(id) ON DELETE CASCADE,
  PRIMARY KEY (task_id, label_id)
);

CREATE INDEX idx_task_tags_task ON tasks.task_tags(task_id);
CREATE INDEX idx_task_tags_label ON tasks.task_tags(label_id);

-- =============================================================================
-- SCHEMA: documents
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS documents;

CREATE TABLE documents.documents (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users.users(id) ON DELETE CASCADE,
  filename VARCHAR(255) NOT NULL,
  storage_path TEXT NOT NULL,
  file_type VARCHAR(50) NOT NULL,
  size_bytes INT NOT NULL,
  extracted_text TEXT,
  summary_short TEXT,
  summary_medium TEXT,
  summary_long TEXT,
  embedding vector(1536),
  processing_status VARCHAR(20) DEFAULT 'queued' CHECK (processing_status IN ('queued', 'processing', 'complete', 'failed')),
  processing_error TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_documents_user ON documents.documents(user_id);
CREATE INDEX idx_documents_type ON documents.documents(file_type);
CREATE INDEX idx_documents_status ON documents.documents(processing_status);

-- Vector search index
CREATE INDEX idx_documents_embedding ON documents.documents
USING hnsw (embedding vector_cosine_ops);

-- Fulltext search on extracted text
CREATE INDEX idx_documents_search ON documents.documents USING GIN(
  to_tsvector('english', COALESCE(filename, '') || ' ' || COALESCE(extracted_text, ''))
);

-- Document tags
CREATE TABLE documents.document_tags (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users.users(id) ON DELETE CASCADE,
  name VARCHAR(50) NOT NULL,
  color VARCHAR(7) NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(user_id, name)
);

-- Document-Tag many-to-many
CREATE TABLE documents.document_tag_assignments (
  document_id UUID REFERENCES documents.documents(id) ON DELETE CASCADE,
  tag_id UUID REFERENCES documents.document_tags(id) ON DELETE CASCADE,
  PRIMARY KEY (document_id, tag_id)
);

CREATE INDEX idx_doc_tags_doc ON documents.document_tag_assignments(document_id);
CREATE INDEX idx_doc_tags_tag ON documents.document_tag_assignments(tag_id);

-- =============================================================================
-- SCHEMA: relationships (knowledge graph)
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS relationships;

CREATE TABLE relationships.relationships (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users.users(id) ON DELETE CASCADE,
  from_type VARCHAR(20) NOT NULL CHECK (from_type IN ('email', 'task', 'calendar', 'document')),
  from_id UUID NOT NULL,
  to_type VARCHAR(20) NOT NULL CHECK (to_type IN ('email', 'task', 'calendar', 'document')),
  to_id UUID NOT NULL,
  relationship_type VARCHAR(50) NOT NULL,
  strength FLOAT DEFAULT 1.0 CHECK (strength >= 0 AND strength <= 1),
  created_by VARCHAR(10) DEFAULT 'agent' CHECK (created_by IN ('user', 'agent')),
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(user_id, from_type, from_id, to_type, to_id, relationship_type)
);

CREATE INDEX idx_relationships_user ON relationships.relationships(user_id);
CREATE INDEX idx_relationships_from ON relationships.relationships(from_type, from_id);
CREATE INDEX idx_relationships_to ON relationships.relationships(to_type, to_id);
CREATE INDEX idx_relationships_strength ON relationships.relationships(strength DESC);

-- Entity embeddings for semantic matching
CREATE TABLE relationships.entity_embeddings (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users.users(id) ON DELETE CASCADE,
  entity_type VARCHAR(20) NOT NULL CHECK (entity_type IN ('email', 'task', 'calendar', 'document')),
  entity_id UUID NOT NULL,
  embedding vector(1536),
  text_content TEXT,
  updated_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(entity_type, entity_id)
);

CREATE INDEX idx_entity_embeddings_type ON relationships.entity_embeddings(entity_type, entity_id);
CREATE INDEX idx_entity_embeddings_vector ON relationships.entity_embeddings
USING hnsw (embedding vector_cosine_ops);

-- =============================================================================
-- SCHEMA: activities (audit log)
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS activities;

CREATE TABLE activities.activities (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users.users(id) ON DELETE CASCADE,
  action_type VARCHAR(50) NOT NULL,
  description TEXT NOT NULL,
  entity_type VARCHAR(20),
  entity_id UUID,
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_activities_user ON activities.activities(user_id, created_at DESC);
CREATE INDEX idx_activities_type ON activities.activities(action_type);
CREATE INDEX idx_activities_entity ON activities.activities(entity_type, entity_id);
CREATE INDEX idx_activities_search ON activities.activities USING GIN(
  to_tsvector('english', description)
);

-- =============================================================================
-- SCHEMA: integrations (n8n workflow tracking)
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS integrations;

CREATE TABLE integrations.integration_logs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users.users(id) ON DELETE CASCADE,
  workflow_name VARCHAR(100) NOT NULL,
  request_payload JSONB,
  response_payload JSONB,
  status VARCHAR(20) CHECK (status IN ('success', 'failed', 'timeout')),
  error_message TEXT,
  latency_ms INT,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_integration_logs_user ON integrations.integration_logs(user_id, created_at DESC);
CREATE INDEX idx_integration_logs_status ON integrations.integration_logs(status);
CREATE INDEX idx_integration_logs_workflow ON integrations.integration_logs(workflow_name);

-- =============================================================================
-- TRIGGERS FOR updated_at TIMESTAMPS
-- =============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users.users
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_drafts_updated_at BEFORE UPDATE ON emails.email_drafts
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_events_updated_at BEFORE UPDATE ON calendar.calendar_events
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_invitations_updated_at BEFORE UPDATE ON calendar.calendar_invitations
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tasks_updated_at BEFORE UPDATE ON tasks.tasks
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_documents_updated_at BEFORE UPDATE ON documents.documents
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_entity_embeddings_updated_at BEFORE UPDATE ON relationships.entity_embeddings
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- HELPER VIEWS (for common queries)
-- =============================================================================

-- Unread emails view
CREATE VIEW emails.unread_emails AS
SELECT * FROM emails.emails
WHERE is_read = FALSE AND is_archived = FALSE
ORDER BY date DESC;

-- Today's tasks view
CREATE VIEW tasks.today_tasks AS
SELECT * FROM tasks.tasks
WHERE status NOT IN ('done', 'dismissed')
AND (due_date::DATE = CURRENT_DATE OR list_id IN (
  SELECT id FROM tasks.task_lists WHERE name = 'Today'
))
ORDER BY vertical_position;

-- Upcoming calendar events (next 7 days)
CREATE VIEW calendar.upcoming_events AS
SELECT * FROM calendar.calendar_events
WHERE start_time BETWEEN NOW() AND NOW() + INTERVAL '7 days'
ORDER BY start_time;

-- Recent activity (last 24 hours)
CREATE VIEW activities.recent_activities AS
SELECT * FROM activities.activities
WHERE created_at > NOW() - INTERVAL '24 hours'
ORDER BY created_at DESC;

-- =============================================================================
-- INITIAL DATA SEEDING (Optional)
-- =============================================================================

-- Create default task lists for demo purposes
-- INSERT INTO tasks.task_lists (id, user_id, name, position, color)
-- VALUES
--   ('00000000-0000-0000-0000-000000000001', 'USER_ID_HERE', 'Backlog', 0, '#94A3B8'),
--   ('00000000-0000-0000-0000-000000000002', 'USER_ID_HERE', 'Today', 1, '#3B82F6'),
--   ('00000000-0000-0000-0000-000000000003', 'USER_ID_HERE', 'In Progress', 2, '#F59E0B'),
--   ('00000000-0000-0000-0000-000000000004', 'USER_ID_HERE', 'Done', 3, '#10B981');
