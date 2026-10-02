"""
DataWise AI — Application Settings

All configuration is driven by environment variables (via .env file).
Uses Pydantic BaseSettings for validation and type coercion.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Literal, List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Search and load local .env files into os.environ
for env_path in [".env", "backend/.env", "../.env", Path(__file__).resolve().parents[2] / ".env", Path(__file__).resolve().parents[1] / ".env"]:
    if os.path.exists(env_path):
        load_dotenv(env_path, override=False)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ------------------------------------------------------------------ #
    #  Application
    # ------------------------------------------------------------------ #
    app_env: Literal["development", "production", "testing"] = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    secret_key: str = Field(default="changeme-replace-in-production-with-long-random-string")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # CORS origins — covers both localhost and 127.0.0.1 (browsers treat them differently)
    cors_origins: str = (
        "http://localhost:5173,http://127.0.0.1:5173,"
        "http://localhost:3000,http://127.0.0.1:3000,"
        "http://localhost:8080,http://127.0.0.1:8080,"
        "http://localhost:4173,http://127.0.0.1:4173"
    )

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    # ------------------------------------------------------------------ #
    #  LLM Provider (Primary: Gemini, Fallback 1: Groq, Fallback 2: Cloudflare)
    # ------------------------------------------------------------------ #
    llm_provider: Literal["gemini", "groq", "cloudflare", "ollama", "openai"] = "gemini"

    # Gemini (Primary)
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    gemini_primary_model: str = "gemini-2.0-flash"

    # Groq (First Fallback)
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"

    # Cloudflare Workers AI (Second Fallback)
    cloudflare_account_id: str = ""
    cloudflare_api_token: str = ""
    cloudflare_model: str = "@cf/meta/llama-3.1-8b-instruct"
    claudeflare_ai_worker_api_key: str = ""

    @field_validator("cloudflare_api_token", mode="before")
    @classmethod
    def resolve_cloudflare_token(cls, v: str) -> str:
        if v:
            return v
        return (
            os.getenv("CLAUDEFLARE_AI_WORKER_API_KEY", "")
            or os.getenv("CLOUDFLARE_WORKERS_AI_API_KEY", "")
            or ""
        )

    # Ollama (Local Fallback & Simple/Coding tasks)
    ollama_base_url: str = "http://localhost:11434"
    ollama_primary_model: str = "qwen2.5:7b"
    ollama_coding_model: str = "qwen2.5-coder:7b"

    # OpenAI-compatible
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o"

    # Generation & Caching
    llm_temperature: float = 0.1
    llm_max_tokens: int = 4096
    llm_cache_enabled: bool = True

    # ------------------------------------------------------------------ #
    #  Autonomous Optimization Loop & Compute Safety Bounds
    # ------------------------------------------------------------------ #
    max_experiments: int = 50
    max_no_improvement: int = 8
    max_training_time: int = 1800
    max_concurrent_training: int = 4
    max_concurrent_training_per_user: int = 2
    max_concurrent_training_global: int = 4

    # ------------------------------------------------------------------ #
    #  Database
    # ------------------------------------------------------------------ #
    database_url: str = "sqlite+aiosqlite:///./datawise.db"
    database_pool_size: int = 10
    database_max_overflow: int = 20
    database_pool_timeout: int = 30
    database_pool_recycle: int = 1800
    database_statement_timeout: int = 60000  # ms

    # ------------------------------------------------------------------ #
    #  Redis
    # ------------------------------------------------------------------ #
    redis_url: str = "redis://localhost:6379/0"
    redis_password: str = ""

    # ------------------------------------------------------------------ #
    #  S3 / MinIO Object Storage
    # ------------------------------------------------------------------ #
    s3_endpoint: str = "http://localhost:9000"
    s3_bucket: str = "datawise"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_region: str = "us-east-1"
    s3_use_ssl: bool = False
    model_storage_bucket: str = "datawise-models"
    artifact_storage_bucket: str = "datawise-artifacts"

    # ------------------------------------------------------------------ #
    #  Rate Limiting
    # ------------------------------------------------------------------ #
    rate_limit_enabled: bool = True
    rate_limit_default: int = 120  # requests / min
    rate_limit_auth: int = 10     # requests / min / IP
    rate_limit_upload: int = 20   # uploads / hour / user
    rate_limit_training: int = 10 # training runs / hour / user
    rate_limit_prediction: int = 300 # predictions / min

    # ------------------------------------------------------------------ #
    #  Observability
    # ------------------------------------------------------------------ #
    sentry_dsn: str = ""
    otel_endpoint: str = ""

    # ------------------------------------------------------------------ #
    #  File Storage (Local Fallback & Staging)
    # ------------------------------------------------------------------ #
    storage_path: str = "./datasets"
    artifacts_path: str = "./artifacts"
    reports_path: str = "./artifacts/reports"
    plots_path: str = "./artifacts/plots"
    code_path: str = "./artifacts/code"

    @property
    def upload_dir_path(self) -> Path:
        for candidate in [
            Path(__file__).resolve().parents[3] / "datasets",
            Path(__file__).resolve().parents[2] / "datasets",
            Path("datasets"),
            Path("../datasets"),
        ]:
            if candidate.exists() and candidate.is_dir():
                return candidate.resolve()
        return Path(self.storage_path)

    @property
    def artifacts_dir_path(self) -> Path:
        return Path(self.artifacts_path)

    # ------------------------------------------------------------------ #
    #  Upload Validation
    # ------------------------------------------------------------------ #
    max_upload_size_mb: int = 100
    allowed_extensions: str = "csv,xlsx,xls,json,parquet"

    @property
    def allowed_extensions_set(self) -> set[str]:
        return {e.strip().lower() for e in self.allowed_extensions.split(",")}

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    # ------------------------------------------------------------------ #
    #  Helpers
    # ------------------------------------------------------------------ #
    def ensure_directories(self) -> None:
        """Create all required directories if they don't exist."""
        paths = [
            self.storage_path,
            self.artifacts_path,
            self.reports_path,
            self.plots_path,
            self.code_path,
        ]
        for path in paths:
            os.makedirs(path, exist_ok=True)

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings singleton."""
    settings = Settings()
    settings.ensure_directories()
    return settings

