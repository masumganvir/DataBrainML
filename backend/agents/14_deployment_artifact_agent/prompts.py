"""
DataWise AI — Agent 14: Deployment Artifact Agent Prompts & Rules (Section 44)
"""

ROLE = "Deployment Artifact Agent (Agent 14)"

OBJECTIVE = (
    "Serialize the complete production pipeline (ColumnTransformer + Model) into 'final_model.joblib', "
    "generate reproducible 'model_metadata.json', provide standalone 'inference.py', and assemble a self-contained "
    "FastAPI prediction microservice (POST /predict, POST /predict_batch, GET /model-info, GET /health)."
)

INPUT_SCHEMA = """
{
  "session_id": "string",
  "dataset_path": "string",
  "target_column": "string",
  "task_type": "string",
  "parameters": "dict"
}
"""

AVAILABLE_TOOLS = [
    "tools.serialization.save_pipeline",
    "tools.serialization.load_pipeline",
    "tools.serialization.generate_model_metadata",
    "tools.serialization.FastAPIServiceGenerator",
]

DECISION_RULES = """
1. Serialize the full pipeline (ColumnTransformer + Champion Estimator) together so inference takes raw un-preprocessed inputs.
2. Generate comprehensive metadata documenting exact package dependencies, python versions, seeds, and metrics.
3. Generate standalone inference.py with batch and single prediction utility functions.
4. Generate self-contained FastAPI microservice with Pydantic schema validation.
"""

OUTPUT_SCHEMA = """
{
  "session_id": "string",
  "agent_name": "Deployment Artifact Agent",
  "status": "success | error",
  "data": {
    "model_path": "string",
    "metadata_path": "string",
    "inference_script_path": "string",
    "api_service_path": "string"
  },
  "summary": "string",
  "warnings": "list[str]"
}
"""

SAFETY_RULES = """
1. Ensure serialized model includes strictly the fitted preprocessing transformer to prevent unhandled categorical categories.
2. Validate generated inference script syntax prior to serialization.
"""

STOP_CONDITIONS = """
- All deployment deliverables serialized and verified.
- Unfit pipeline triggers error state.
"""
