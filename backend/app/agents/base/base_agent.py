"""
DataWise AI — Base Agent
Defines the foundational abstract class for all specialized domain agents.
Each agent encapsulates domain expertise, deterministic tool orchestration,
and LLM-assisted reasoning.
"""

from __future__ import annotations

import abc
from typing import Any, Dict, List, Optional

import pandas as pd
from loguru import logger

from app.graph.llm_provider import LLMMessage, llm_provider
from app.state.data_science_state import DataScienceState


class BaseAgent(abc.ABC):
    """
    Abstract base class for all specialized data science agents.
    
    Attributes:
        name: Unique name of the agent (e.g. 'ProfilingAgent')
        role: Functional persona title (e.g. 'Data Profiler & Schema Specialist')
        description: Summary of what tasks this agent handles
        system_prompt: Specific persona instruction passed to the LLM
    """

    def __init__(
        self,
        name: str,
        role: str,
        description: str,
        system_prompt: str,
    ) -> None:
        self.name = name
        self.role = role
        self.description = description
        self.system_prompt = system_prompt

    def _load_df(self, state: DataScienceState) -> Optional[pd.DataFrame]:
        """Utility to safely load the current working dataset from state paths."""
        path = state.get("dataset_path_analysis") or state.get("dataset_path_original")
        if not path:
            return None
        try:
            ext = path.rsplit(".", 1)[-1].lower()
            if ext == "csv":
                return pd.read_csv(path, low_memory=False)
            elif ext in ("xlsx", "xls"):
                return pd.read_excel(path)
            elif ext == "json":
                return pd.read_json(path)
            return pd.read_csv(path, low_memory=False)
        except Exception as exc:  # noqa: BLE001
            logger.error(f"[{self.name}] Failed to load dataset at {path}: {exc}")
            return None

    @abc.abstractmethod
    def run(self, state: DataScienceState) -> DataScienceState:
        """
        Executes the agent's deterministic analysis and state mutation.
        Must be implemented by each specialized agent.
        """
        raise NotImplementedError

    async def respond(
        self,
        query: str,
        state: Optional[DataScienceState] = None,
        history: Optional[List[LLMMessage]] = None,
    ) -> str:
        """
        Generates an intelligent conversational response to a user query
        leveraging this agent's domain persona and the current dataset state.
        """
        context_str = self._format_state_context(state) if state else "No active dataset loaded."
        
        system = (
            f"You are the {self.name} ({self.role}) in the DataWise AI multi-agent system.\n"
            f"Specialty: {self.description}\n\n"
            f"{self.system_prompt}\n\n"
            f"Always answer directly from your domain perspective. "
            f"Use concise, structured markdown with bullet points and code where appropriate."
        )

        messages: List[LLMMessage] = []
        if history:
            messages.extend(history[-6:])  # Include recent conversation context
        
        prompt_content = f"[Current Dataset Context]\n{context_str}\n\nUser Question: {query}"
        messages.append(LLMMessage(role="user", content=prompt_content))

        try:
            return await llm_provider.complete(
                messages=messages,
                system_prompt=system,
                temperature=0.3,
                max_tokens=1500,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"[{self.name}] LLM response failed: {exc}")
            return f"[{self.name}] Analysis update: {self.description}. (Error generating text response: {exc})"

    def _format_state_context(self, state: DataScienceState) -> str:
        """Default summary context extractor from state; can be overridden."""
        lines = [
            f"Session ID: {state.get('session_id', 'N/A')}",
            f"Current Stage: {state.get('current_stage', 'N/A')}",
            f"Target Column: {state.get('target_column') or 'None detected'}",
            f"Task Type: {state.get('task_type') or 'Undetermined'}",
            f"Rows: {state.get('row_count_original', 'N/A')} | Columns: {state.get('column_count_original', 'N/A')}",
        ]
        return "\n".join(lines)
