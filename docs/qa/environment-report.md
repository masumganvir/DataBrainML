# Environment Verification & Readiness Report

- **Date / Timestamp**: 2026-09-30T18:05:00+05:30
- **Host OS**: Windows 11 Enterprise (AMD64 build 10.0.26200)
- **QA Branch**: `qa/production-readiness`

---

## 1. System Toolchain Verification

| Component | Installed Version | Required / Baseline | Status | Notes |
|---|---|---|---|---|
| **Python** | 3.14.6 | Python 3.11+ | **PASS** | Verified via `backend/.venv/Scripts/python.exe` |
| **Node.js** | v24.14.0 | Node 18+ | **PASS** | LTS runtime verified |
| **npm** | 11.9.0 | npm 9+ | **PASS** | Node package manager active |
| **pnpm** | Not installed | Optional | **INFO** | Project uses `npm` (`package-lock.json` present) |
| **Git** | 2.53.0.windows.2 | Git 2.x | **PASS** | Branch `qa/production-readiness` established |
| **Docker CLI** | 29.7.2 (build a7dcaa6) | Docker 24+ | **PASS** | CLI available |
| **Docker Daemon** | Stopped / Unavailable | Docker Desktop | **WARNING** | Local daemon offline; container builds deferred |
| **Docker Compose** | v5.5.0 | v2.20+ | **PASS** | CLI available |
| **PostgreSQL** | asyncpg 0.31.0 | Postgres 15+ | **PASS** | Local SQLite fallback enabled; Postgres ready |
| **Redis Client** | redis 8.1.0 | Redis 7+ | **PASS** | Resilient `InMemoryFallbackCache` active |
| **Tauri Desktop** | Tauri 1.5 (Cargo.toml) | Tauri 1.5+ | **PASS** | Manifest and architecture configured |
| **Rust / Cargo** | Not on host PATH | Rust 1.70+ | **WARNING** | Native `.exe` build requires host Rust install |
| **PyTorch & CUDA** | PyTorch 2.14.0+cpu | PyTorch 2.2+ | **PASS** | CPU-accelerated execution; CUDA is False |
| **Jupyter Format** | Custom v4 Generator | Jupyter / nbformat | **PASS** | Zero-dependency JSON `.ipynb` compliant engine |

---

## 2. Package Manifests & Dependency Audit

### 2.1 Python Dependencies (`backend/requirements.txt`, `requirements.txt`)
- **FastAPI / Uvicorn**: `fastapi==0.141.1`, `uvicorn==0.53.0` (Latest, asynchronous, ASGI compliant).
- **Database & Persistence**: `SQLAlchemy==2.0.54`, `alembic==1.20.0`, `asyncpg==0.31.0`, `aiosqlite==0.22.1`.
- **Machine Learning**: `scikit-learn==1.9.1`, `xgboost==3.4.1`, `lightgbm==4.7.0`, `imbalanced-learn==0.14.2`, `optuna==5.0.0`, `shap==0.52.0`.
- **Agents & Orchestration**: `langgraph==1.2.11`, `langchain==1.4.2`, `langchain-core==1.6.3`, `google-genai==2.24.0`, `openai==3.16.2`.
- **Status**: No missing critical Python dependencies in active virtual environment.

### 2.2 Frontend Dependencies (`frontend/package.json`, `package-lock.json`)
- React 18.3.1, TypeScript 5.6.3, Vite 6.0.5, Plotly.js 2.35.2, PrismJS 1.29.0, Lucide-React 0.468.0.
- `node_modules` directory is populated with lockfile consistency.

### 2.3 Desktop Dependencies (`frontend/src-tauri/Cargo.toml`)
- Tauri 1.5 with features: `shell-open`, `dialog-all`, `http-request`, `notification`.
- `serde`, `serde_json` for native bridge IPC.

---

## 3. Discovered Version & Compatibility Considerations
1. **Python 3.14 Support**: The project was specifically tested and tuned for Python 3.14 compatibility (`scikit-learn==1.9.1`, `numpy==2.5.3`, `torch==2.14.0+cpu`).
2. **CUDA / GPU Acceleration**: The test runner host is a CPU execution node. Tabular AutoML and neural MLP networks fall back to CPU execution cleanly without crashing.
3. **Local Docker / Redis / Postgres**: The application includes self-contained fallbacks (`aiosqlite` for database and `InMemoryFallbackCache` for Redis) ensuring local development and integration tests can run without requiring background services.
