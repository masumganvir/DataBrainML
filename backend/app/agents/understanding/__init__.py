"""
DataWise AI — Understanding Agents
Agents for profiling, schema extraction, problem classification, modality detection, and quality assessment.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional
import pandas as pd
from loguru import logger

from agents.base import BaseAgent, AgentInput, AgentOutput
from app.tools.data_tools import profile_dataset, detect_missing_values, detect_duplicates, run_quality_checks
from app.tools.target_detector import detect_target_column, classify_problem_type


class DatasetProfilerAgent(BaseAgent):
    """
    Computes deterministic statistical profiles across all columns:
    cardinality, missingness, memory usage, distributions, duplicates, constants.
    """
    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="DatasetProfilerAgent")

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        file_path = input_data.dataset_path or input_data.parameters.get("file_path")
        if not file_path or not os.path.exists(file_path):
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="error",
                errors=["Dataset path not provided or does not exist."],
                summary="Dataset file missing."
            )

        try:
            profile = profile_dataset(file_path)
            profile_dict = profile.model_dump() if hasattr(profile, "model_dump") else dict(profile)
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="success",
                data=profile_dict,
                summary=f"Profiled dataset: {profile_dict.get('total_rows', 0)} rows, {profile_dict.get('total_columns', 0)} columns across {len(profile_dict.get('column_types', {}))} data types."
            )
        except Exception as e:
            logger.error(f"Dataset profiling failed: {e}")
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="error",
                errors=[str(e)],
                summary=f"Profiling failed: {e}"
            )


class SchemaAgent(BaseAgent):
    """
    Discovers dataset schema, primary keys, ID columns, temporal sequences, and semantic column roles.
    """
    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="SchemaAgent")

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        file_path = input_data.dataset_path or input_data.parameters.get("file_path")
        if not file_path or not os.path.exists(file_path):
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="error",
                errors=["Dataset file missing."],
                summary="Dataset file missing."
            )

        try:
            from app.tools.data_tools import load_dataset_file
            df = load_dataset_file(file_path)

            id_candidates = []
            temporal_candidates = []
            categorical_cols = []
            numerical_cols = []

            for col in df.columns:
                n_unique = df[col].nunique()
                total = len(df)
                dtype_str = str(df[col].dtype).lower()

                if "date" in dtype_str or "time" in dtype_str:
                    temporal_candidates.append(col)
                elif pd.api.types.is_numeric_dtype(df[col]):
                    if n_unique == total and total > 50:
                        id_candidates.append(col)
                    else:
                        numerical_cols.append(col)
                else:
                    categorical_cols.append(col)

            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="success",
                data={
                    "total_features": len(df.columns),
                    "numerical_features": numerical_cols,
                    "categorical_features": categorical_cols,
                    "temporal_features": temporal_candidates,
                    "id_candidates": id_candidates,
                },
                summary=f"Schema discovery complete: {len(numerical_cols)} numerical, {len(categorical_cols)} categorical, {len(temporal_candidates)} temporal, {len(id_candidates)} ID candidates."
            )
        except Exception as e:
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="error",
                errors=[str(e)],
                summary=f"Schema discovery failed: {e}"
            )


class ProblemTypeAgent(BaseAgent):
    """
    Infers machine learning problem formulation (binary classification, multiclass, regression, time series forecasting, clustering).
    """
    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="ProblemTypeAgent")

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        file_path = input_data.dataset_path or input_data.parameters.get("file_path")
        target_col = input_data.parameters.get("target_column")

        if not file_path or not os.path.exists(file_path):
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="error",
                errors=["Dataset file missing."],
                summary="Dataset file missing."
            )

        try:
            from app.tools.data_tools import load_dataset_file
            df = load_dataset_file(file_path)

            if not target_col:
                target_result = detect_target_column(df)
                target_col = target_result.get("target_column") or target_result.get("recommended_target")
                confidence = target_result.get("confidence", 0.85)
            else:
                confidence = 1.0

            if target_col and target_col in df.columns:
                pt_result = classify_problem_type(df, target_col)
                problem_type = pt_result.get("problem_type") or pt_result.get("task_type", "classification")
                rationale = pt_result.get("rationale") or pt_result.get("imbalance_recommendation", "")
            else:
                problem_type = "unsupervised_clustering"
                rationale = "No target column specified or detected; routing to unsupervised representation learning."


            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="success",
                data={
                    "target_column": target_col,
                    "problem_type": problem_type,
                    "confidence": confidence,
                    "rationale": rationale,
                },
                summary=f"Identified problem formulation: {problem_type.upper()} with target '{target_col}'. {rationale}"
            )
        except Exception as e:
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="error",
                errors=[str(e)],
                summary=f"Problem type identification failed: {e}"
            )


class ModalityAgent(BaseAgent):
    """
    Routes dataset to proper modality pipeline: TABULAR, TEXT, IMAGE, TIME_SERIES, MULTIMODAL.
    """
    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="ModalityAgent")

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        file_path = input_data.dataset_path or input_data.parameters.get("file_path")
        if not file_path or not os.path.exists(file_path):
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="error",
                errors=["Dataset file missing."],
                summary="Dataset file missing."
            )

        try:
            from app.tools.data_tools import load_dataset_file
            df = load_dataset_file(file_path)

            # Analyze text length and columns
            text_cols = []
            for col in df.select_dtypes(include=["object", "string"]).columns:
                avg_len = df[col].astype(str).str.len().mean()
                if avg_len > 100:
                    text_cols.append(col)

            has_time = any("date" in str(col).lower() or "time" in str(col).lower() for col in df.columns)

            if len(text_cols) > 0 and len(df.columns) <= 5:
                modality = "TEXT"
                pipeline_route = "NLP + Transformer Pipeline"
            elif has_time and len(df) > 100:
                modality = "TIME_SERIES"
                pipeline_route = "Temporal + Statistical Forecasting / LSTM Pipeline"
            else:
                modality = "TABULAR"
                pipeline_route = "Classical ML + Tabular Neural Network Pipeline"

            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="success",
                data={
                    "data_modality": modality,
                    "recommended_pipeline": pipeline_route,
                    "text_columns": text_cols,
                    "temporal_columns": [c for c in df.columns if "date" in str(c).lower() or "time" in str(c).lower()],
                },
                summary=f"Dataset classified as modality '{modality}'. Routing to {pipeline_route}."
            )
        except Exception as e:
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="error",
                errors=[str(e)],
                summary=f"Modality detection failed: {e}"
            )


class DataQualityAgent(BaseAgent):
    """
    Computes global data quality score, missing rates, duplicate rates, constant columns, and cardinality anomalies.
    """
    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="DataQualityAgent")

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        file_path = input_data.dataset_path or input_data.parameters.get("file_path")
        if not file_path or not os.path.exists(file_path):
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="error",
                errors=["Dataset file missing."],
                summary="Dataset file missing."
            )

        try:
            from app.tools.data_tools import load_dataset_file
            df = load_dataset_file(file_path)
            quality_report = run_quality_checks(df)

            score = quality_report.get("overall_quality_score", 100.0)
            issues = quality_report.get("critical_issues", [])

            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="success",
                data=quality_report,
                summary=f"Data Quality Score: {score}/100 with {len(issues)} critical quality warnings detected."
            )
        except Exception as e:
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="error",
                errors=[str(e)],
                summary=f"Data quality analysis failed: {e}"
            )


__all__ = [
    "DatasetProfilerAgent",
    "SchemaAgent",
    "ProblemTypeAgent",
    "ModalityAgent",
    "DataQualityAgent",
]
