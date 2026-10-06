# DataWise AI — Comprehensive System Audit & Root Cause Analysis

**Audit Date:** 2026-10-06  
**System Target:** DataWise AI Full-Stack Agentic AutoML Platform  
**Repository Root:** `c:\Users\Chokha\Desktop\DATAPREPAGENT`

---

## 1. Current Architecture

DataWise AI is designed as an enterprise full-stack Agentic AI Data Science & AutoML preparation application.

```
   ┌─────────────────────────────────────────────────────────────┐
   │                     React 18 + Vite SPA                     │
   │  (Lucide Icons, Tailwind-like styling, React-Plotly, Axios) │
   └──────────────────────────────┬──────────────────────────────┘
                                  │ REST + WebSocket Proxy (:5173 -> :8000)
   ┌──────────────────────────────▼──────────────────────────────┐
   │                   FastAPI Backend (:8000)                   │
   │   (Endpoints: /api/projects, /api/auth, /api/artifacts)     │
   ├──────────────────────────────┬──────────────────────────────┤
   │ Multi-Agent Coordinator      │ LangGraph Analysis Workflow  │
   │ Deterministic ML Tools       │ Background Worker Tasks      │
   └───────┬──────────────────────┴───────────────┬──────────────┘
           │                                      │
   ┌───────▼──────────────────────┐       ┌───────▼──────────────┐
   │  Supabase PostgreSQL / Local │       │  MinIO S3 / Local    │
   │  SQLite Database             │       │  Disk Object Storage │
   └──────────────────────────────┘       └──────────────────────┘
```

The system components:
1. **Frontend:** React 18 with Vite, React Router v6, Axios, Lucide React, and Supabase client SDK.
2. **Backend API:** FastAPI with Pydantic v2 and Settings validation, JWT / Supabase RBAC authentication middleware, and Starlette CORS.
3. **Storage Engine:** AWS S3 / MinIO object storage abstraction (`StorageService`) with resilient local fallback directory.
4. **Database Layer:** SQLAlchemy async engine supporting PostgreSQL via `asyncpg` (Supabase pooler) with fallback to local SQLite (`datawise.db`).
5. **Agent Engine:** LangGraph `StateGraph` workflow coordinating profiling, quality checks, human-in-the-loop decisions, EDA, feature engineering, model training, evaluation, and artifact generation with an LLM abstraction (`GeminiProvider`, `GroqProvider`, `CloudflareWorkersAIProvider`).

---

## 2. Existing Project Model

- **Database Entity (`Project` in `app/db/models/entities.py`):**
  - Fields: `id` (UUID), `user_id` (foreign key to `users.id`), `organization_id`, `name`, `description`, `status`, `configuration` (JSON dict), `created_at`, `updated_at`, `deleted_at`.
  - Relationships: `datasets`, `experiments`, `models`, `artifacts`, `notebooks`, `reports`, `jobs`.
- **Gaps Identified:**
  - Missing `project_slug` for deterministic human-friendly URL routing and multi-user disambiguation.
  - Missing `objective`, `visibility`, `current_dataset_id`, `current_run_id`, `latest_model_id`, `latest_model_version`, and structured `metadata`.
  - In `backend/app/api/endpoints/projects.py`, project records rely on an in-memory dictionary `_RUN_STATES[project_id]`. If a project exists in the database but was created in another process or restarted, dataset and run details are not reconstructed from the database relations.

---

## 3. Existing Dataset Model

- **Database Entities (`DatasetEntity`, `DatasetVersion` in `entities.py`):**
  - `DatasetEntity`: `id`, `project_id`, `session_id`, `name`, `original_filename`, `file_type`, `mime_type`, `file_size`, `storage_key`, `storage_bucket`, `checksum` (SHA-256), `row_count`, `column_count`, `status`, `version`, `metadata`, `schema_info`, `profile_summary`, `quality_summary`.
  - `DatasetVersion`: `id`, `dataset_id`, `version`, `storage_key`, `checksum`, `row_count`, `column_count`, `schema`.
- **Gaps Identified:**
  - Duplicate detection is not actively wired into the upload endpoint: re-uploading an identical dataset does not calculate SHA-256 before disk write and does not present the user with an interactive dialog (Use Existing, Create Version, Retrain, Cancel).
  - Datasets are stored in a flat `./datasets` or workspace root folder rather than a strictly scoped `users/{user_id}/projects/{project_id}/datasets/` namespace.

---

## 4. Existing Artifact Model

- **Database Entity (`ArtifactEntity` in `entities.py`):**
  - Fields: `id`, `project_id`, `session_id`, `artifact_type`, `filename`, `storage_provider`, `bucket`, `storage_key`, `content_type`, `size_bytes`, `checksum`, `metadata`, `file_path`.
- **Gaps Identified:**
  - Missing explicit `user_id` and `run_id` columns on `ArtifactEntity`.
  - Global queries in several endpoints retrieve artifacts or recent reports without filtering simultaneously by `user_id == current_user.id` and `project_id == requested_project_id`.
  - Artifact download URLs default to flat query parameters or mock files when storage keys are incomplete.

---

## 5. Existing Storage Model

- **Storage Service (`app/storage/service.py`):**
  - Supports S3/MinIO via `boto3` and local disk fallback.
  - Current storage key format: `projects/{project_id}/{category}/{uuid}_{filename}`.
- **Gaps Identified:**
  - Master specification requires user-scoped hierarchy: `users/{user_id}/projects/{project_id}/{category}/...`.
  - Some endpoints bypass `StorageService` and directly write to local paths like `datasets/{filename}` or `./artifacts/reports/{filename}` without user or project prefixing, causing potential collisions.

---

## 6. Existing Authentication Model

- **Supabase Auth + JWT (`app/auth/rbac.py` & `frontend/src/services/authStore.ts`):**
  - Frontend authenticates with Supabase Auth and stores JWT in session/state.
  - Backend validates Supabase JWT and resolves user to `User` entity or `default_user` when unauthenticated.
- **Gaps Identified:**
  - Several backend endpoints treat unauthenticated access as "demo mode" and return hardcoded demo project data rather than enforcing strict 401/403 authorization.
  - IDOR vulnerabilities exist where a user can supply an arbitrary `project_id` in path parameters and backend methods check only if the project exists in `_RUN_STATES` or return template data.

---

## 7. Existing Routing

- **Frontend Routes (`frontend/src/App.tsx`):**
  - Top-level routes: `/projects`, `/projects/new`, `/projects/:projectId`, `/projects/:projectId/eda`, etc.
  - Legacy routes under `/app/*` (e.g., `/app/projects`, `/app/dashboard`).
- **Gaps Identified:**
  - Some components link to `/app/projects/${proj.id}` while others link to `/projects/${proj.id}`.
  - Many sub-views do not extract `projectId` from URL parameters via `useParams()`, relying instead on `authStore.getState().currentProject`. Navigating directly via URL or opening multiple tabs breaks context isolation.

---

## 8. Existing Caching

- **Redis Cache & InMemoryFallbackCache (`app/cache/redis_client.py`):**
  - Uses in-memory fallback cache when Redis is offline.
- **Gaps Identified:**
  - Cache keys are not consistently namespaced with `project:{project_id}:user:{user_id}`.
  - Frontend has no query-invalidation mechanism on project switch: React component state and Axios responses linger across project switches.

---

## 9. Existing State Management

- **Frontend Store (`authStore.ts`):**
  - Single global `currentProject` stored in `localStorage` under key `datalab_active_project`.
  - Initialized with static `DEMO_PROJECTS` containing `"Customer Churn Intelligence"`.
- **Gaps Identified:**
  - When the user opens the app or switches projects, `localStorage` holds the old project. If API requests fail or take time, the old project remains active.
  - `localStorage` is not namespaced by `datawise:{userId}:{projectId}:...`.

---

## 10. Existing Agent Architecture

- **LangGraph StateGraph (`app/graph/workflow.py`):**
  - Sequential pipeline: Profile -> Quality -> Human Approval -> Outliers -> Distributions -> Correlations -> Feature Engineering -> Feature Selection -> Target Detection -> Leakage -> Pipeline -> ML Recommendation -> Training -> Evaluation -> Explainability -> Notebook -> Artifacts.
- **Gaps Identified:**
  - Missing the initial **AI Project Planner Agent** (`project_planner_agent`) that executes before the pipeline to analyze the dataset profile, user prompt, and business objective, proposing a project plan with human approval.
  - Missing **System Improvement Agent** (`system_improvement_agent`) and **System Testing Agent** (`system_testing_agent`).
  - Agent state does not strictly isolate context per `user_id`, `project_id`, `dataset_id`, and `run_id`.

---

## 11. DETECTED BUGS & ROOT CAUSE OF "CUSTOMER CHURN PREDICTION"

### The Primary Root Cause

The leakage of "Customer Churn Prediction" across unrelated datasets is caused by a multi-layer cascade of hardcoded defaults, asynchronous React state race conditions, and unauthenticated demo fallbacks:

1. **React State Closure Race Condition in `NewProject.tsx` (Lines 145, 174-192, 201-222):**
   - In `NewProject.tsx`, the component initial state is hardcoded:
     ```typescript
     const [projectName, setProjectName] = useState('Customer Churn Prediction')
     const [prompt, setPrompt] = useState('Analyze this customer dataset and build a model that predicts customer churn...')
     ```
   - When a user uploads a new dataset (e.g. `housing.csv`), `handleFileUpload` calculates a clean title and queues:
     ```typescript
     setProjectName(titleCase) // e.g. "Housing"
     ```
   - Immediately in the exact same synchronous JavaScript event frame, it calls:
     ```typescript
     const projId = await ensureProjectCreated()
     ```
   - Because React state updates are asynchronous and batched, `ensureProjectCreated()` reads `projectName` from the **current render closure**, which is STILL `'Customer Churn Prediction'`!
   - As a result, the backend receives a `create_project` API call with:
     ```json
     { "name": "Customer Churn Prediction", "prompt": "Analyze this customer dataset and build a model that predicts customer churn..." }
     ```
   - The project is created in the database with the name "Customer Churn Prediction", regardless of what dataset was uploaded!

2. **Backend Demo Fallbacks in `backend/app/api/endpoints/projects.py` (Lines 266-306 & 410-430):**
   - In `get_project(project_id)`, if `user` is None or the project is not in memory:
     ```python
     return {
         "id": project_id,
         "name": "Customer Churn Prediction",
         "description": "Predict churn risk with high recall; identify retention indicators.",
         ...
     }
     ```
   - In `list_projects`, if the database returns an empty list or the user is not authenticated, it returns `default_projects` with `"Customer Churn Intelligence"`.

3. **Frontend Store Initial State in `authStore.ts` (Lines 46-80):**
   - `DEMO_PROJECTS` has `{ id: 'proj_default', name: 'Customer Churn Intelligence' }`.
   - `authStore` initializes `currentProject` from `localStorage.getItem('datalab_active_project')`. If the user once had the demo or churn project, it persists indefinitely across page reloads.

4. **Component Fallbacks in Frontend Pages:**
   - `ResultsWorkspace.tsx`: `const projectName = project?.name || 'Customer Churn Predictor'` and hardcoded header string `Project: Customer Churn Predictor Run #004 ● Done`.
   - `ReportsCenter.tsx`: Hardcoded default report title `"Customer Churn AutoML Executive Technical Summary"` and hardcoded paragraph about 7,043 telecom subscribers.
   - `MonitoringDashboard.tsx`, `AlertCenter.tsx`, `NotebooksViewer.tsx`, `PipelineVisualizer.tsx`, `ExperimentsLab.tsx`, `DeploymentManager.tsx`, `AIAssistant.tsx`: All contain `{activeProject?.name || 'Customer Churn Prevention'}`.
   - `ProjectsList.tsx`: Initializes `useState<Project[]>(DEMO_PROJECTS)` and does not fetch from `/api/projects` on load.

---

## 12. Duplicate Logic

1. Project creation logic is duplicated across `ProjectsList.tsx`, `NewProject.tsx`, and `backend/app/api/endpoints/projects.py`.
2. Storage path generation exists in both `backend/app/tools/storage.py` and `backend/app/storage/service.py` with conflicting path schemas.
3. Dataset profiling code is duplicated between `agents/eda.py` and `app/tools/profiler.py`.

---

## 13. Security Issues

1. **IDOR / Authorization Bypass:** Projects and artifacts are queried without verifying that `project.user_id == current_user.id`.
2. **Path Traversal Risk:** Direct file uploads in some endpoints use `file.filename` directly in local filesystem paths without sanitization.
3. **Hardcoded Fallbacks Exposing Confusing State:** Unauthenticated users receive full mock responses with customer churn data instead of a clean 401 Unauthorized redirect.

---

## 14. Data Isolation Problems

1. All artifacts and dataset files in local storage are stored in global `./datasets/` and `./artifacts/` directories rather than `users/{user_id}/projects/{project_id}/`.
2. Database queries in reports, notebooks, and models list the latest records across the entire table if `project_id` is omitted in the query.
3. React components share a single `currentProject` in `authStore` without clearing state on route changes.

---

## 15. Naming Problems

1. Project names are inferred prematurely before file profiling finishes.
2. No slug generation (`project_slug`) exists, making project identification reliant on mutable display names or raw UUIDs.
3. Fallback names like `"Customer Churn Intelligence"` and `"Customer Churn Prevention"` are scattered across 15+ frontend files.

---

## 16. UI Problems

1. `NewProject.tsx` does not display an interactive AI Planning Proposal with Human-in-the-Loop approval before launching the AutoML pipeline.
2. No global Project Switcher in the TopBar that reflects actual database projects with status, dataset, last run, model, and last updated metadata.
3. Switching projects does not clear active run, report, and artifact state in the UI.

---

## 17. Performance Problems

1. Projects list endpoint attempts to load full dataset rows and preview configurations in memory for all projects.
2. In-memory dictionary `_RUN_STATES` grows unbounded without eviction policies.
3. Frontend does not use query keys or memoization keyed by `projectId`.

---

## 18. Missing Tests

1. No automated test verifying project data isolation (User A/Project A cannot access User B/Project B).
2. No regression test ensuring a newly created project with an arbitrary dataset does not display "Customer Churn Prediction".
3. No storage namespace isolation test verifying files exist under `users/{user_id}/projects/{project_id}/`.
4. No unit/integration test for AI Project Planner with human approval flow.

---

## 19. Recommended Improvements & Execution Roadmap

1. **Database Schema Enhancements:**
   - Add `slug`, `objective`, `visibility`, `current_dataset_id`, `current_run_id`, `latest_model_id`, `latest_model_version`, `metadata` to `Project`.
   - Add `ProjectPrompt` entity supporting versioning (`prompt_id`, `project_id`, `version`, `content`, `created_by`, `created_at`, `is_active`).
   - Add SHA-256 duplicate checking and versioning to `DatasetEntity`.
   - Update `ArtifactEntity` and `TrainingRun` with strict `user_id` and `project_id` foreign keys.

2. **Storage Namespace Refactoring:**
   - Enforce `users/{user_id}/projects/{project_id}/{category}/...` across all uploads and generated artifacts.

3. **Backend Agent & API Enhancements:**
   - Implement `project_planner_agent` in LangGraph to generate dynamic project proposals from dataset profiles.
   - Implement human approval endpoint for approving, editing, or regenerating proposals.
   - Implement `system_improvement_agent` and `system_testing_agent`.
   - Enforce strict server-side authorization in all project, dataset, run, and artifact endpoints.

4. **Frontend Architecture Refactoring:**
   - Remove all hardcoded "Customer Churn Prediction" strings and fallbacks across the entire application.
   - Fix the state race condition in `NewProject.tsx` and integrate the AI Project Proposal modal.
   - Build a global dynamic Project Switcher with active project metadata.
   - Update routing and all project workspace pages to strictly derive project identity from URL parameters (`useParams().projectId`), clearing state on project switch.

5. **Comprehensive Testing & Validation:**
   - Run end-to-end multi-project tests with diverse datasets (classification, regression, fraud, housing).
   - Generate `SYSTEM_TEST_REPORT.md` documenting verified pass/fail results.
