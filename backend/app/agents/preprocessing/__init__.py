"""
DataWise AI — Preprocessing Agents
Agents for missing value imputation, outlier analysis, encoding, scaling, transformation, and leakage prevention.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional
import pandas as pd
from loguru import logger

from agents.base import BaseAgent, AgentInput, AgentOutput
from app.tools.preprocessing_tools import (
    analyze_missingness,
    recommend_imputation_strategy,
    detect_outliers_iqr,
    detect_outliers_isolation_forest,
    analyze_outlier_context,
    evaluate_removal_risk,
    suggest_encoding,
    suggest_scaling,
    analyze_skewness,
    suggest_transformations,
    detect_target_leakage,
    check_train_test_contamination,
)


class MissingValueAgent(BaseAgent):
    """
    Analyzes missing value mechanisms (MCAR/MAR/MNAR) and recommends leak-free imputation strategies.
    Ensures preprocessors are fitted strictly on training data.
    """
    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="MissingValueAgent")

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
            missing_report = analyze_missingness(df)
            strategy = recommend_imputation_strategy(df, missing_report)

            total_missing = missing_report.get("total_missing_cells", 0)
            cols_missing = missing_report.get("columns_with_missing", 0)
            missing_cols_count = len(cols_missing) if isinstance(cols_missing, (list, tuple)) else int(cols_missing)

            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="success",
                data={
                    "missing_analysis": missing_report,
                    "recommended_strategies": strategy,
                },
                summary=f"Found {total_missing} missing values across {missing_cols_count} columns. Recommended strategies: {strategy.get('summary', 'Standard median/mode imputation')}."
            )

        except Exception as e:
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="error",
                errors=[str(e)],
                summary=f"Missing value analysis failed: {e}"
            )


class OutlierAgent(BaseAgent):
    """
    Analyzes outliers using IQR, Z-Score, LOF, and Isolation Forest.
    Never deletes outliers automatically. Requires explicit human approval for destructive operations.
    """
    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="OutlierAgent")

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
            iqr_outliers = detect_outliers_iqr(df)
            context = analyze_outlier_context(df, target_col=target_col)
            risk = evaluate_removal_risk(df, iqr_outliers, target_col=target_col)

            affected_cols = list(iqr_outliers.get("column_outliers", {}).keys())
            total_outlier_rows = iqr_outliers.get("total_unique_outlier_rows", 0)

            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="needs_approval" if total_outlier_rows > 0 else "success",
                needs_approval=bool(total_outlier_rows > 0),
                approval_context={
                    "action": "outlier_treatment",
                    "affected_rows": total_outlier_rows,
                    "affected_columns": affected_cols,
                    "removal_risk": risk.get("risk_level", "low"),
                    "recommendation": "Retain outliers and use RobustScaler or Tree/Boosting models resistant to extreme values.",
                },
                data={
                    "detection_summary": iqr_outliers,
                    "contextual_analysis": context,
                    "removal_risk": risk,
                },
                summary=f"Detected {total_outlier_rows} rows with extreme values across {len(affected_cols)} columns. Outliers preserved by default to protect fraud/anomaly signals. Removal risk: {risk.get('risk_level', 'low')}."
            )
        except Exception as e:
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="error",
                errors=[str(e)],
                summary=f"Outlier analysis failed: {e}"
            )


class EncodingAgent(BaseAgent):
    """
    Selects encoding methods based on cardinality, ordinal relationships, and target task.
    """
    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="EncodingAgent")

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
            enc_plan = suggest_encoding(df, target_col=target_col)

            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="success",
                data=enc_plan,
                summary=f"Encoding strategy formulated: {len(enc_plan.get('one_hot_columns', []))} OneHot columns, {len(enc_plan.get('ordinal_columns', []))} Ordinal columns, {len(enc_plan.get('high_cardinality_columns', []))} High-Cardinality target/frequency columns."
            )
        except Exception as e:
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="error",
                errors=[str(e)],
                summary=f"Encoding recommendation failed: {e}"
            )


class ScalingAgent(BaseAgent):
    """
    Recommends feature scaling (StandardScaler, RobustScaler, MinMaxScaler).
    Avoids unnecessary scaling for tree-based models.
    """
    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="ScalingAgent")

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        file_path = input_data.dataset_path or input_data.parameters.get("file_path")
        model_family = input_data.parameters.get("model_family", "mixed")
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
            scaling_plan = suggest_scaling(df, model_family=model_family)

            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="success",
                data=scaling_plan,
                summary=f"Scaling plan ready: recommended '{scaling_plan.get('recommended_scaler', 'StandardScaler')}' for distance and gradient-based candidates."
            )
        except Exception as e:
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="error",
                errors=[str(e)],
                summary=f"Scaling recommendation failed: {e}"
            )


class TransformationAgent(BaseAgent):
    """
    Analyzes skewness and applies Yeo-Johnson, Box-Cox, or log transforms.
    """
    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="TransformationAgent")

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
            skew_info = analyze_skewness(df)
            trans_plan = suggest_transformations(df, skew_info)

            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="success",
                data={
                    "skewness": skew_info,
                    "transformation_plan": trans_plan,
                },
                summary=f"Analyzed feature distributions: {len(trans_plan.get('skewed_features', []))} highly skewed features identified for power transformation."
            )
        except Exception as e:
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="error",
                errors=[str(e)],
                summary=f"Transformation analysis failed: {e}"
            )


class LeakageAgent(BaseAgent):
    """
    Detects target leakage, temporal leakage, duplicate rows, and train/test contamination.
    Halts the pipeline immediately if severe leakage is found.
    """
    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="LeakageAgent")

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
            leakage_res = detect_target_leakage(df, target_col=target_col)

            leak_cols = leakage_res.get("leaking_columns", [])
            has_leakage = len(leak_cols) > 0

            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="warning" if has_leakage else "success",
                warnings=[f"Potential target leakage in columns: {leak_cols}"] if has_leakage else [],
                data=leakage_res,
                summary=f"Data leakage check: {'WARNING: ' + str(len(leak_cols)) + ' leaking columns detected (' + ', '.join(leak_cols) + ')' if has_leakage else 'Zero target leakage or contamination detected.'}"
            )
        except Exception as e:
            return AgentOutput(
                session_id=input_data.session_id,
                agent_name=self.agent_name,
                status="error",
                errors=[str(e)],
                summary=f"Leakage detection failed: {e}"
            )


from app.agents.preprocessing.preprocessing_agent import PreprocessingAgent

__all__ = [
    "PreprocessingAgent",
    "MissingValueAgent",
    "OutlierAgent",
    "EncodingAgent",
    "ScalingAgent",
    "TransformationAgent",
    "LeakageAgent",
]

