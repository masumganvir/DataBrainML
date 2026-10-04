"""
DataWise AI — Base Agent Architecture (Phase 2)
Provides standard contract, strongly-typed I/O, validation, and error recovery.
"""

from __future__ import annotations

from collections.abc import Mapping
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Union
import pandas as pd
from loguru import logger
from pydantic import BaseModel, Field


AgentStatus = Literal["pending", "running", "success", "warning", "error", "needs_approval"]


class AgentInput(BaseModel):
    session_id: str = Field(default="")
    run_id: Optional[str] = Field(default=None)
    dataset_path: Optional[str] = Field(default=None)
    dataset_id: Optional[str] = Field(default=None)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    state_ref: Optional[Dict[str, Any]] = Field(default=None)

    class Config:
        arbitrary_types_allowed = True


class AgentOutput(BaseModel):
    session_id: str = ""
    agent_name: str = ""
    status: AgentStatus = "success"
    success: Optional[bool] = None
    message: Optional[str] = None
    data: Dict[str, Any] = Field(default_factory=dict)
    summary: str = ""
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    execution_time_seconds: float = 0.0
    artifacts_generated: List[str] = Field(default_factory=list)
    needs_approval: bool = False
    approval_context: Optional[Dict[str, Any]] = None

    def model_post_init(self, __context: Any) -> None:
        if self.message and not self.summary:
            self.summary = self.message
        if self.success is not None:
            self.status = "success" if self.success else "error"
        elif self.status == "success":
            self.success = True
        else:
            self.success = False

    def __getitem__(self, item: str) -> Any:
        if hasattr(self, item):
            return getattr(self, item)
        if isinstance(self.data, dict) and item in self.data:
            return self.data[item]
        raise KeyError(item)

    def __setitem__(self, key: str, value: Any) -> None:
        if hasattr(self, key):
            setattr(self, key, value)
        else:
            if not isinstance(self.data, dict):
                self.data = {}
            self.data[key] = value

    def __contains__(self, item: Any) -> bool:
        return hasattr(self, str(item)) or (isinstance(self.data, dict) and str(item) in self.data)

    def __iter__(self):
        d = dict(self.__dict__)
        if isinstance(self.data, dict):
            d.update(self.data)
        return iter(d)

    def __len__(self) -> int:
        d = dict(self.__dict__)
        if isinstance(self.data, dict):
            d.update(self.data)
        return len(d)

    def get(self, key: str, default: Any = None) -> Any:
        if hasattr(self, key):
            val = getattr(self, key)
            return val if val is not None else default
        if isinstance(self.data, dict):
            return self.data.get(key, default)
        return default

    def keys(self):
        d = dict(self.__dict__)
        if isinstance(self.data, dict):
            d.update(self.data)
        return d.keys()

    def values(self):
        d = dict(self.__dict__)
        if isinstance(self.data, dict):
            d.update(self.data)
        return d.values()

    def items(self):
        d = dict(self.__dict__)
        if isinstance(self.data, dict):
            d.update(self.data)
        return d.items()

    class Config:
        arbitrary_types_allowed = True


Mapping.register(AgentOutput)


def load_dataframe_safely(path: Union[str, Path], max_rows: Optional[int] = None) -> Optional[pd.DataFrame]:
    """
    Safely loads a DataFrame from disk without loading large datasets into LLM context.
    Supports CSV, Excel, JSON, and Parquet.
    """
    if not path:
        return None
    p = Path(path)
    if not p.exists():
        logger.warning(f"Dataset path does not exist: {path}")
        return None

    ext = p.suffix.lower()
    try:
        if ext == ".csv":
            return pd.read_csv(p, nrows=max_rows, low_memory=False)
        elif ext in (".xlsx", ".xls"):
            return pd.read_excel(p, nrows=max_rows)
        elif ext == ".json":
            return pd.read_json(p)
        elif ext in (".parquet", ".pq"):
            return pd.read_parquet(p)
        else:
            return pd.read_csv(p, nrows=max_rows, low_memory=False)
    except Exception as exc:
        logger.error(f"Failed to load dataset at {path}: {exc}")
        return None


class BaseAgent(ABC):
    """Abstract Base Class for all Data Science Agents."""

    def __init__(self, session_id: str = "", agent_name: str = "BaseAgent", **kwargs: Any):
        self.name = kwargs.get("name", agent_name)
        self.role = kwargs.get("role", agent_name)
        self.description = kwargs.get("description", f"{agent_name} agent")
        self.system_prompt = kwargs.get("system_prompt", "")
        self.session_id = session_id
        self.agent_name = agent_name

    def _load_df(self, state: Any) -> Optional[pd.DataFrame]:
        """Utility to safely load the current working dataset from state paths."""
        if isinstance(state, dict):
            path = state.get("dataset_path_analysis") or state.get("dataset_path_original") or state.get("dataset_path")
        elif hasattr(state, "dataset_path"):
            path = getattr(state, "dataset_path")
        else:
            path = None
        if not path:
            return None
        return load_dataframe_safely(path)

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        """Core execution logic. Subclasses implement either analyze() or run()."""
        return AgentOutput(
            session_id=self.session_id,
            agent_name=self.agent_name,
            status="success",
            message=f"{self.agent_name} executed successfully.",
        )

    def validate(self, output: AgentOutput) -> AgentOutput:
        """Validate output schema, ensure timings and agent names match."""
        if not output.agent_name:
            output.agent_name = self.agent_name
        return output

    def run(self, input_data: Union[AgentInput, Dict[str, Any]]) -> Any:
        """Execution wrapper handling exceptions, structured timing, and logging."""
        t0 = time.time()
        if isinstance(input_data, dict) and ("completed_stages" in input_data or "dataset_path_original" in input_data or "dataset_path_analysis" in input_data):
            try:
                logger.info(f"[{self.agent_name}] Running state mutation for session={input_data.get('session_id')}")
                dataset_path = input_data.get("dataset_path_analysis") or input_data.get("dataset_path_original")
                params = {
                    "target_column": input_data.get("target_column"),
                    "task_type": input_data.get("task_type"),
                    "problem_type": input_data.get("task_type"),
                }
                inp = AgentInput(
                    session_id=str(input_data.get("session_id", "")),
                    dataset_path=dataset_path,
                    parameters=params,
                    state_ref=input_data,
                )
                output = self.analyze(inp)
                new_state = dict(input_data)
                if isinstance(output.data, dict):
                    for k, v in output.data.items():
                        new_state[k] = v
                return new_state
            except Exception as exc:
                logger.exception(f"[{self.agent_name}] Error during state execution: {exc}")
                new_state = dict(input_data)
                errs = list(new_state.get("errors", []))
                errs.append({"stage": self.agent_name, "error": str(exc)})
                new_state["errors"] = errs
                return new_state

        if isinstance(input_data, dict):
            input_obj = AgentInput(**input_data)
        else:
            input_obj = input_data

        try:
            logger.info(f"[{self.agent_name}] Started analysis for session={input_obj.session_id}")
            output = self.analyze(input_obj)
            output.execution_time_seconds = round(time.time() - t0, 4)
            return self.validate(output)
        except Exception as exc:
            elapsed = round(time.time() - t0, 4)
            logger.exception(f"[{self.agent_name}] Error during execution: {exc}")
            return AgentOutput(
                session_id=input_obj.session_id,
                agent_name=self.agent_name,
                status="error",
                summary=f"{self.agent_name} failed: {str(exc)}",
                errors=[str(exc)],
                execution_time_seconds=elapsed,
            )
