-- ==============================================================================
-- DataWise AI — Supabase Row Level Security (RLS) Master Configuration
-- Ensures 100% Tenant Isolation: No user can ever access another user's data.
-- ==============================================================================

-- 1. Enable RLS on all primary tables
ALTER TABLE IF EXISTS users ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS datasets ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS dataset_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS agent_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS pipeline_stages ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS artifacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS models ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS model_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS conversation_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS predictions ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS deployments ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS model_monitoring ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS audit_logs ENABLE ROW LEVEL SECURITY;

-- 2. USERS Table Policies
-- Users can only read and update their own profile
DROP POLICY IF EXISTS "Users can read own profile" ON users;
CREATE POLICY "Users can read own profile"
    ON users FOR SELECT
    USING (auth.uid()::text = id::text OR auth.role() = 'service_role');

DROP POLICY IF EXISTS "Users can update own profile" ON users;
CREATE POLICY "Users can update own profile"
    ON users FOR UPDATE
    USING (auth.uid()::text = id::text OR auth.role() = 'service_role')
    WITH CHECK (auth.uid()::text = id::text OR auth.role() = 'service_role');

-- 3. PROJECTS Table Policies
-- Strict User Isolation: owner_id must match auth.uid()
DROP POLICY IF EXISTS "Users can manage own projects" ON projects;
CREATE POLICY "Users can manage own projects"
    ON projects FOR ALL
    USING (auth.uid()::text = user_id::text OR auth.role() = 'service_role')
    WITH CHECK (auth.uid()::text = user_id::text OR auth.role() = 'service_role');

-- 4. DATASETS Table Policies
DROP POLICY IF EXISTS "Users can manage own datasets" ON datasets;
CREATE POLICY "Users can manage own datasets"
    ON datasets FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM projects
            WHERE projects.id = datasets.project_id
            AND (projects.user_id::text = auth.uid()::text OR auth.role() = 'service_role')
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM projects
            WHERE projects.id = datasets.project_id
            AND (projects.user_id::text = auth.uid()::text OR auth.role() = 'service_role')
        )
    );

-- 5. RUNS & PIPELINES Policies
DROP POLICY IF EXISTS "Users can view own runs" ON runs;
CREATE POLICY "Users can view own runs"
    ON runs FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM projects
            WHERE projects.id = runs.project_id
            AND (projects.user_id::text = auth.uid()::text OR auth.role() = 'service_role')
        )
    );

-- 6. ARTIFACTS Table Policies
-- Protects serialized PKL, HTML reports, and notebooks from cross-user access
DROP POLICY IF EXISTS "Users can access own artifacts" ON artifacts;
CREATE POLICY "Users can access own artifacts"
    ON artifacts FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM projects
            WHERE projects.id = artifacts.project_id
            AND (projects.user_id::text = auth.uid()::text OR auth.role() = 'service_role')
        )
    );

-- 7. MODELS & REGISTRY Policies
DROP POLICY IF EXISTS "Users can manage own models" ON models;
CREATE POLICY "Users can manage own models"
    ON models FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM projects
            WHERE projects.id = models.project_id
            AND (projects.user_id::text = auth.uid()::text OR auth.role() = 'service_role')
        )
    );

-- 8. PREDICTIONS Policies
DROP POLICY IF EXISTS "Users can view own predictions" ON predictions;
CREATE POLICY "Users can view own predictions"
    ON predictions FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM projects
            WHERE projects.id = predictions.project_id
            AND (projects.user_id::text = auth.uid()::text OR auth.role() = 'service_role')
        )
    );

-- 9. AUDIT LOGS Policies
DROP POLICY IF EXISTS "Users can view own audit logs" ON audit_logs;
CREATE POLICY "Users can view own audit logs"
    ON audit_logs FOR SELECT
    USING (auth.uid()::text = user_id::text OR auth.role() = 'service_role');
