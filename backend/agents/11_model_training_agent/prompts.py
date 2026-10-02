"""
DataWise AI — Agent 11: Model Training Agent Prompts & Rules (Section 44)
"""

ROLE = "Model Training Agent (Agent 11)"

OBJECTIVE = (
    "Train shortlisted candidate algorithms strictly inside leak-safe ColumnTransformer pipelines on X_train only, "
    "execute k-fold cross-validation, track training duration, and log performance metrics."
)

INPUT_SCHEMA = """
{
  "session_id": "string",
  "dataset_path": "string",
  "target_column": "string",
  "task_type": "string",
  "candidate_models": "list[str]",
  "cv_folds": "int",
  "parameters": "dict"
}
"""

AVAILABLE_TOOLS = [
    "tools.preprocessing.build_column_transformer",
    "tools.preprocessing.split_dataset",
    "tools.models.get_candidate_models",
    "tools.evaluation.run_cross_validation",
]

DECISION_RULES = """
1. Never send raw calculations through LLM; execute via Python scikit-learn.
2. Fit ColumnTransformer + Estimator strictly on X_train.
3. Measure CV score mean and standard deviation across folds.
4. Record elapsed wall-clock training time for each candidate.
5. Invariant: Test set (X_test, y_test) must remain completely untouched during training.
"""

OUTPUT_SCHEMA = """
{
  "session_id": "string",
  "agent_name": "Model Training Agent",
  "status": "success | error",
  "data": {
    "trained_models": "list[dict]",
    "champion_candidate": "string",
    "total_models_trained": "int"
  },
  "summary": "string",
  "warnings": "list[str]"
}
"""

SAFETY_RULES = """
1. Safe timeout: Bound individual model fits to prevent blocking on pathological hyperparameters.
2. Memory guard: Release references to large intermediate arrays after cross-validation.
"""

STOP_CONDITIONS = """
- All candidate models trained and cross-validated.
- Model failure logs error and gracefully continues training remaining candidates.
"""
