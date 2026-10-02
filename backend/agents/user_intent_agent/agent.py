"""
Agentic AutoML Intelligence Platform — User Intent Agent
Analyzes user natural language goals, business objectives, and custom metric priorities.
"""

from __future__ import annotations

from typing import Any, Dict
from agents.base import BaseAgent, AgentInput, AgentOutput


class UserIntentAgent(BaseAgent):
    def __init__(self, session_id: str = ""):
        super().__init__(session_id=session_id, agent_name="UserIntentAgent")

    def analyze(self, input_data: AgentInput) -> AgentOutput:
        user_prompt = input_data.parameters.get("prompt", "") or input_data.parameters.get("user_goal", "")
        prompt_lower = user_prompt.lower()

        # Deduce primary domain and objective
        domain = "general"
        recommended_metric = "f1"
        is_rare_event = False

        if any(w in prompt_lower for w in ["fraud", "anomaly", "cyber", "rare", "intrusion", "failure"]):
            domain = "fraud_or_rare_event"
            recommended_metric = "pr_auc"
            is_rare_event = True
        elif any(w in prompt_lower for w in ["churn", "conversion", "retention"]):
            domain = "customer_behavior"
            recommended_metric = "roc_auc"
        elif any(w in prompt_lower for w in ["predict price", "forecast", "revenue", "sales", "cost"]):
            domain = "regression_or_forecasting"
            recommended_metric = "rmse"

        intent_data = {
            "user_prompt": user_prompt,
            "inferred_domain": domain,
            "primary_metric": recommended_metric,
            "is_rare_event": is_rare_event,
            "optimization_priority": "robustness_and_precision" if is_rare_event else "balanced_generalization",
        }

        return AgentOutput(
            session_id=input_data.session_id,
            agent_name=self.agent_name,
            status="success",
            data=intent_data,
            summary=f"Understood objective: {domain}. Recommended evaluation metric: {recommended_metric.upper()}.",
        )
