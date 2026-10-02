"""
DataWise AI — Central API Router

All endpoint routers are registered here.
Steps add routes incrementally as they are implemented.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.endpoints.health import router as health_router
from app.api.endpoints.sessions import router as sessions_router

from app.api.endpoints.datasets import router as datasets_router
from app.api.endpoints.analysis import router as analysis_router
from app.api.endpoints.decisions import router as decisions_router
from app.api.endpoints.ml_analysis import router as ml_analysis_router
from app.api.endpoints.chat import router as chat_router
from app.api.endpoints.reports import router as reports_router
from app.api.endpoints.registry import router as registry_router
from app.api.endpoints.inference import router as inference_router
from app.api.endpoints.realtime_platform import router as realtime_platform_router
from app.api.endpoints.projects import router as projects_router

api_router = APIRouter()

# Core routes (always available)
api_router.include_router(health_router, prefix="/health", tags=["System"])
api_router.include_router(realtime_platform_router, tags=["Realtime AutoML & MLOps Platform"])
api_router.include_router(projects_router, prefix="/projects", tags=["Projects & Agentic AutoML"])
api_router.include_router(sessions_router, prefix="/sessions", tags=["Sessions"])
api_router.include_router(datasets_router, prefix="/sessions", tags=["Datasets"])
api_router.include_router(analysis_router, prefix="/sessions", tags=["Analysis"])
api_router.include_router(decisions_router, prefix="/sessions", tags=["Decisions"])
api_router.include_router(ml_analysis_router, prefix="/sessions", tags=["ML Analysis"])
api_router.include_router(chat_router, prefix="/sessions", tags=["Chat & Workflow"])
api_router.include_router(reports_router, prefix="/sessions", tags=["Reports & Roadmaps"])
api_router.include_router(registry_router, prefix="/models", tags=["Model Registry"])
api_router.include_router(inference_router, prefix="/models", tags=["Model Inference"])
api_router.include_router(inference_router, prefix="/inference", tags=["Model Inference"])


