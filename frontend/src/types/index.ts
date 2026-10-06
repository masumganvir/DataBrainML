/**
 * DataWise AI — TypeScript Type Definitions
 *
 * These types mirror the backend Pydantic schemas and LangGraph state.
 */

// ------------------------------------------------------------------ //
//  Session
// ------------------------------------------------------------------ //
export interface Session {
  id: string;
  name: string;
  status: 'created' | 'active' | 'completed' | 'error';
  current_stage: DataStage;
  task_type: TaskType | null;
  target_column: string | null;
  created_at: string;
  updated_at: string;
}

export type TaskType = 'classification' | 'regression' | 'clustering' | 'time_series';

export type DataStage =
  | 'INGEST'
  | 'PROFILE'
  | 'DATA_QUALITY'
  | 'OUTLIERS'
  | 'VISUALIZATION'
  | 'MISSING_VALUE_DECISION'
  | 'ENCODING_DECISION'
  | 'SCALING_DECISION'
  | 'TRANSFORMATION'
  | 'FEATURE_ENGINEERING'
  | 'FEATURE_SELECTION'
  | 'TARGET_CONFIRMATION'
  | 'LEAKAGE_CHECK'
  | 'ML_READINESS'
  | 'PIPELINE_GENERATION'
  | 'MODEL_RECOMMENDATION'
  | 'REPORT'
  | 'END';

// ------------------------------------------------------------------ //
//  Dataset
// ------------------------------------------------------------------ //
export interface Dataset {
  id: string;
  session_id: string;
  version: 'original' | 'analysis' | 'preprocessed' | 'feature_engineered' | 'final';
  original_filename: string;
  file_format: 'csv' | 'xlsx' | 'xls' | 'json';
  file_size_bytes: number;
  row_count: number | null;
  column_count: number | null;
  created_at: string;
  schema_info: Record<string, string> | null;
  profile_summary: DatasetProfileSummary | null;
  quality_summary: QualitySummary | null;
}

export interface DatasetProfileSummary {
  total_rows: number;
  total_columns: number;
  memory_usage_mb: number;
  numerical_columns: string[];
  categorical_columns: string[];
  datetime_columns: string[];
  identifier_columns: string[];
  constant_columns: string[];
  missing_total: number;
  duplicate_rows: number;
}

export interface QualitySummary {
  missing_columns: number;
  high_missing_columns: string[];
  duplicate_count: number;
  outlier_columns: string[];
}

// ------------------------------------------------------------------ //
//  Column Profile
// ------------------------------------------------------------------ //
export interface ColumnProfile {
  name: string;
  dtype: string;
  unique_count: number;
  unique_ratio: number;
  missing_count: number;
  missing_pct: number;
  mean?: number;
  median?: number;
  mode?: unknown;
  std?: number;
  min?: number;
  max?: number;
  q1?: number;
  q3?: number;
  skewness?: number;
  kurtosis?: number;
  is_identifier: boolean;
  is_constant: boolean;
}

// ------------------------------------------------------------------ //
//  Analysis Reports
// ------------------------------------------------------------------ //
export interface MissingValueReport {
  column: string;
  missing_count: number;
  missing_pct: number;
  dtype: string;
  severity: 'NONE' | 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  recommended_strategy: string;
  alternative_strategies: string[];
  explanation: string;
}

export interface OutlierReport {
  column: string;
  method: string;
  outlier_count: number;
  outlier_pct: number;
  lower_bound: number | null;
  upper_bound: number | null;
  severity: 'none' | 'mild' | 'moderate' | 'severe';
  interpretation: string;
}

export interface CorrelationPair {
  feature_a: string;
  feature_b: string;
  correlation: number;
  method: string;
  warning: string;
}

// ------------------------------------------------------------------ //
//  Visualizations
// ------------------------------------------------------------------ //
export interface VisualizationResult {
  artifact_id: string;
  column?: string;
  chart_type: string;
  file_path: string;
  file_format: 'png' | 'svg' | 'html';
  title: string;
  ai_interpretation: string;
}

// ------------------------------------------------------------------ //
//  Human-in-the-Loop Decision
// ------------------------------------------------------------------ //
export interface PendingDecision {
  id: string;
  stage: DataStage;
  question: string;
  context: Record<string, unknown>;
  options: DecisionOption[];
  allow_custom: boolean;
}

export interface DecisionOption {
  value: string;
  label: string;
  description?: string;
}

export interface UserDecision {
  decision_key: string;
  decision_value: string;
  stage: DataStage;
  created_at: string;
}

// ------------------------------------------------------------------ //
//  Chat
// ------------------------------------------------------------------ //
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system' | 'tool';
  content: string;
  created_at: string;
  metadata?: {
    stage?: DataStage;
    tool_name?: string;
    artifacts?: string[];
    pending_decision?: PendingDecision;
  };
}

// ------------------------------------------------------------------ //
//  ML Recommendations
// ------------------------------------------------------------------ //
export interface ModelRecommendation {
  model_name: string;
  model_class: string;
  rationale: string;
  pros: string[];
  cons: string[];
  evaluation_metrics: string[];
}

export type MLReadinessLevel = 'NOT_READY' | 'NEEDS_PREPROCESSING' | 'READY_FOR_BASELINE';

export interface MLReadinessReport {
  level: MLReadinessLevel;
  score: number;
  checks: ReadinessCheck[];
  summary: string;
}

export interface ReadinessCheck {
  name: string;
  passed: boolean;
  detail: string;
}

// ------------------------------------------------------------------ //
//  Pipeline
// ------------------------------------------------------------------ //
export interface PipelineDefinition {
  numerical_columns: string[];
  categorical_columns: string[];
  numerical_imputer: string;
  numerical_scaler?: string;
  categorical_imputer: string;
  categorical_encoder: string;
  selected_features: string[];
  target_column: string;
  task_type: TaskType;
  generated_code: string;
}

// ------------------------------------------------------------------ //
//  Artifacts
// ------------------------------------------------------------------ //
export interface Artifact {
  id: string;
  session_id: string;
  artifact_type: 'plot' | 'report' | 'code' | 'pipeline' | 'data';
  name: string;
  description?: string;
  file_format: string;
  file_size_bytes: number;
  created_at: string;
}

// ------------------------------------------------------------------ //
//  API Responses
// ------------------------------------------------------------------ //
export interface ApiError {
  error: string;
  message: string;
  detail?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

// ------------------------------------------------------------------ //
//  Stage Progress
// ------------------------------------------------------------------ //
export const STAGE_ORDER: DataStage[] = [
  'INGEST',
  'PROFILE',
  'DATA_QUALITY',
  'OUTLIERS',
  'VISUALIZATION',
  'MISSING_VALUE_DECISION',
  'ENCODING_DECISION',
  'SCALING_DECISION',
  'TRANSFORMATION',
  'FEATURE_ENGINEERING',
  'FEATURE_SELECTION',
  'TARGET_CONFIRMATION',
  'LEAKAGE_CHECK',
  'ML_READINESS',
  'PIPELINE_GENERATION',
  'MODEL_RECOMMENDATION',
  'REPORT',
  'END',
];

export const STAGE_LABELS: Record<DataStage, string> = {
  INGEST: 'Dataset Loaded',
  PROFILE: 'Schema Analyzed',
  DATA_QUALITY: 'Quality Checked',
  OUTLIERS: 'Outliers Detected',
  VISUALIZATION: 'Visualizations Generated',
  MISSING_VALUE_DECISION: 'Missing Values',
  ENCODING_DECISION: 'Encoding Strategy',
  SCALING_DECISION: 'Scaling Strategy',
  TRANSFORMATION: 'Feature Transformation',
  FEATURE_ENGINEERING: 'Feature Engineering',
  FEATURE_SELECTION: 'Feature Selection',
  TARGET_CONFIRMATION: 'Target Confirmed',
  LEAKAGE_CHECK: 'Leakage Checked',
  ML_READINESS: 'ML Readiness',
  PIPELINE_GENERATION: 'Pipeline Built',
  MODEL_RECOMMENDATION: 'Model Recommended',
  REPORT: 'Report Generated',
  END: 'Complete',
};

// ------------------------------------------------------------------ //
//  AutoML & Model Comparison Types
// ------------------------------------------------------------------ //
export interface ModelComparisonResult {
  model_name: string;
  model_class: string;
  cv_scores: number[];
  cv_mean: number;
  cv_std: number;
  test_metrics: Record<string, number>;
  training_time_seconds: number;
  hyperparameters: Record<string, string>;
  is_selected: boolean;
  is_champion?: boolean;
  selection_rationale?: string;
}

export interface ProductionReadinessCheck {
  check: string;
  passed: boolean;
  detail: string;
}

export interface ProductionReadinessReport {
  status: 'PASS' | 'WARNING' | 'FAIL';
  readiness_score: number;
  checklist: ProductionReadinessCheck[];
  reasons: string[];
  limitations?: string[];
}

export interface DatasetShiftReport {
  has_distribution_shift: boolean;
  numerical_shifts: Array<{ feature: string; p_value: number; status: string }>;
  warning_message?: string;
}

export interface TrainingResponse {
  session_id: string;
  task_type: string;
  target_column: string;
  primary_metric: string;
  cv_strategy: string;
  selected_final_model: string;
  models: ModelComparisonResult[];
  selection_rationale: string;
  production_readiness?: ProductionReadinessReport;
  dataset_shift?: DatasetShiftReport;
  feature_importance?: Record<string, number>;
  limitations?: string[];
}

// ------------------------------------------------------------------ //
//  Enterprise Multi-Tenancy & Project Hierarchy
// ------------------------------------------------------------------ //
export type UserRole = 'owner' | 'admin' | 'data_scientist' | 'ml_engineer' | 'viewer';

export interface UserProfile {
  id: string;
  email: string;
  name: string;
  role: UserRole;
  avatar_url?: string;
  organization_id?: string;
  organization_name?: string;
  mfa_enabled: boolean;
  created_at: string;
}

export interface Project {
  id: string;
  name: string;
  slug?: string;
  description: string;
  objective?: string;
  created_at: string;
  updated_at: string;
  dataset_count: number;
  experiment_count: number;
  model_count: number;
  active_deployment: boolean;
  status: 'active' | 'archived' | 'training' | string;
  current_champion_model?: string;
  current_dataset_id?: string;
  current_run_id?: string;
  tags: string[];
  configuration?: any;
  project_metadata?: any;
}

export interface PipelineNode {
  id: string;
  name: string;
  agent: string;
  stage: string;
  status: 'queued' | 'running' | 'waiting' | 'success' | 'warning' | 'failed' | 'retrying';
  duration_seconds: number;
  input_summary?: string;
  output_summary?: string;
  error?: string;
  details?: Record<string, any>;
}

export interface RegisteredModel {
  id: string;
  project_id: string;
  name: string;
  version: string;
  model_family: string;
  framework: 'scikit-learn' | 'xgboost' | 'lightgbm' | 'pytorch' | 'catboost';
  stage: 'development' | 'staging' | 'production' | 'archived';
  metrics: {
    accuracy?: number;
    f1: number;
    roc_auc?: number;
    rmse?: number;
    mae?: number;
    inference_latency_ms: number;
  };
  artifact_size_mb: number;
  sha256_checksum: string;
  created_at: string;
  author: string;
  is_champion: boolean;
  top_features: Array<{ feature: string; importance: number }>;
}

export interface DeploymentRecord {
  id: string;
  project_id: string;
  model_id: string;
  model_name: string;
  version: string;
  environment: 'production' | 'staging' | 'dev';
  status: 'healthy' | 'degraded' | 'deploying' | 'failed' | 'stopped';
  endpoint_url: string;
  container_image: string;
  cpu_usage_pct: number;
  memory_usage_mb: number;
  requests_per_minute: number;
  p99_latency_ms: number;
  uptime_pct: number;
  created_at: string;
  last_rollback_available: boolean;
}

export interface DriftMetric {
  feature_name: string;
  metric_type: 'PSI' | 'KS';
  statistic_value: number;
  p_value?: number;
  severity: 'none' | 'moderate' | 'critical';
  threshold: number;
  detected_at: string;
  baseline_mean: number;
  current_mean: number;
}

export interface SystemAlert {
  id: string;
  severity: 'critical' | 'warning' | 'info';
  category: 'drift' | 'latency' | 'quality' | 'security' | 'worker';
  title: string;
  message: string;
  resource_id?: string;
  created_at: string;
  acknowledged: boolean;
}

export interface AuditRecord {
  id: string;
  timestamp: string;
  actor_email: string;
  actor_role: string;
  action: string;
  resource_type: string;
  resource_name: string;
  ip_address_masked: string;
  status: 'SUCCESS' | 'FAILED' | 'BLOCKED';
  request_id: string;
}

export interface DatabaseConnector {
  id: string;
  name: string;
  type: 'postgresql' | 'mysql' | 'mongodb' | 's3' | 'rest_api';
  status: 'connected' | 'disconnected' | 'testing' | 'error';
  host_masked: string;
  database_name: string;
  last_sync: string;
  tables_count?: number;
}

export interface UserSessionRecord {
  id: string;
  device: string;
  browser: string;
  ip_masked: string;
  location: string;
  is_current: boolean;
  last_active: string;
  created_at: string;
}

export interface ApiKeyRecord {
  id: string;
  name: string;
  prefix: string;
  created_at: string;
  last_used?: string;
  expires_at: string;
  scopes: string[];
}


