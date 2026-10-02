"""
DataWise AI — LLM Schemas and Task Typing
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TaskType(str, Enum):
    SUPERVISOR = "supervisor"
    COMPLEX_REASONING = "complex_reasoning"
    DATASET_INTERPRETATION = "dataset_interpretation"
    MODEL_SELECTION_REASONING = "model_selection_reasoning"
    REPORT_GENERATION = "report_generation"
    FAST_SIMPLE = "fast_simple"
    CODE_GENERATION = "code_generation"


class ProviderType(str, Enum):
    GEMINI = "gemini"
    OLLAMA = "ollama"
    OPENAI = "openai"


class ModelDescriptor(BaseModel):
    model_name: str
    provider: ProviderType
    context_window: int = 8192
    supports_system_prompt: bool = True
    supports_json_schema: bool = True
    is_local: bool = False
    description: str = ""


class LLMGenerationRequest(BaseModel):
    prompt: str
    system_instruction: Optional[str] = None
    task_type: TaskType = TaskType.FAST_SIMPLE
    temperature: float = 0.2
    max_tokens: int = 1500
    stop_sequences: Optional[List[str]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class StructuredRecommendation(BaseModel):
    title: str
    rationale: str
    risk_level: str = "low"  # low, medium, high
    confidence: float = 0.85
    recommended_action: str
    requires_user_approval: bool = False
    details: Dict[str, Any] = Field(default_factory=dict)
