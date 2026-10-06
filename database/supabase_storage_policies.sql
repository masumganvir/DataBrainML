-- ============================================================
-- DataWise AI — Supabase Storage Bucket RLS Policies
-- Run AFTER creating the buckets in the Dashboard.
-- ============================================================

-- ─────────────────────────────────────────────────────────────
-- datasets bucket
-- ─────────────────────────────────────────────────────────────
DROP POLICY IF EXISTS "datasets_select_own" ON storage.objects;
CREATE POLICY "datasets_select_own" ON storage.objects FOR SELECT
  USING (
    bucket_id = 'datasets'
    AND auth.uid()::text = (storage.foldername(name))[1]
  );

DROP POLICY IF EXISTS "datasets_insert_own" ON storage.objects;
CREATE POLICY "datasets_insert_own" ON storage.objects FOR INSERT
  WITH CHECK (
    bucket_id = 'datasets'
    AND auth.uid()::text = (storage.foldername(name))[1]
  );

DROP POLICY IF EXISTS "datasets_update_own" ON storage.objects;
CREATE POLICY "datasets_update_own" ON storage.objects FOR UPDATE
  USING (
    bucket_id = 'datasets'
    AND auth.uid()::text = (storage.foldername(name))[1]
  );

DROP POLICY IF EXISTS "datasets_delete_own" ON storage.objects;
CREATE POLICY "datasets_delete_own" ON storage.objects FOR DELETE
  USING (
    bucket_id = 'datasets'
    AND auth.uid()::text = (storage.foldername(name))[1]
  );

-- ─────────────────────────────────────────────────────────────
-- models bucket (pkl, joblib)
-- ─────────────────────────────────────────────────────────────
DROP POLICY IF EXISTS "models_select_own" ON storage.objects;
CREATE POLICY "models_select_own" ON storage.objects FOR SELECT
  USING (
    bucket_id = 'models'
    AND auth.uid()::text = (storage.foldername(name))[1]
  );

DROP POLICY IF EXISTS "models_insert_own" ON storage.objects;
CREATE POLICY "models_insert_own" ON storage.objects FOR INSERT
  WITH CHECK (
    bucket_id = 'models'
    AND auth.uid()::text = (storage.foldername(name))[1]
  );

DROP POLICY IF EXISTS "models_delete_own" ON storage.objects;
CREATE POLICY "models_delete_own" ON storage.objects FOR DELETE
  USING (
    bucket_id = 'models'
    AND auth.uid()::text = (storage.foldername(name))[1]
  );

-- ─────────────────────────────────────────────────────────────
-- notebooks bucket (ipynb)
-- ─────────────────────────────────────────────────────────────
DROP POLICY IF EXISTS "notebooks_select_own" ON storage.objects;
CREATE POLICY "notebooks_select_own" ON storage.objects FOR SELECT
  USING (
    bucket_id = 'notebooks'
    AND auth.uid()::text = (storage.foldername(name))[1]
  );

DROP POLICY IF EXISTS "notebooks_insert_own" ON storage.objects;
CREATE POLICY "notebooks_insert_own" ON storage.objects FOR INSERT
  WITH CHECK (
    bucket_id = 'notebooks'
    AND auth.uid()::text = (storage.foldername(name))[1]
  );

DROP POLICY IF EXISTS "notebooks_delete_own" ON storage.objects;
CREATE POLICY "notebooks_delete_own" ON storage.objects FOR DELETE
  USING (
    bucket_id = 'notebooks'
    AND auth.uid()::text = (storage.foldername(name))[1]
  );

-- ─────────────────────────────────────────────────────────────
-- artifacts bucket (html, png, svg, pdf, md)
-- ─────────────────────────────────────────────────────────────
DROP POLICY IF EXISTS "artifacts_select_own" ON storage.objects;
CREATE POLICY "artifacts_select_own" ON storage.objects FOR SELECT
  USING (
    bucket_id = 'artifacts'
    AND auth.uid()::text = (storage.foldername(name))[1]
  );

DROP POLICY IF EXISTS "artifacts_insert_own" ON storage.objects;
CREATE POLICY "artifacts_insert_own" ON storage.objects FOR INSERT
  WITH CHECK (
    bucket_id = 'artifacts'
    AND auth.uid()::text = (storage.foldername(name))[1]
  );

DROP POLICY IF EXISTS "artifacts_delete_own" ON storage.objects;
CREATE POLICY "artifacts_delete_own" ON storage.objects FOR DELETE
  USING (
    bucket_id = 'artifacts'
    AND auth.uid()::text = (storage.foldername(name))[1]
  );
