# DataWise AI 🧠📊

> **Autonomous Data Science & ML Preparation Agent**
>
> Upload a dataset. Chat with an AI Data Scientist. Get a production-ready ML pipeline.

---

## What it Does

DataWise AI is a ChatGPT-like agent that autonomously:

- 🔍 **Profiles** your dataset (schema, statistics, column types)
- 🚨 **Detects** missing values, outliers, duplicates, and data quality issues
- 📊 **Visualizes** distributions, correlations, and outliers intelligently
- 🤔 **Recommends** preprocessing strategies (with explanations)
- ✅ **Asks you** before any destructive operation (human-in-the-loop)
- ⚙️ **Builds** a reusable `sklearn` `Pipeline` / `ColumnTransformer`
- 🤖 **Recommends** ML algorithms with rationale
- 📋 **Generates** reproducible Python code and complete ML project roadmap
- 📥 **Exports** reports (HTML, PDF, Markdown), plots (PNG/SVG/HTML), and code

---

## Architecture

```
User ↔ React Frontend
       ↕ REST + WebSocket
     FastAPI Backend
       ↕ LangGraph Agent Workflow
     Deterministic Python Tools (Pandas, Sklearn, Plotly)
       ↕ Results + Summaries
     LLM (Gemini / OpenAI) — interprets, explains, recommends
       ↕ Human Approval
     Next Analysis Stage
```

---

## Quick Start (Local Development)

### Prerequisites

- Python 3.11+
- Node.js 20+
- Git

### 1. Clone and set up environment

```bash
git clone <repo-url>
cd datawise-ai

# Copy environment template
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY or OPENAI_API_KEY
```

### 2. Backend setup

```bash
cd backend

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Generate test datasets
python ../data/test_datasets/generate_test_datasets.py

# Run the server
python main.py
# → API available at http://localhost:8000
# → Docs available at http://localhost:8000/api/docs
```

### 3. Frontend setup

```bash
cd frontend
npm install
npm run dev
# → UI available at http://localhost:5173
```

### 4. Run Tests

```bash
cd backend
pytest tests/ -v
```

---

## Docker (Production)

```bash
# Copy and configure env
cp .env.example .env
# Set GEMINI_API_KEY, SECRET_KEY, etc.

# Build and start all services
docker-compose up --build -d

# Services:
# - Frontend:  http://localhost:80
# - Backend:   http://localhost:8000
# - API Docs:  http://localhost:8000/api/docs
```

---

## Environment Variables

See [`.env.example`](.env.example) for all available configuration options.

| Variable | Required | Description |
|---|---|---|
| `LLM_PROVIDER` | Yes | `gemini` or `openai` |
| `GEMINI_API_KEY` | If Gemini | Google AI API key |
| `OPENAI_API_KEY` | If OpenAI | OpenAI API key |
| `DATABASE_URL` | Yes | SQLite (dev) or PostgreSQL (prod) |
| `SECRET_KEY` | Yes | JWT signing secret |
| `MAX_UPLOAD_SIZE_MB` | No | Default: 100 |

---

## Project Structure

```
datawise-ai/
├── backend/
│   ├── app/
│   │   ├── api/endpoints/     ← REST API routes
│   │   ├── agents/            ← LangGraph agent nodes
│   │   ├── graph/             ← LangGraph workflow + LLM provider
│   │   ├── tools/             ← Deterministic Python analysis tools
│   │   ├── state/             ← Shared LangGraph state TypedDict
│   │   ├── models/            ← SQLAlchemy ORM + database session
│   │   ├── security/          ← File validation, sandboxing, injection guard
│   │   ├── reports/           ← HTML/PDF/MD report generators
│   │   └── config/            ← Settings + logging
│   ├── tests/                 ← pytest test suite
│   └── requirements.txt
│
├── frontend/
│   └── src/
│       ├── components/        ← Chat, Sidebar, VisualizationCard, etc.
│       ├── pages/             ← Home, Analysis
│       ├── hooks/             ← useWebSocket, useApi
│       └── services/          ← API client
│
├── data/
│   ├── uploads/               ← User uploaded files (gitignored)
│   └── test_datasets/         ← Generated test CSVs
│
├── artifacts/                 ← Generated plots, reports, code (gitignored)
├── docker/                    ← Dockerfiles + nginx config
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Build Status

| Step | Status | Description |
|---|---|---|
| STEP 1 | ✅ Complete | Project structure, config, DB models, state, health API |
| STEP 2 | 🔜 Next | Dataset upload, validation, versioning |
| STEP 3 | ⬜ Planned | Dataset profiler |
| STEP 4 | ⬜ Planned | Missing value analyzer |
| STEP 5 | ⬜ Planned | Outlier analyzer |
| STEP 6 | ⬜ Planned | Visualization engine |
| STEP 7–23 | ⬜ Planned | See task.md |

---

## Contributing

This project uses an incremental build strategy. Each step is:
1. Implemented
2. Tested (`pytest`)
3. Verified manually
4. Then the next step begins

---

## License

MIT
