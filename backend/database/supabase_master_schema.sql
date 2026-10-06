-- ==============================================================================
-- DataWise AI — Master Supabase Schema & Tenant Isolation (RLS)
-- Complete PostgreSQL DDL with Auth Integration, RLS Policies, and Storage Setup
-- ==============================================================================

-- 0. Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ==============================================================================
-- 1. PUBLIC.USERS TABLE (Mirrors and extends Supabase auth.users)
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.users (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL DEFAULT 'User',
    role VARCHAR(50) NOT NULL DEFAULT 'data_scientist', -- owner | admin | developer | data_scientist | viewer
    status VARCHAR(50) NOT NULL DEFAULT 'active',      -- active | suspended | pending
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    organization_id VARCHAR(36) NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    last_login_at TIMESTAMPTZ NULL,
    deleted_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS idx_users_email ON public.users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON public.users(role);

-- Automatic synchronization trigger:
-- When a user registers via Supabase Auth, automatically insert into public.users
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.users (id, email, name, role, status, is_active)
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'name', split_part(NEW.email, '@', 1)),
        COALESCE(NEW.raw_user_meta_data->>'role', 'data_scientist'),
        'active',
        TRUE
    )
    ON CONFLICT (id) DO UPDATE SET
        email = EXCLUDED.email,
        updated_at = timezone('utc'::text, now());
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();


-- ==============================================================================
-- 2. PROJECTS TABLE (Workspaces strictly owned by user)
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    organization_id VARCHAR(36) NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    configuration JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    deleted_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS idx_projects_user_id ON public.projects(user_id);
CREATE INDEX IF NOT EXISTS idx_projects_status ON public.projects(status);
CREATE INDEX IF NOT EXISTS idx_projects_created_at ON public.projects(created_at DESC);


-- ==============================================================================
-- 3. DATASETS & VERSIONS (Files & Data Catalog restricted to user & project)
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.datasets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    project_id UUID REFERENCES public.projects(id) ON DELETE CASCADE,
    session_id VARCHAR(36) NULL,
    name VARCHAR(255) NOT NULL DEFAULT '',
    original_filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(50) NOT NULL DEFAULT 'csv',
    mime_type VARCHAR(100) DEFAULT 'text/csv',
    file_size BIGINT NOT NULL DEFAULT 0,
    storage_path TEXT NULL,
    checksum_sha256 VARCHAR(64) NULL,
    row_count INT NULL,
    column_count INT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE INDEX IF NOT EXISTS idx_datasets_user_id ON public.datasets(user_id);
CREATE INDEX IF NOT EXISTS idx_datasets_project_id ON public.datasets(project_id);

CREATE TABLE IF NOT EXISTS public.dataset_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_id UUID NOT NULL REFERENCES public.datasets(id) ON DELETE CASCADE,
    version VARCHAR(50) NOT NULL DEFAULT 'v1',
    storage_key TEXT NOT NULL,
    checksum_sha256 VARCHAR(64) NOT NULL,
    row_count INT NOT NULL DEFAULT 0,
    column_count INT NOT NULL DEFAULT 0,
    schema_info JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    UNIQUE(dataset_id, version)
);

CREATE TABLE IF NOT EXISTS public.dataset_columns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_id UUID NOT NULL REFERENCES public.datasets(id) ON DELETE CASCADE,
    column_name VARCHAR(255) NOT NULL,
    data_type VARCHAR(50) NOT NULL,
    is_nullable BOOLEAN DEFAULT TRUE,
    missing_count INT DEFAULT 0,
    unique_count INT DEFAULT 0,
    statistics JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE TABLE IF NOT EXISTS public.dataset_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_id UUID NOT NULL REFERENCES public.datasets(id) ON DELETE CASCADE,
    summary JSONB DEFAULT '{}'::jsonb,
    correlations JSONB DEFAULT '{}'::jsonb,
    quality_score FLOAT DEFAULT 1.0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);


-- ==============================================================================
-- 4. EXPERIMENTS & RUNS
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.experiments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    target_column VARCHAR(255) NULL,
    task_type VARCHAR(50) NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    configuration JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE INDEX IF NOT EXISTS idx_experiments_user_id ON public.experiments(user_id);
CREATE INDEX IF NOT EXISTS idx_experiments_project_id ON public.experiments(project_id);

CREATE TABLE IF NOT EXISTS public.experiment_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    experiment_id UUID NOT NULL REFERENCES public.experiments(id) ON DELETE CASCADE,
    run_number INT NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'running',
    best_algorithm VARCHAR(100) NULL,
    best_score FLOAT NULL,
    metrics JSONB DEFAULT '{}'::jsonb,
    duration_seconds FLOAT DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);


-- ==============================================================================
-- 5. MODELS & MODEL REGISTRY
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    task_type VARCHAR(50) NOT NULL,
    algorithm VARCHAR(100) NOT NULL,
    current_version VARCHAR(50) DEFAULT 'v1',
    status VARCHAR(50) DEFAULT 'staging',
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE INDEX IF NOT EXISTS idx_models_user_id ON public.models(user_id);
CREATE INDEX IF NOT EXISTS idx_models_project_id ON public.models(project_id);

CREATE TABLE IF NOT EXISTS public.model_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id UUID NOT NULL REFERENCES public.models(id) ON DELETE CASCADE,
    version VARCHAR(50) NOT NULL,
    storage_path TEXT NOT NULL,
    checksum_sha256 VARCHAR(64) NOT NULL,
    metrics JSONB DEFAULT '{}'::jsonb,
    hyperparameters JSONB DEFAULT '{}'::jsonb,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    UNIQUE(model_id, version)
);


-- ==============================================================================
-- 6. ARTIFACTS (Reports, Notebooks, Models, Visualizations)
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.artifacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    run_id VARCHAR(100) NULL,
    name VARCHAR(255) NOT NULL,
    artifact_type VARCHAR(50) NOT NULL, -- notebook | model_weights | pdf_report | html_report | plot | log
    storage_key TEXT NOT NULL,
    file_size BIGINT NOT NULL DEFAULT 0,
    checksum_sha256 VARCHAR(64) NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE INDEX IF NOT EXISTS idx_artifacts_user_id ON public.artifacts(user_id);
CREATE INDEX IF NOT EXISTS idx_artifacts_project_id ON public.artifacts(project_id);


-- ==============================================================================
-- 7. PREDICTIONS (Online & Batch Inference Results)
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.predictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    model_id UUID REFERENCES public.models(id) ON DELETE SET NULL,
    input_payload JSONB NOT NULL,
    prediction_result JSONB NOT NULL,
    latency_ms FLOAT DEFAULT 0.0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE INDEX IF NOT EXISTS idx_predictions_user_id ON public.predictions(user_id);
CREATE INDEX IF NOT EXISTS idx_predictions_project_id ON public.predictions(project_id);


-- ==============================================================================
-- 8. CONVERSATIONS & CHAT (Contextual AI Assistant)
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    project_id UUID REFERENCES public.projects(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL DEFAULT 'New Conversation',
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON public.conversations(user_id);

CREATE TABLE IF NOT EXISTS public.conversation_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES public.conversations(id) ON DELETE CASCADE,
    sender VARCHAR(50) NOT NULL, -- user | assistant | system
    message TEXT NOT NULL,
    tool_calls JSONB NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);


-- ==============================================================================
-- 9. USER DECISIONS & AUDIT LOGS (Traceability & Security)
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.user_decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    decision_key VARCHAR(100) NOT NULL,
    decision_value TEXT NOT NULL,
    rationale TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE INDEX IF NOT EXISTS idx_user_decisions_user_id ON public.user_decisions(user_id);

CREATE TABLE IF NOT EXISTS public.audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100) NOT NULL,
    resource_id VARCHAR(255) NULL,
    details JSONB DEFAULT '{}'::jsonb,
    ip_address VARCHAR(45) NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON public.audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON public.audit_logs(created_at DESC);


-- ==============================================================================
-- 10. ROW LEVEL SECURITY (RLS) POLICIES — 100% USER RESTRICTION & ISOLATION
-- ==============================================================================

-- Enable RLS on all tables
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.datasets ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.dataset_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.dataset_columns ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.dataset_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.experiments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.experiment_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.models ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.model_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.artifacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.predictions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.conversation_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_decisions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audit_logs ENABLE ROW LEVEL SECURITY;

-- ------------------------------------------------------------------------------
-- A. USERS POLICIES
-- ------------------------------------------------------------------------------
DROP POLICY IF EXISTS "Users can view their own profile" ON public.users;
CREATE POLICY "Users can view their own profile"
    ON public.users FOR SELECT
    USING (auth.uid() = id OR auth.role() = 'service_role');

DROP POLICY IF EXISTS "Users can update their own profile" ON public.users;
CREATE POLICY "Users can update their own profile"
    ON public.users FOR UPDATE
    USING (auth.uid() = id OR auth.role() = 'service_role')
    WITH CHECK (auth.uid() = id OR auth.role() = 'service_role');

-- ------------------------------------------------------------------------------
-- B. PROJECTS POLICIES (Users can only see & manage their own projects)
-- ------------------------------------------------------------------------------
DROP POLICY IF EXISTS "Users can manage their own projects" ON public.projects;
CREATE POLICY "Users can manage their own projects"
    ON public.projects FOR ALL
    USING (auth.uid() = user_id OR auth.role() = 'service_role')
    WITH CHECK (auth.uid() = user_id OR auth.role() = 'service_role');

-- ------------------------------------------------------------------------------
-- C. DATASETS & CHILD ENTITIES POLICIES
-- ------------------------------------------------------------------------------
DROP POLICY IF EXISTS "Users can manage their own datasets" ON public.datasets;
CREATE POLICY "Users can manage their own datasets"
    ON public.datasets FOR ALL
    USING (auth.uid() = user_id OR auth.role() = 'service_role')
    WITH CHECK (auth.uid() = user_id OR auth.role() = 'service_role');

DROP POLICY IF EXISTS "Users can access their dataset versions" ON public.dataset_versions;
CREATE POLICY "Users can access their dataset versions"
    ON public.dataset_versions FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM public.datasets
            WHERE public.datasets.id = dataset_versions.dataset_id
            AND (public.datasets.user_id = auth.uid() OR auth.role() = 'service_role')
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.datasets
            WHERE public.datasets.id = dataset_versions.dataset_id
            AND (public.datasets.user_id = auth.uid() OR auth.role() = 'service_role')
        )
    );

DROP POLICY IF EXISTS "Users can access their dataset columns" ON public.dataset_columns;
CREATE POLICY "Users can access their dataset columns"
    ON public.dataset_columns FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM public.datasets
            WHERE public.datasets.id = dataset_columns.dataset_id
            AND (public.datasets.user_id = auth.uid() OR auth.role() = 'service_role')
        )
    );

DROP POLICY IF EXISTS "Users can access their dataset profiles" ON public.dataset_profiles;
CREATE POLICY "Users can access their dataset profiles"
    ON public.dataset_profiles FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM public.datasets
            WHERE public.datasets.id = dataset_profiles.dataset_id
            AND (public.datasets.user_id = auth.uid() OR auth.role() = 'service_role')
        )
    );

-- ------------------------------------------------------------------------------
-- D. EXPERIMENTS & RUNS POLICIES
-- ------------------------------------------------------------------------------
DROP POLICY IF EXISTS "Users can manage their own experiments" ON public.experiments;
CREATE POLICY "Users can manage their own experiments"
    ON public.experiments FOR ALL
    USING (auth.uid() = user_id OR auth.role() = 'service_role')
    WITH CHECK (auth.uid() = user_id OR auth.role() = 'service_role');

DROP POLICY IF EXISTS "Users can manage their own experiment runs" ON public.experiment_runs;
CREATE POLICY "Users can manage their own experiment runs"
    ON public.experiment_runs FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM public.experiments
            WHERE public.experiments.id = experiment_runs.experiment_id
            AND (public.experiments.user_id = auth.uid() OR auth.role() = 'service_role')
        )
    );

-- ------------------------------------------------------------------------------
-- E. MODELS & VERSIONS POLICIES
-- ------------------------------------------------------------------------------
DROP POLICY IF EXISTS "Users can manage their own models" ON public.models;
CREATE POLICY "Users can manage their own models"
    ON public.models FOR ALL
    USING (auth.uid() = user_id OR auth.role() = 'service_role')
    WITH CHECK (auth.uid() = user_id OR auth.role() = 'service_role');

DROP POLICY IF EXISTS "Users can access their own model versions" ON public.model_versions;
CREATE POLICY "Users can access their own model versions"
    ON public.model_versions FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM public.models
            WHERE public.models.id = model_versions.model_id
            AND (public.models.user_id = auth.uid() OR auth.role() = 'service_role')
        )
    );

-- ------------------------------------------------------------------------------
-- F. ARTIFACTS POLICIES (Protects files, weights, reports from cross-access)
-- ------------------------------------------------------------------------------
DROP POLICY IF EXISTS "Users can manage their own artifacts" ON public.artifacts;
CREATE POLICY "Users can manage their own artifacts"
    ON public.artifacts FOR ALL
    USING (auth.uid() = user_id OR auth.role() = 'service_role')
    WITH CHECK (auth.uid() = user_id OR auth.role() = 'service_role');

-- ------------------------------------------------------------------------------
-- G. PREDICTIONS POLICIES
-- ------------------------------------------------------------------------------
DROP POLICY IF EXISTS "Users can view their own predictions" ON public.predictions;
CREATE POLICY "Users can view their own predictions"
    ON public.predictions FOR ALL
    USING (auth.uid() = user_id OR auth.role() = 'service_role')
    WITH CHECK (auth.uid() = user_id OR auth.role() = 'service_role');

-- ------------------------------------------------------------------------------
-- H. CONVERSATIONS & CHAT MESSAGES POLICIES
-- ------------------------------------------------------------------------------
DROP POLICY IF EXISTS "Users can manage their own conversations" ON public.conversations;
CREATE POLICY "Users can manage their own conversations"
    ON public.conversations FOR ALL
    USING (auth.uid() = user_id OR auth.role() = 'service_role')
    WITH CHECK (auth.uid() = user_id OR auth.role() = 'service_role');

DROP POLICY IF EXISTS "Users can manage their conversation messages" ON public.conversation_messages;
CREATE POLICY "Users can manage their conversation messages"
    ON public.conversation_messages FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM public.conversations
            WHERE public.conversations.id = conversation_messages.conversation_id
            AND (public.conversations.user_id = auth.uid() OR auth.role() = 'service_role')
        )
    );

-- ------------------------------------------------------------------------------
-- I. USER DECISIONS & AUDIT LOGS POLICIES
-- ------------------------------------------------------------------------------
DROP POLICY IF EXISTS "Users can manage their own decisions" ON public.user_decisions;
CREATE POLICY "Users can manage their own decisions"
    ON public.user_decisions FOR ALL
    USING (auth.uid() = user_id OR auth.role() = 'service_role')
    WITH CHECK (auth.uid() = user_id OR auth.role() = 'service_role');

DROP POLICY IF EXISTS "Users can view their own audit logs" ON public.audit_logs;
CREATE POLICY "Users can view their own audit logs"
    ON public.audit_logs FOR SELECT
    USING (auth.uid() = user_id OR auth.role() = 'service_role');


-- ==============================================================================
-- 11. SUPABASE STORAGE BUCKETS & ISOLATION POLICIES
-- ==============================================================================
-- Each user has their own top-level folder in storage: "<user_id>/<filename>"
-- Run this in Supabase SQL editor to create buckets and folder security:

INSERT INTO storage.buckets (id, name, public)
VALUES 
    ('DataWise', 'DataWise', false),
    ('datawise', 'datawise', false),
    ('datasets', 'datasets', false),
    ('artifacts', 'artifacts', false),
    ('models', 'models', false)
ON CONFLICT (id) DO NOTHING;

-- Policy: Users can only upload into their own folder ({user_id}/*)
DROP POLICY IF EXISTS "Allow authenticated user to upload to own folder" ON storage.objects;
CREATE POLICY "Allow authenticated user to upload to own folder"
    ON storage.objects FOR INSERT
    WITH CHECK (
        bucket_id IN ('DataWise', 'datawise', 'datasets', 'artifacts', 'models')
        AND (storage.foldername(name))[1] = auth.uid()::text
    );

-- Policy: Users can only read files from their own folder ({user_id}/*)
DROP POLICY IF EXISTS "Allow user to read own files" ON storage.objects;
CREATE POLICY "Allow user to read own files"
    ON storage.objects FOR SELECT
    USING (
        bucket_id IN ('DataWise', 'datawise', 'datasets', 'artifacts', 'models')
        AND (
            (storage.foldername(name))[1] = auth.uid()::text
            OR auth.role() = 'service_role'
        )
    );

-- Policy: Users can only delete their own files
DROP POLICY IF EXISTS "Allow user to delete own files" ON storage.objects;
CREATE POLICY "Allow user to delete own files"
    ON storage.objects FOR DELETE
    USING (
        bucket_id IN ('DataWise', 'datawise', 'datasets', 'artifacts', 'models')
        AND (
            (storage.foldername(name))[1] = auth.uid()::text
            OR auth.role() = 'service_role'
        )
    );

