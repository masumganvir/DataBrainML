-- ============================================================
-- DataWise AI — Complete Supabase PostgreSQL Schema
-- Run this in Supabase SQL Editor as a single transaction.
-- ============================================================

-- ─────────────────────────────────────────────────────────────
-- 0. Extensions
-- ─────────────────────────────────────────────────────────────
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ─────────────────────────────────────────────────────────────
-- 1. ENUM TYPES
-- ─────────────────────────────────────────────────────────────
DO $$ BEGIN
  CREATE TYPE project_status    AS ENUM ('active','archived','training','failed','completed');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE dataset_status    AS ENUM ('uploading','ready','processing','failed','deleted');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE run_status        AS ENUM ('queued','running','completed','failed','cancelled');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE artifact_type     AS ENUM ('dataset','model','notebook','report','plot','code','pipeline','other');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE user_role         AS ENUM ('admin','data_scientist','analyst','viewer');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE storage_provider  AS ENUM ('supabase','s3','local');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- ─────────────────────────────────────────────────────────────
-- 2. USERS — extends Supabase auth.users
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.users (
  id                  UUID        PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  email               TEXT        NOT NULL UNIQUE,
  name                TEXT        NOT NULL DEFAULT 'Data Scientist',
  avatar_url          TEXT,
  role                user_role   NOT NULL DEFAULT 'data_scientist',
  organization_id     TEXT,
  organization_name   TEXT,
  mfa_enabled         BOOLEAN     NOT NULL DEFAULT FALSE,
  preferences         JSONB       NOT NULL DEFAULT '{}',
  storage_used_bytes  BIGINT      NOT NULL DEFAULT 0,
  storage_limit_bytes BIGINT      NOT NULL DEFAULT 5368709120, -- 5 GB default
  created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─────────────────────────────────────────────────────────────
-- 3. PROJECTS
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.projects (
  id                      UUID          PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id                 UUID          NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
  name                    TEXT          NOT NULL,
  description             TEXT,
  status                  project_status NOT NULL DEFAULT 'active',
  target_column           TEXT,
  task_type               TEXT,              -- classification, regression, clustering
  tags                    TEXT[]        NOT NULL DEFAULT '{}',
  dataset_count           INTEGER       NOT NULL DEFAULT 0,
  experiment_count        INTEGER       NOT NULL DEFAULT 0,
  model_count             INTEGER       NOT NULL DEFAULT 0,
  active_deployment       BOOLEAN       NOT NULL DEFAULT FALSE,
  current_champion_model  TEXT,
  metadata                JSONB         NOT NULL DEFAULT '{}',
  created_at              TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
  updated_at              TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_projects_user_id  ON public.projects(user_id);
CREATE INDEX IF NOT EXISTS idx_projects_status   ON public.projects(status);

-- ─────────────────────────────────────────────────────────────
-- 4. DATASETS — metadata for uploaded files
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.datasets (
  id               UUID           PRIMARY KEY DEFAULT uuid_generate_v4(),
  project_id       UUID           NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
  user_id          UUID           NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
  name             TEXT           NOT NULL,
  original_name    TEXT           NOT NULL,
  description      TEXT,
  status           dataset_status NOT NULL DEFAULT 'uploading',
  -- Storage
  storage_provider storage_provider NOT NULL DEFAULT 'supabase',
  storage_path     TEXT           NOT NULL,   -- path in Supabase Storage bucket
  storage_bucket   TEXT           NOT NULL DEFAULT 'datasets',
  file_size_bytes  BIGINT         NOT NULL DEFAULT 0,
  file_extension   TEXT           NOT NULL,
  mime_type        TEXT,
  -- Dataset statistics (populated after upload)
  num_rows         INTEGER,
  num_columns      INTEGER,
  column_names     TEXT[],
  column_types     JSONB,
  missing_count    INTEGER,
  duplicate_count  INTEGER,
  profile_summary  JSONB          NOT NULL DEFAULT '{}',
  -- Version tracking
  version          INTEGER        NOT NULL DEFAULT 1,
  parent_id        UUID           REFERENCES public.datasets(id),
  -- Timestamps
  created_at       TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
  updated_at       TIMESTAMPTZ    NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_datasets_project_id ON public.datasets(project_id);
CREATE INDEX IF NOT EXISTS idx_datasets_user_id    ON public.datasets(user_id);
CREATE INDEX IF NOT EXISTS idx_datasets_status     ON public.datasets(status);

-- ─────────────────────────────────────────────────────────────
-- 5. RUNS / EXPERIMENTS
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.runs (
  id            UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
  project_id    UUID        NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
  user_id       UUID        NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
  dataset_id    UUID        REFERENCES public.datasets(id),
  name          TEXT        NOT NULL DEFAULT 'Untitled Run',
  status        run_status  NOT NULL DEFAULT 'queued',
  run_type      TEXT        NOT NULL DEFAULT 'full',  -- full, eda, preprocessing, training
  config        JSONB       NOT NULL DEFAULT '{}',
  metrics       JSONB       NOT NULL DEFAULT '{}',
  logs          TEXT,
  error_message TEXT,
  started_at    TIMESTAMPTZ,
  completed_at  TIMESTAMPTZ,
  duration_sec  FLOAT,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_runs_project_id ON public.runs(project_id);
CREATE INDEX IF NOT EXISTS idx_runs_user_id    ON public.runs(user_id);
CREATE INDEX IF NOT EXISTS idx_runs_status     ON public.runs(status);

-- ─────────────────────────────────────────────────────────────
-- 6. ARTIFACTS — all generated files linked to Supabase Storage
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.artifacts (
  id               UUID          PRIMARY KEY DEFAULT uuid_generate_v4(),
  project_id       UUID          NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
  run_id           UUID          REFERENCES public.runs(id) ON DELETE SET NULL,
  user_id          UUID          NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
  name             TEXT          NOT NULL,
  artifact_type    artifact_type NOT NULL DEFAULT 'other',
  description      TEXT,
  -- Storage
  storage_provider storage_provider NOT NULL DEFAULT 'supabase',
  storage_path     TEXT          NOT NULL,
  storage_bucket   TEXT          NOT NULL,
  file_size_bytes  BIGINT        NOT NULL DEFAULT 0,
  file_extension   TEXT          NOT NULL,
  mime_type        TEXT,
  -- Download URL (ephemeral signed URL, refreshed on demand)
  tags             TEXT[]        NOT NULL DEFAULT '{}',
  metadata         JSONB         NOT NULL DEFAULT '{}',
  created_at       TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
  updated_at       TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_artifacts_project_id    ON public.artifacts(project_id);
CREATE INDEX IF NOT EXISTS idx_artifacts_user_id       ON public.artifacts(user_id);
CREATE INDEX IF NOT EXISTS idx_artifacts_artifact_type ON public.artifacts(artifact_type);

-- ─────────────────────────────────────────────────────────────
-- 7. MODELS — registered ML models
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.models (
  id               UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
  project_id       UUID        NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
  run_id           UUID        REFERENCES public.runs(id),
  user_id          UUID        NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
  name             TEXT        NOT NULL,
  algorithm        TEXT        NOT NULL,
  task_type        TEXT        NOT NULL,
  framework        TEXT        NOT NULL DEFAULT 'sklearn',
  version          TEXT        NOT NULL DEFAULT '1.0.0',
  is_champion      BOOLEAN     NOT NULL DEFAULT FALSE,
  -- Metrics
  train_score      FLOAT,
  val_score        FLOAT,
  test_score       FLOAT,
  metrics          JSONB       NOT NULL DEFAULT '{}',
  hyperparameters  JSONB       NOT NULL DEFAULT '{}',
  feature_names    TEXT[]      NOT NULL DEFAULT '{}',
  -- Storage (PKL / JOBLIB file)
  storage_path     TEXT,
  storage_bucket   TEXT        DEFAULT 'models',
  model_size_bytes BIGINT      NOT NULL DEFAULT 0,
  -- Deployment
  is_deployed      BOOLEAN     NOT NULL DEFAULT FALSE,
  endpoint_url     TEXT,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_models_project_id ON public.models(project_id);
CREATE INDEX IF NOT EXISTS idx_models_user_id    ON public.models(user_id);

-- ─────────────────────────────────────────────────────────────
-- 8. CONVERSATIONS — chat history per project
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.conversations (
  id            UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
  project_id    UUID        NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
  user_id       UUID        NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
  title         TEXT        NOT NULL DEFAULT 'New Conversation',
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.conversation_messages (
  id              UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
  conversation_id UUID        NOT NULL REFERENCES public.conversations(id) ON DELETE CASCADE,
  user_id         UUID        NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
  role            TEXT        NOT NULL CHECK (role IN ('user','assistant','system','tool')),
  content         TEXT        NOT NULL,
  tool_calls      JSONB,
  tool_results    JSONB,
  metadata        JSONB       NOT NULL DEFAULT '{}',
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_conv_project_id  ON public.conversations(project_id);
CREATE INDEX IF NOT EXISTS idx_conv_user_id     ON public.conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_cmsg_conv_id     ON public.conversation_messages(conversation_id);

-- ─────────────────────────────────────────────────────────────
-- 9. AUDIT LOGS
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.audit_logs (
  id          UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id     UUID        REFERENCES public.users(id) ON DELETE SET NULL,
  action      TEXT        NOT NULL,
  resource    TEXT        NOT NULL,
  resource_id TEXT,
  metadata    JSONB       NOT NULL DEFAULT '{}',
  ip_address  INET,
  user_agent  TEXT,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_user_id   ON public.audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_action    ON public.audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_created   ON public.audit_logs(created_at DESC);

-- ─────────────────────────────────────────────────────────────
-- 10. AUTO-UPDATE updated_at TRIGGER
-- ─────────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION public.handle_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$;

DO $$ DECLARE
  t TEXT;
BEGIN
  FOREACH t IN ARRAY ARRAY['users','projects','datasets','runs','artifacts','models','conversations']
  LOOP
    EXECUTE format('
      DROP TRIGGER IF EXISTS trg_updated_at_%I ON public.%I;
      CREATE TRIGGER trg_updated_at_%I
        BEFORE UPDATE ON public.%I
        FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();
    ', t, t, t, t);
  END LOOP;
END $$;

-- ─────────────────────────────────────────────────────────────
-- 11. AUTO-CREATE USER PROFILE ON AUTH SIGNUP
-- ─────────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
BEGIN
  INSERT INTO public.users (id, email, name, avatar_url)
  VALUES (
    NEW.id,
    NEW.email,
    COALESCE(NEW.raw_user_meta_data->>'name', split_part(NEW.email, '@', 1)),
    NEW.raw_user_meta_data->>'avatar_url'
  )
  ON CONFLICT (id) DO NOTHING;
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- ─────────────────────────────────────────────────────────────
-- 12. ROW LEVEL SECURITY
-- ─────────────────────────────────────────────────────────────
ALTER TABLE public.users                 ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.projects              ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.datasets              ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.runs                  ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.artifacts             ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.models                ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.conversations         ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.conversation_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audit_logs            ENABLE ROW LEVEL SECURITY;

-- USERS
DROP POLICY IF EXISTS "users_select_own" ON public.users;
CREATE POLICY "users_select_own" ON public.users FOR SELECT
  USING (auth.uid() = id OR auth.jwt() ->> 'role' = 'service_role');

DROP POLICY IF EXISTS "users_update_own" ON public.users;
CREATE POLICY "users_update_own" ON public.users FOR UPDATE
  USING (auth.uid() = id)
  WITH CHECK (auth.uid() = id);

DROP POLICY IF EXISTS "users_insert_own" ON public.users;
CREATE POLICY "users_insert_own" ON public.users FOR INSERT
  WITH CHECK (auth.uid() = id);

-- PROJECTS
DROP POLICY IF EXISTS "projects_all_own" ON public.projects;
CREATE POLICY "projects_all_own" ON public.projects FOR ALL
  USING (auth.uid() = user_id OR auth.jwt() ->> 'role' = 'service_role')
  WITH CHECK (auth.uid() = user_id OR auth.jwt() ->> 'role' = 'service_role');

-- DATASETS
DROP POLICY IF EXISTS "datasets_all_own" ON public.datasets;
CREATE POLICY "datasets_all_own" ON public.datasets FOR ALL
  USING (auth.uid() = user_id OR auth.jwt() ->> 'role' = 'service_role')
  WITH CHECK (auth.uid() = user_id OR auth.jwt() ->> 'role' = 'service_role');

-- RUNS
DROP POLICY IF EXISTS "runs_all_own" ON public.runs;
CREATE POLICY "runs_all_own" ON public.runs FOR ALL
  USING (auth.uid() = user_id OR auth.jwt() ->> 'role' = 'service_role')
  WITH CHECK (auth.uid() = user_id OR auth.jwt() ->> 'role' = 'service_role');

-- ARTIFACTS
DROP POLICY IF EXISTS "artifacts_all_own" ON public.artifacts;
CREATE POLICY "artifacts_all_own" ON public.artifacts FOR ALL
  USING (auth.uid() = user_id OR auth.jwt() ->> 'role' = 'service_role')
  WITH CHECK (auth.uid() = user_id OR auth.jwt() ->> 'role' = 'service_role');

-- MODELS
DROP POLICY IF EXISTS "models_all_own" ON public.models;
CREATE POLICY "models_all_own" ON public.models FOR ALL
  USING (auth.uid() = user_id OR auth.jwt() ->> 'role' = 'service_role')
  WITH CHECK (auth.uid() = user_id OR auth.jwt() ->> 'role' = 'service_role');

-- CONVERSATIONS
DROP POLICY IF EXISTS "conversations_all_own" ON public.conversations;
CREATE POLICY "conversations_all_own" ON public.conversations FOR ALL
  USING (auth.uid() = user_id OR auth.jwt() ->> 'role' = 'service_role')
  WITH CHECK (auth.uid() = user_id OR auth.jwt() ->> 'role' = 'service_role');

DROP POLICY IF EXISTS "conv_messages_all_own" ON public.conversation_messages;
CREATE POLICY "conv_messages_all_own" ON public.conversation_messages FOR ALL
  USING (auth.uid() = user_id OR auth.jwt() ->> 'role' = 'service_role')
  WITH CHECK (auth.uid() = user_id OR auth.jwt() ->> 'role' = 'service_role');

-- AUDIT LOGS
DROP POLICY IF EXISTS "audit_logs_select_own" ON public.audit_logs;
CREATE POLICY "audit_logs_select_own" ON public.audit_logs FOR SELECT
  USING (auth.uid() = user_id OR auth.jwt() ->> 'role' = 'service_role');

DROP POLICY IF EXISTS "audit_logs_insert" ON public.audit_logs;
CREATE POLICY "audit_logs_insert" ON public.audit_logs FOR INSERT
  WITH CHECK (TRUE); -- anyone authenticated can insert their own logs
