"""
DataWise AI — LangGraph Workflow

Full StateGraph connecting all analysis nodes:
  INGEST → PROFILE → QUALITY → OUTLIERS → DISTRIBUTIONS → CORRELATIONS →
  PREPROCESSING → HUMAN_APPROVAL → FEATURE_ENGINEERING → FEATURE_SELECTION →
  TARGET_DETECTION → LEAKAGE_CHECK → PIPELINE_BUILDING → ML_RECOMMENDATION →
  COMPLETE

Human-in-the-loop interrupts are managed via HumanApprovalNode.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, Literal, Optional

import pandas as pd
from loguru import logger

from app.agents.coordinator import multi_agent_coordinator
from app.agents.governance import HumanApprovalNode
from app.graph.llm_provider import LLMMessage, llm_provider
from app.state.data_science_state import DataScienceState
from app.tools.correlations import CorrelationAnalyzer
from app.tools.distributions import DistributionAnalyzer
from app.tools.feature_engineering import FeatureEngineer
from app.tools.feature_selection import FeatureSelector
from app.tools.leakage import LeakageDetector
from app.tools.ml_recommender import MLRecommender
from app.tools.outliers import OutlierAnalyzer
from app.tools.pipeline_builder import PipelineBuilder
from app.tools.profiler import profile_dataframe
from app.tools.quality import QualityAnalyzer
from app.tools.target_detector import TargetDetector


# ------------------------------------------------------------------ #
#  System Prompt
# ------------------------------------------------------------------ #

SYSTEM_PROMPT = """You are DataWise AI, a world-class AI data scientist assistant.

Your job is to:
1. Guide the user through every step of the data science lifecycle
2. Explain findings in clear, accessible language
3. Propose actions with rationale and require confirmation for destructive operations
4. Generate production-quality sklearn pipelines and ML project roadmaps
5. Flag data quality issues, leakage risks, and class imbalance proactively

Communication Style:
- Use structured markdown with headers and bullet points
- Quantify every claim (e.g., "32.4% missing values", not "many missing values")
- Highlight critical issues with ⚠️ and good findings with ✅
- Always explain WHY a recommendation matters for ML performance
"""


# ------------------------------------------------------------------ #
#  Node implementations
# ------------------------------------------------------------------ #

def _load_df(state: DataScienceState) -> Optional[pd.DataFrame]:
    """Load dataset from path stored in state."""
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
        logger.error(f"Failed to load dataset at {path}: {exc}")
        return None


# ─── Node: Profile ────────────────────────────────────────────────────────────

def profile_node(state: DataScienceState) -> DataScienceState:
    """Run dataset profiling via ProfilingAgent."""
    logger.info(f"[Node: PROFILE] session={state.get('session_id')}")
    return multi_agent_coordinator.profiling_agent.run(state)


# ─── Node: Quality ────────────────────────────────────────────────────────────

def quality_node(state: DataScienceState) -> DataScienceState:
    """Run missing value and duplicate analysis via QualityAgent."""
    logger.info(f"[Node: QUALITY] session={state.get('session_id')}")
    return multi_agent_coordinator.quality_agent.run(state)


# ─── Node: Human Approval ─────────────────────────────────────────────────────

def human_approval_node(state: DataScienceState) -> DataScienceState:
    """Check for pending human decisions. Pause if needed."""
    logger.info(f"[Node: HUMAN_APPROVAL] session={state.get('session_id')}")
    pending = HumanApprovalNode.inspect_proposed_actions(state)
    if pending:
        return {
            **state,
            "pending_decision": pending,
            "should_continue": False,
            "current_stage": "HUMAN_APPROVAL",
        }
    return {
        **state,
        "pending_decision": None,
        "should_continue": True,
        "current_stage": "OUTLIERS",
        "completed_stages": [*state.get("completed_stages", []), "HUMAN_APPROVAL"],
    }


# ─── Node: Outliers ───────────────────────────────────────────────────────────

def outlier_node(state: DataScienceState) -> DataScienceState:
    """Run outlier detection via OutlierAgent."""
    logger.info(f"[Node: OUTLIERS] session={state.get('session_id')}")
    return multi_agent_coordinator.outlier_agent.run(state)


# ─── Node: Distributions ─────────────────────────────────────────────────────

def distribution_node(state: DataScienceState) -> DataScienceState:
    logger.info(f"[Node: DISTRIBUTIONS] session={state.get('session_id')}")
    df = _load_df(state)
    if df is None:
        return state

    try:
        analyzer = DistributionAnalyzer(df)
        result = analyzer.analyze()
        return {
            **state,
            "distribution_report": result,
            "current_stage": "CORRELATIONS",
            "completed_stages": [*state.get("completed_stages", []), "DISTRIBUTIONS"],
        }
    except Exception as exc:  # noqa: BLE001
        logger.exception(f"Distribution node failed: {exc}")
        return state


# ─── Node: Correlations ───────────────────────────────────────────────────────

def correlation_node(state: DataScienceState) -> DataScienceState:
    logger.info(f"[Node: CORRELATIONS] session={state.get('session_id')}")
    df = _load_df(state)
    if df is None:
        return state

    try:
        analyzer = CorrelationAnalyzer(df)
        result = analyzer.analyze()
        return {
            **state,
            "correlation_report": result,
            "current_stage": "FEATURE_ENGINEERING",
            "completed_stages": [*state.get("completed_stages", []), "CORRELATIONS"],
        }
    except Exception as exc:  # noqa: BLE001
        logger.exception(f"Correlation node failed: {exc}")
        return state


# ─── Node: Feature Engineering ───────────────────────────────────────────────

def feature_engineering_node(state: DataScienceState) -> DataScienceState:
    """Run feature engineering recommendations via FeatureEngineeringAgent."""
    logger.info(f"[Node: FEATURE_ENGINEERING] session={state.get('session_id')}")
    return multi_agent_coordinator.feature_engineering_agent.run(state)


# ─── Node: Feature Selection ─────────────────────────────────────────────────

def feature_selection_node(state: DataScienceState) -> DataScienceState:
    """Run feature selection via FeatureSelectionAgent."""
    logger.info(f"[Node: FEATURE_SELECTION] session={state.get('session_id')}")
    return multi_agent_coordinator.feature_selection_agent.run(state)


# ─── Node: Target Detection ───────────────────────────────────────────────────

def target_detection_node(state: DataScienceState) -> DataScienceState:
    logger.info(f"[Node: TARGET_DETECTION] session={state.get('session_id')}")
    df = _load_df(state)
    if df is None:
        return state

    # Skip if user already confirmed target
    if state.get("target_column"):
        return {**state, "current_stage": "LEAKAGE_CHECK"}

    try:
        detector = TargetDetector(df)
        result = detector.detect()
        candidates = [c["column"] for c in result.get("candidates", [])]
        return {
            **state,
            "target_candidates": candidates,
            "current_stage": "LEAKAGE_CHECK",
            "completed_stages": [*state.get("completed_stages", []), "TARGET_DETECTION"],
        }
    except Exception as exc:  # noqa: BLE001
        logger.exception(f"Target detection node failed: {exc}")
        return state


# ─── Node: Leakage Check ─────────────────────────────────────────────────────

def leakage_node(state: DataScienceState) -> DataScienceState:
    logger.info(f"[Node: LEAKAGE_CHECK] session={state.get('session_id')}")
    df = _load_df(state)
    if df is None:
        return state

    try:
        detector = LeakageDetector(
            df,
            target_column=state.get("target_column"),
            task_type=state.get("task_type"),
        )
        result = detector.detect()
        return {
            **state,
            "leakage_warnings": result.get("warnings", []),
            "current_stage": "PIPELINE_BUILDING",
            "completed_stages": [*state.get("completed_stages", []), "LEAKAGE_CHECK"],
        }
    except Exception as exc:  # noqa: BLE001
        logger.exception(f"Leakage node failed: {exc}")
        return state


# ─── Node: Pipeline Building ─────────────────────────────────────────────────

def pipeline_node(state: DataScienceState) -> DataScienceState:
    """Run pipeline construction via PipelineBuilderAgent."""
    logger.info(f"[Node: PIPELINE_BUILDING] session={state.get('session_id')}")
    return multi_agent_coordinator.pipeline_builder_agent.run(state)


# ─── Node: ML Recommendation ─────────────────────────────────────────────────

def ml_recommendation_node(state: DataScienceState) -> DataScienceState:
    """Run ML algorithm recommendation via MLRecommendationAgent."""
    logger.info(f"[Node: ML_RECOMMENDATION] session={state.get('session_id')}")
    return multi_agent_coordinator.ml_recommendation_agent.run(state)


# ─── Node: Training ───────────────────────────────────────────────────────────

def training_node(state: DataScienceState) -> DataScienceState:
    """Run candidate model training and cross-validation via TrainingAgent."""
    logger.info(f"[Node: TRAINING] session={state.get('session_id')}")
    return multi_agent_coordinator.training_agent.run(state)


# ─── Node: Evaluation ─────────────────────────────────────────────────────────

def evaluation_node(state: DataScienceState) -> DataScienceState:
    """Run covariate shift check and production readiness audit via EvaluationAgent."""
    logger.info(f"[Node: EVALUATION] session={state.get('session_id')}")
    return multi_agent_coordinator.evaluation_agent.run(state)


# ─── Node: Explainability ─────────────────────────────────────────────────────

def explainability_node(state: DataScienceState) -> DataScienceState:
    """Run feature importance and permutation importance via ExplainabilityAgent."""
    logger.info(f"[Node: EXPLAINABILITY] session={state.get('session_id')}")
    return multi_agent_coordinator.explainability_agent.run(state)


# ─── Node: Notebook ───────────────────────────────────────────────────────────

def notebook_node(state: DataScienceState) -> DataScienceState:
    """Generate standalone 24-section Jupyter Notebook via NotebookAgent."""
    logger.info(f"[Node: NOTEBOOK] session={state.get('session_id')}")
    return multi_agent_coordinator.notebook_agent.run(state)


# ─── Node: Artifacts ──────────────────────────────────────────────────────────

def artifact_node(state: DataScienceState) -> DataScienceState:
    """Serialize model pipeline, metadata, and ZIP bundle via ArtifactManagerAgent."""
    logger.info(f"[Node: ARTIFACTS] session={state.get('session_id')}")
    return multi_agent_coordinator.artifact_agent.run(state)


# ─── Node: LLM Interpreter ───────────────────────────────────────────────────

async def llm_interpreter_node(state: DataScienceState) -> DataScienceState:
    """
    Generates a natural language interpretation of the current analysis stage.
    Called after any analysis node to add an AI explanation to conversation history.
    """
    stage = state.get("current_stage", "UNKNOWN")
    history = state.get("conversation_history", [])

    # Build context summary based on current stage
    context = _build_stage_context(state, stage)

    messages = [
        LLMMessage(role="user", content=(
            f"I'm at the {stage} stage of my data analysis. "
            f"Here's the analysis summary:\n\n{context}\n\n"
            f"Please provide a clear, structured interpretation of these findings "
            f"and what the user should do next."
        ))
    ]

    try:
        response = await llm_provider.complete(
            messages=messages,
            system_prompt=SYSTEM_PROMPT,
            temperature=0.3,
            max_tokens=1500,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"LLM interpretation failed: {exc}")
        response = f"Analysis completed at stage: {stage}. Please review the detailed results above."

    new_message = {"role": "assistant", "content": response}
    return {
        **state,
        "conversation_history": [*history, new_message],
        "total_llm_calls": state.get("total_llm_calls", 0) + 1,
    }


# ------------------------------------------------------------------ #
#  Context builder for LLM
# ------------------------------------------------------------------ #

def _build_stage_context(state: DataScienceState, stage: str) -> str:  # noqa: C901
    lines: list[str] = []

    if stage in ("PROFILE", "QUALITY", "OUTLIERS", "DISTRIBUTIONS", "CORRELATIONS"):
        profiles = state.get("column_profiles", [])
        if profiles:
            lines.append(f"Dataset: {len(profiles)} columns profiled.")
        missing = state.get("missing_value_report", [])
        critical = [r for r in missing if r.get("severity") in ("HIGH", "CRITICAL")]
        if critical:
            lines.append(f"⚠️ {len(critical)} columns with HIGH/CRITICAL missing values.")
        dup = state.get("duplicate_report", {})
        if dup.get("has_duplicates"):
            lines.append(f"⚠️ {dup.get('duplicate_count')} duplicate rows ({dup.get('duplicate_pct')}%).")
        outliers = state.get("outlier_report", [])
        severe = [o for o in outliers if o.get("severity") == "severe"]
        if severe:
            lines.append(f"⚠️ {len(severe)} columns with severe outlier contamination.")

    if stage in ("FEATURE_ENGINEERING", "FEATURE_SELECTION"):
        fe_plan = state.get("feature_engineering_plan", [])
        if fe_plan:
            lines.append(f"Feature engineering: {len(fe_plan)} new feature operations planned.")
        fs = state.get("feature_selection_results", [])
        dropped = [f for f in fs if not f.get("selected")]
        if dropped:
            lines.append(f"Feature selection: recommends dropping {len(dropped)} low-information features.")

    if stage in ("LEAKAGE_CHECK",):
        warnings = state.get("leakage_warnings", [])
        critical = [w for w in warnings if w.get("severity") == "CRITICAL"]
        if critical:
            lines.append(f"🚨 CRITICAL: {len(critical)} direct data leakage column(s) detected!")

    if stage in ("ML_RECOMMENDATION", "COMPLETE"):
        readiness = state.get("ml_readiness_report", {})
        if readiness:
            lines.append(f"ML Readiness Score: {readiness.get('score', 'N/A')}/100 — {readiness.get('level', '')}.")
        recs = state.get("model_recommendations", [])
        if recs:
            lines.append(f"Top recommended model: {recs[0].get('model_name', '')}.")

    if stage in ("TRAINING", "EVALUATION"):
        models = state.get("trained_models", [])
        champ = state.get("selected_final_model")
        metric = state.get("primary_metric", "Score")
        if models:
            lines.append(f"Models trained: {len(models)}. Champion: {champ} optimized for {metric}.")

    if not lines:
        lines.append(f"Analysis at stage: {stage}.")

    return "\n".join(lines)


# ------------------------------------------------------------------ #
#  Workflow runner (simple sequential, no LangGraph dependency required)
# ------------------------------------------------------------------ #

async def run_analysis_workflow(state: DataScienceState) -> DataScienceState:
    """
    Runs the full sequential analysis pipeline on a DataScienceState.
    Returns the final state after all nodes have executed.

    This is the synchronous fallback used when LangGraph is unavailable.
    The full LangGraph StateGraph implementation below is used when available.
    """
    pipeline = [
        profile_node,
        quality_node,
        human_approval_node,
        outlier_node,
        distribution_node,
        correlation_node,
        feature_engineering_node,
        feature_selection_node,
        target_detection_node,
        leakage_node,
        pipeline_node,
        ml_recommendation_node,
        training_node,
        evaluation_node,
        explainability_node,
        notebook_node,
        artifact_node,
    ]

    current_state = state
    for node_fn in pipeline:
        try:
            current_state = node_fn(current_state)
            # Stop if human input is required
            if not current_state.get("should_continue", True) and current_state.get("pending_decision"):
                logger.info(f"Workflow paused at {current_state.get('current_stage')} awaiting human decision.")
                break
        except Exception as exc:  # noqa: BLE001
            logger.exception(f"Node {node_fn.__name__} failed: {exc}")
            current_state = {
                **current_state,
                "errors": [*current_state.get("errors", []), {"stage": node_fn.__name__, "error": str(exc)}],
            }

    # Run LLM interpretation on final state
    try:
        current_state = await llm_interpreter_node(current_state)
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"LLM interpretation failed: {exc}")

    return current_state


# ------------------------------------------------------------------ #
#  LangGraph StateGraph (optional, requires langgraph installed)
# ------------------------------------------------------------------ #

def build_langgraph_workflow():
    """
    Build the full LangGraph StateGraph.
    Returns None if langgraph is not installed.
    """
    try:
        from langgraph.graph import END, StateGraph  # type: ignore

        def should_continue(state: DataScienceState) -> Literal["continue", "pause"]:
            if state.get("should_continue", True) is False and state.get("pending_decision"):
                return "pause"
            return "continue"

        workflow = StateGraph(DataScienceState)

        # Add nodes
        workflow.add_node("profile", profile_node)
        workflow.add_node("quality", quality_node)
        workflow.add_node("human_approval", human_approval_node)
        workflow.add_node("outliers", outlier_node)
        workflow.add_node("distributions", distribution_node)
        workflow.add_node("correlations", correlation_node)
        workflow.add_node("feature_engineering", feature_engineering_node)
        workflow.add_node("feature_selection", feature_selection_node)
        workflow.add_node("target_detection", target_detection_node)
        workflow.add_node("leakage", leakage_node)
        workflow.add_node("pipeline", pipeline_node)
        workflow.add_node("ml_recommendation", ml_recommendation_node)
        workflow.add_node("training", training_node)
        workflow.add_node("evaluation", evaluation_node)
        workflow.add_node("explainability", explainability_node)
        workflow.add_node("notebook", notebook_node)
        workflow.add_node("artifacts", artifact_node)

        # Set entry point
        workflow.set_entry_point("profile")

        # Linear edges
        workflow.add_edge("profile", "quality")
        workflow.add_edge("quality", "human_approval")

        # Conditional edge from human_approval
        workflow.add_conditional_edges(
            "human_approval",
            should_continue,
            {"continue": "outliers", "pause": END},
        )

        workflow.add_edge("outliers", "distributions")
        workflow.add_edge("distributions", "correlations")
        workflow.add_edge("correlations", "feature_engineering")
        workflow.add_edge("feature_engineering", "feature_selection")
        workflow.add_edge("feature_selection", "target_detection")
        workflow.add_edge("target_detection", "leakage")
        workflow.add_edge("leakage", "pipeline")
        workflow.add_edge("pipeline", "ml_recommendation")
        workflow.add_edge("ml_recommendation", "training")
        workflow.add_edge("training", "evaluation")
        workflow.add_edge("evaluation", "explainability")
        workflow.add_edge("explainability", "notebook")
        workflow.add_edge("notebook", "artifacts")
        workflow.add_edge("artifacts", END)

        return workflow.compile()

    except ImportError:
        logger.warning("langgraph not installed. Using sequential fallback workflow.")
        return None


# Module-level compiled graph (None if langgraph unavailable)
compiled_workflow = build_langgraph_workflow()

