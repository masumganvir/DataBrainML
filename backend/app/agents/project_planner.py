"""
DataWise AI — AI Project Planner Agent
LangGraph-ready autonomous planning agent that evaluates dataset profiles,
user prompts, and business objectives to generate structured, human-approvable
project blueprints.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional
from loguru import logger

from app.graph.llm_provider import LLMMessage, llm_provider


class ProjectPlannerAgent:
    """Autonomous agent that designs ML project proposals from data & intent."""

    def __init__(self):
        self.llm = llm_provider

    def _generate_deterministic_proposal(
        self,
        dataset_info: Dict[str, Any],
        user_prompt: str = "",
        dataset_filename: str = "",
    ) -> Dict[str, Any]:
        """High-quality deterministic fallback when LLM is unavailable."""
        columns: List[str] = dataset_info.get("columns", []) or []
        row_count: int = dataset_info.get("row_count") or dataset_info.get("rows") or 0
        col_count: int = len(columns) or dataset_info.get("column_count") or dataset_info.get("cols") or 0
        target_candidate = dataset_info.get("target_candidate") or dataset_info.get("recommended_target")

        # Derive candidate target if missing
        if not target_candidate and columns:
            candidates = [
                c for c in columns
                if any(k in c.lower() for k in ["target", "label", "class", "churn", "fraud", "price", "sale", "outcome", "status", "score"])
            ]
            target_candidate = candidates[0] if candidates else columns[-1]

        # Derive task type
        task_type = "classification"
        target_lower = (target_candidate or "").lower()
        prompt_lower = (user_prompt or "").lower()
        regression_keywords = [
            "price", "cost", "salary", "amount", "score", "value", "rate", "count",
            "time", "revenue", "loss", "sale", "sales", "spend", "gdp", "profit",
            "temperature", "demand", "volume", "quantity", "forecast", "forecasting"
        ]
        if any(k in target_lower for k in regression_keywords) or any(k in prompt_lower for k in ["forecast", "regression", "continuous", "sales"]):
            task_type = "regression"

        # Derive clean display name from filename or target
        base_name = ""
        if dataset_filename:
            clean = re.sub(r"\.[^.]+$", "", dataset_filename)
            clean = re.sub(r"[_\-]+", " ", clean).strip()
            base_name = " ".join(word.capitalize() for word in clean.split())
        elif target_candidate:
            base_name = f"{target_candidate.replace('_', ' ').title()} Intelligence"
        else:
            base_name = "Autonomous Machine Learning"

        project_name = f"{base_name} {task_type.capitalize()}" if not any(t in base_name.lower() for t in ["classification", "regression", "prediction"]) else base_name
        primary_metric = "F1" if task_type == "classification" else "R²"
        secondary_metrics = ["ROC-AUC", "Precision", "Recall"] if task_type == "classification" else ["RMSE", "MAE", "MAPE"]

        objective = user_prompt.strip() or f"Autonomously predict '{target_candidate or 'target'}' using a production-ready {task_type} pipeline."
        structured_prompt = (
            f"Build a production-ready {task_type} model using the uploaded dataset ({dataset_filename or 'tabular'}). "
            f"Analyze feature distributions, handle missing values and outliers without leaking target information, "
            f"benchmark candidate algorithms, optimize for {primary_metric}, validate overfitting with cross-validation holdouts, "
            f"and generate explainability artifacts and REST API inference packages."
        )

        return {
            "project_name": project_name,
            "project_description": f"End-to-end autonomous {task_type} pipeline targeting '{target_candidate}' across {row_count or 'unknown'} records.",
            "business_problem": f"Automate data-driven decision making and risk assessment for {base_name.lower()}.",
            "target": target_candidate or "target",
            "target_candidate": target_candidate or "target",
            "task": task_type,
            "task_type": task_type,
            "ml_task": task_type,
            "primary_metric": primary_metric,
            "secondary_metrics": secondary_metrics,
            "recommended_pipeline": [
                "Automated Schema Inference & Imputation",
                "Outlier Containment & Robust Scaling",
                "Information-Theoretic Feature Selection",
                "Ensemble Gradient Boosted Trees & Baseline Linear Models",
                "Stratified K-Fold Cross-Validation",
                "SHAP Tree Explainability & Dockerized FastAPI Packaging",
            ],
            "deployment_context": "Real-time REST API & Batch Scoring",
            "expected_output": "Serialized Joblib Model, Preprocessing Pipeline, Executable Jupyter Notebook, and PDF/HTML Technical Summary",
            "risks": [
                "Class imbalance or skewed target distributions may require focal weighting or resampling",
                "Potential collinearity between numeric regressors",
            ],
            "project_prompt": structured_prompt,
        }

    async def plan_project(
        self,
        dataset_info: Dict[str, Any],
        user_prompt: str = "",
        dataset_filename: str = "",
        custom_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate a project plan proposal based on dataset profile and user intent."""
        deterministic = self._generate_deterministic_proposal(dataset_info, user_prompt, dataset_filename)

        prompt_text = f"""
You are the Lead AI Data Scientist at DataWise AI.
Analyze the following dataset context and user request to create a structured Machine Learning Project Blueprint.

DATASET CONTEXT:
- Filename: {dataset_filename or 'Unknown'}
- Rows: {dataset_info.get('row_count', 'Unknown')}
- Columns: {json.dumps(dataset_info.get('columns', [])[:30])}
- Target Candidate: {dataset_info.get('recommended_target') or dataset_info.get('target_candidate') or 'Unknown'}
- Column Types: {json.dumps(dataset_info.get('dtypes', {}))}
- User Objective/Prompt: {user_prompt or 'Autonomous AutoML exploration'}

INSTRUCTIONS:
Respond with a strict JSON object containing:
{{
  "project_name": "Concise, professional title (e.g. 'Credit Card Fraud Anomaly Engine' or 'California Housing Valuation')",
  "project_description": "2-sentence executive summary of the problem and approach",
  "business_problem": "Specific operational or business goal this model solves",
  "target_candidate": "Best column name to predict",
  "ml_task": "classification" or "regression",
  "primary_metric": "Primary optimization metric (F1, ROC-AUC, RMSE, R2, etc.)",
  "secondary_metrics": ["List", "of", "metrics"],
  "recommended_pipeline": ["Step 1", "Step 2", "Step 3", "Step 4"],
  "deployment_context": "Recommended deployment pattern (e.g., REST API, Batch, Edge)",
  "expected_output": "Summary of deliverables",
  "risks": ["Potential data quality or operational risks"],
  "project_prompt": "A rigorous, detailed prompt guiding the downstream AutoML agents"
}}

CRITICAL RULES:
- Never mention or default to unrelated domains (e.g. do not say Customer Churn if dataset is about housing or fraud!).
- Tailor strictly to the actual columns and user prompt.
- Return ONLY valid JSON without markdown fences.
"""
        try:
            resp = await self.llm.generate([
                LLMMessage(role="system", content="You are a principal ML systems architect. Output valid JSON only."),
                LLMMessage(role="user", content=prompt_text),
            ])
            content = resp.content.strip()
            # Clean possible markdown JSON wrappers
            content = re.sub(r"^```json\s*", "", content)
            content = re.sub(r"^```\s*", "", content)
            content = re.sub(r"\s*```$", "", content)
            plan = json.loads(content)

            # Ensure all required keys exist
            for k, v in deterministic.items():
                if k not in plan or not plan[k]:
                    plan[k] = v

            plan["task_type"] = plan.get("task_type") or plan.get("task") or plan.get("ml_task") or deterministic["task_type"]
            plan["task"] = plan["task_type"]
            plan["target_candidate"] = plan.get("target_candidate") or plan.get("target") or deterministic["target_candidate"]
            plan["target"] = plan["target_candidate"]

            if custom_name:
                plan["project_name"] = custom_name

            return plan
        except Exception as exc:
            logger.warning(f"LLM project planning fallback to deterministic: {exc}")
            if custom_name:
                deterministic["project_name"] = custom_name
            return deterministic


project_planner_agent = ProjectPlannerAgent()
