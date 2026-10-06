/**
 * DataWise AI — Extended API Service Layer
 * Adds all new endpoints for Steps 10-19
 */

import axios, { AxiosInstance } from 'axios';
import type { Session, Artifact, Dataset } from '@/types';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// ------------------------------------------------------------------ //
//  Axios Instance
// ------------------------------------------------------------------ //
const apiClient: AxiosInstance = axios.create({
  baseURL: `${BASE_URL}/api`,
  timeout: 120000,
  headers: { 'Content-Type': 'application/json' },
});

apiClient.interceptors.request.use((config) => {
  const token =
    localStorage.getItem('datalab_auth_state') ||
    localStorage.getItem('access_token') ||
    localStorage.getItem('token');
  if (token && !config.headers['Authorization']) {
    config.headers['Authorization'] = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const message =
      error.response?.data?.error?.message ||
      error.response?.data?.message ||
      error.response?.data?.detail ||
      error.message ||
      'An unexpected error occurred';
    return Promise.reject(new Error(message));
  }
);

// ------------------------------------------------------------------ //
//  Sessions API
// ------------------------------------------------------------------ //
export const sessionsApi = {
  list: (): Promise<Session[]> =>
    apiClient.get<Session[]>('/sessions').then((r) => r.data),

  create: (name = 'Untitled Session'): Promise<Session> =>
    apiClient.post<Session>('/sessions', { name }).then((r) => r.data),

  get: (sessionId: string): Promise<Session> =>
    apiClient.get<Session>(`/sessions/${sessionId}`).then((r) => r.data),

  update: (sessionId: string, data: Partial<Pick<Session, 'name' | 'status'>>): Promise<Session> =>
    apiClient.patch<Session>(`/sessions/${sessionId}`, data).then((r) => r.data),

  delete: (sessionId: string): Promise<void> =>
    apiClient.delete(`/sessions/${sessionId}`).then(() => undefined),
};

// ------------------------------------------------------------------ //
//  Datasets API
// ------------------------------------------------------------------ //
export const datasetsApi = {
  upload: (sessionId: string, file: File, onProgress?: (pct: number) => void): Promise<Dataset> => {
    const formData = new FormData();
    formData.append('file', file);
    return apiClient.post(`/sessions/${sessionId}/datasets`, formData, {
      headers: { 'Content-Type': undefined },
      onUploadProgress: (e) => {
        if (onProgress && e.total) {
          onProgress(Math.round((e.loaded * 100) / e.total));
        }
      },
    }).then((r) => r.data);
  },

  list: (sessionId: string): Promise<unknown[]> =>
    apiClient.get(`/sessions/${sessionId}/datasets`).then((r) => r.data),

  preview: (sessionId: string, datasetId: string, limit = 50, offset = 0): Promise<unknown> =>
    apiClient.get(`/sessions/${sessionId}/datasets/${datasetId}/preview`, { params: { limit, offset } }).then((r) => r.data),
};

// ------------------------------------------------------------------ //
//  Analysis API (Steps 3-8)
// ------------------------------------------------------------------ //
export const analysisApi = {
  profile: (sessionId: string): Promise<unknown> =>
    apiClient.post(`/sessions/${sessionId}/profile`).then((r) => r.data),

  quality: (sessionId: string): Promise<unknown> =>
    apiClient.post(`/sessions/${sessionId}/quality`).then((r) => r.data),

  outliers: (sessionId: string): Promise<unknown> =>
    apiClient.post(`/sessions/${sessionId}/outliers`).then((r) => r.data),

  distributions: (sessionId: string): Promise<unknown> =>
    apiClient.post(`/sessions/${sessionId}/distributions`).then((r) => r.data),

  correlations: (sessionId: string): Promise<unknown> =>
    apiClient.post(`/sessions/${sessionId}/correlations`).then((r) => r.data),

  visualize: (sessionId: string, columnName?: string): Promise<unknown> =>
    apiClient.post(`/sessions/${sessionId}/visualize`, { column_name: columnName }).then((r) => r.data),
};

// ------------------------------------------------------------------ //
//  ML Analysis API (Steps 10-16)
// ------------------------------------------------------------------ //
export const mlApi = {
  detectTarget: (sessionId: string): Promise<unknown> =>
    apiClient.get(`/sessions/${sessionId}/target/detect`).then((r) => r.data),

  confirmTarget: (sessionId: string, targetColumn: string, taskType?: string): Promise<unknown> =>
    apiClient.post(`/sessions/${sessionId}/target/confirm`, {
      target_column: targetColumn,
      task_type: taskType,
    }).then((r) => r.data),

  featureEngineeringRecommend: (sessionId: string): Promise<unknown> =>
    apiClient.get(`/sessions/${sessionId}/feature-engineering/recommend`).then((r) => r.data),

  featureEngineeringApply: (sessionId: string, operations: unknown[]): Promise<unknown> =>
    apiClient.post(`/sessions/${sessionId}/feature-engineering/apply`, { operations }).then((r) => r.data),

  featureSelection: (sessionId: string): Promise<unknown> =>
    apiClient.get(`/sessions/${sessionId}/feature-selection`).then((r) => r.data),

  leakage: (sessionId: string): Promise<unknown> =>
    apiClient.get(`/sessions/${sessionId}/leakage`).then((r) => r.data),

  buildPipeline: (sessionId: string): Promise<unknown> =>
    apiClient.get(`/sessions/${sessionId}/pipeline/build`).then((r) => r.data),

  recommend: (sessionId: string, taskType: string, targetColumn?: string): Promise<unknown> =>
    apiClient.post(`/sessions/${sessionId}/ml/recommend`, {
      task_type: taskType,
      target_column: targetColumn,
    }).then((r) => r.data),

  readiness: (sessionId: string): Promise<unknown> =>
    apiClient.get(`/sessions/${sessionId}/ml/readiness`).then((r) => r.data),

  setContext: (
    sessionId: string,
    context: { dataset_domain?: string; prediction_objective?: string; execution_mode?: string }
  ): Promise<{ message: string; session_id: string; dataset_domain?: string; prediction_objective?: string; execution_mode?: string }> =>
    apiClient.post(`/sessions/${sessionId}/context`, context).then((r) => r.data),

  train: (
    sessionId: string,
    params: {
      target_column?: string;
      task_type?: string;
      primary_metric?: string;
      candidate_models?: string[];
      cv_folds?: number;
      test_size?: number;
    }
  ): Promise<any> =>
    apiClient.post(`/sessions/${sessionId}/ml/train`, params).then((r) => r.data),

  getComparison: (sessionId: string): Promise<any> =>
    apiClient.get(`/sessions/${sessionId}/ml/comparison`).then((r) => r.data),

  selectModel: (sessionId: string, modelName: string, rationale?: string): Promise<unknown> =>
    apiClient.post(`/sessions/${sessionId}/ml/select-model`, { model_name: modelName, rationale }).then((r) => r.data),

  generateNotebook: (sessionId: string): Promise<{
    session_id: string;
    notebook_path: string;
    filename: string;
    download_url: string;
    file_size_bytes: number;
    message: string;
  }> =>
    apiClient.post(`/sessions/${sessionId}/notebook/generate`).then((r) => r.data),

  getNotebookDownloadUrl: (sessionId: string): string =>
    `${BASE_URL}/api/sessions/${sessionId}/notebook/download`,

  packageArtifacts: (sessionId: string): Promise<{
    session_id: string;
    bundle_path: string;
    filename: string;
    zip_size_bytes: number;
    download_url: string;
    final_pipeline_path?: string;
    model_metadata_path?: string;
    notebook_path?: string;
    message: string;
  }> =>
    apiClient.post(`/sessions/${sessionId}/artifacts/package`).then((r) => r.data),

  getBundleDownloadUrl: (sessionId: string): string =>
    `${BASE_URL}/api/sessions/${sessionId}/artifacts/download-bundle`,

  getModelDownloadUrl: (sessionId: string): string =>
    `${BASE_URL}/api/sessions/${sessionId}/model/download`,

  getReportHtmlUrl: (sessionId: string): string =>
    `${BASE_URL}/api/sessions/${sessionId}/reports/html`,

  getReportMarkdownUrl: (sessionId: string): string =>
    `${BASE_URL}/api/sessions/${sessionId}/reports/markdown`,
};


// ------------------------------------------------------------------ //
//  Decisions API
// ------------------------------------------------------------------ //
export const decisionsApi = {
  getPending: (sessionId: string): Promise<unknown> =>
    apiClient.get(`/sessions/${sessionId}/decisions/pending`).then((r) => r.data),

  submit: (sessionId: string, decisionKey: string, decisionValue: string, stage?: string): Promise<unknown> =>
    apiClient.post(`/sessions/${sessionId}/decisions`, {
      decision_key: decisionKey,
      decision_value: decisionValue,
      stage: stage || 'HUMAN_APPROVAL',
    }).then((r) => r.data),

  list: (sessionId: string): Promise<unknown[]> =>
    apiClient.get(`/sessions/${sessionId}/decisions`).then((r) => r.data),
};

export interface AgentInfo {
  id: string;
  name: string;
  role: string;
  description: string;
}

// ------------------------------------------------------------------ //
//  Chat API
// ------------------------------------------------------------------ //
export const chatApi = {
  send: (
    sessionId: string,
    message: string,
    agentId?: string
  ): Promise<{ content: string; stage?: string; agent_name?: string; agent_role?: string }> =>
    apiClient.post(`/sessions/${sessionId}/chat`, { message, agent_id: agentId }).then((r) => r.data),

  history: (sessionId: string, limit = 50): Promise<unknown[]> =>
    apiClient.get(`/sessions/${sessionId}/chat/history`, { params: { limit } }).then((r) => r.data),

  getAgents: (sessionId: string): Promise<AgentInfo[]> =>
    apiClient.get(`/sessions/${sessionId}/agents`).then((r) => r.data),
};

// ------------------------------------------------------------------ //
//  Workflow API
// ------------------------------------------------------------------ //
export const workflowApi = {
  run: (sessionId: string): Promise<unknown> =>
    apiClient.post(`/sessions/${sessionId}/workflow/run`).then((r) => r.data),

  status: (sessionId: string): Promise<unknown> =>
    apiClient.get(`/sessions/${sessionId}/workflow/status`).then((r) => r.data),
};

// ------------------------------------------------------------------ //
//  Artifacts API
// ------------------------------------------------------------------ //
export const artifactsApi = {
  list: (sessionId: string): Promise<Artifact[]> =>
    apiClient.get<Artifact[]>(`/sessions/${sessionId}/artifacts`).then((r) => r.data),

  downloadUrl: (artifactId: string): string =>
    `${BASE_URL}/api/artifacts/${artifactId}/download`,
};

// ------------------------------------------------------------------ //
//  Projects & Agentic AutoML API
// ------------------------------------------------------------------ //
export interface ProjectSummary {
  id: string;
  name: string;
  description?: string;
  status: string;
  configuration?: any;
  created_at: string;
  dataset_name?: string;
  dataset_rows?: number;
  dataset_cols?: number;
  best_model?: string;
  metric?: string;
  last_run?: string;
}

export interface RunStatusResponse {
  run_id: string;
  job_id: string;
  project_id: string;
  status: 'QUEUED' | 'RUNNING' | 'PAUSED' | 'COMPLETED' | 'FAILED';
  current_agent: string;
  current_tools: string;
  current_task: string;
  elapsed_seconds: number;
  progress_pct: number;
  timeline: Array<{
    id: string;
    name: string;
    state: 'QUEUED' | 'RUNNING' | 'COMPLETED' | 'WARNING' | 'FAILED' | 'SKIPPED' | 'RETRYING';
    agent: string;
  }>;
  agent_graph: Array<{
    id: string;
    name: string;
    state: 'QUEUED' | 'RUNNING' | 'COMPLETED' | 'WARNING' | 'FAILED';
  }>;
  logs: Array<{
    timestamp: string;
    agent: string;
    message: string;
    type: string;
  }>;
  pending_decision?: {
    decision_id: string;
    category: string;
    title: string;
    message: string;
    explanation?: string;
    recommended_choice: string;
    options: Array<{ value: string; label: string }>;
  } | null;
  dataset_name?: string;
  prompt?: string;
  results?: any;
}

export const projectsApi = {
  list: (): Promise<ProjectSummary[]> =>
    apiClient.get<ProjectSummary[]>('/projects').then((r) => r.data),

  get: (projectId: string): Promise<any> =>
    apiClient.get(`/projects/${projectId}`).then((r) => r.data),

  create: (data: { name: string; description?: string; objective?: string; prompt?: string; configuration?: any }): Promise<any> =>
    apiClient.post('/projects', data).then((r) => r.data),

  update: (projectId: string, data: any): Promise<any> =>
    apiClient.patch(`/projects/${projectId}`, data).then((r) => r.data),

  delete: (projectId: string): Promise<void> =>
    apiClient.delete(`/projects/${projectId}`).then(() => undefined),

  uploadDataset: (projectId: string, file: File, onProgress?: (pct: number) => void): Promise<any> => {
    const formData = new FormData();
    formData.append('file', file);
    return apiClient.post(`/projects/${projectId}/datasets/upload`, formData, {
      headers: { 'Content-Type': undefined },
      onUploadProgress: (e) => {
        if (onProgress && e.total) {
          onProgress(Math.round((e.loaded * 100) / e.total));
        }
      },
    }).then((r) => r.data);
  },

  previewDataset: (projectId: string, params?: { page?: number; page_size?: number; search?: string; sort_col?: string; sort_dir?: string }): Promise<any> =>
    apiClient.get(`/projects/${projectId}/datasets/preview`, { params }).then((r) => r.data),

  startRun: (projectId: string, data: { prompt?: string; configuration?: any }): Promise<{ project_id: string; run_id: string; job_id: string; status: string; target_url: string }> =>
    apiClient.post(`/projects/${projectId}/runs`, data).then((r) => r.data),

  getRunStatus: (projectId: string, runId: string): Promise<RunStatusResponse> =>
    apiClient.get<RunStatusResponse>(`/projects/${projectId}/runs/${runId}`).then((r) => r.data),

  listRuns: (projectId: string): Promise<any[]> =>
    apiClient.get(`/projects/${projectId}/runs`).then((r) => r.data),

  submitDecision: (projectId: string, runId: string, decisionKey: string, decisionValue: string, rationale?: string): Promise<any> =>
    apiClient.post(`/projects/${projectId}/runs/${runId}/decisions`, { decision_key: decisionKey, decision_value: decisionValue, rationale }).then((r) => r.data),

  getResults: (projectId: string, runId: string): Promise<any> =>
    apiClient.get(`/projects/${projectId}/runs/${runId}/results`).then((r) => r.data),

  getArtifactUrl: (projectId: string, runId: string, artifactType: string): string =>
    `${BASE_URL}/api/projects/${projectId}/runs/${runId}/artifacts/${artifactType}`,

  chat: (projectId: string, message: string): Promise<{ role: string; content: string; timestamp: string }> =>
    apiClient.post(`/projects/${projectId}/chat`, { message }).then((r) => r.data),

  deployModel: (projectId: string, modelId: string): Promise<any> =>
    apiClient.post(`/projects/${projectId}/models/${modelId}/deploy`).then((r) => r.data),

  getMonitoring: (projectId: string): Promise<any> =>
    apiClient.get(`/projects/${projectId}/monitoring`).then((r) => r.data),

  getPredictSchema: (projectId: string): Promise<any> =>
    apiClient.get(`/projects/${projectId}/predict/schema`).then((r) => r.data),

  predict: (projectId: string, features: Record<string, any>): Promise<any> =>
    apiClient.post(`/projects/${projectId}/predict`, { features }).then((r) => r.data),

  getNotebook: (projectId: string, runId?: string): Promise<{ project_id: string; run_id: string; filename: string; cells: any[] }> =>
    apiClient.get(`/projects/${projectId}/notebook`, { params: { run_id: runId } }).then((r) => r.data),

  getEDA: (projectId: string, runId?: string): Promise<any> =>
    apiClient.get(`/projects/${projectId}/eda`, { params: { run_id: runId } }).then((r) => r.data),


  proposePlan: (projectId: string, data?: { prompt?: string; custom_name?: string }): Promise<any> =>
    apiClient.post(`/projects/${projectId}/plan/propose`, data || {}).then((r) => r.data),

  approvePlan: (projectId: string, data: any): Promise<any> =>
    apiClient.post(`/projects/${projectId}/plan/approve`, data).then((r) => r.data),

  regeneratePlan: (projectId: string, data?: { prompt?: string; custom_name?: string }): Promise<any> =>
    apiClient.post(`/projects/${projectId}/plan/regenerate`, data || {}).then((r) => r.data),

  clone: (projectId: string): Promise<any> =>
    apiClient.post(`/projects/${projectId}/clone`).then((r) => r.data),

  compareRuns: (projectId: string): Promise<any> =>
    apiClient.get(`/projects/${projectId}/runs/compare`).then((r) => r.data),

  getPrompts: (projectId: string): Promise<any[]> =>
    apiClient.get(`/projects/${projectId}/prompts`).then((r) => r.data),

  addPrompt: (projectId: string, content: string): Promise<any> =>
    apiClient.post(`/projects/${projectId}/prompts`, { content }).then((r) => r.data),

  getImprovements: (): Promise<any> =>
    apiClient.get('/projects/system/improvements').then((r) => r.data),

  runDiagnostics: (): Promise<any> =>
    apiClient.post('/projects/system/diagnostics').then((r) => r.data),

  createWebSocket: (projectId: string, runId: string): WebSocket => {
    const wsUrl = BASE_URL.replace(/^http/, 'ws');
    return new WebSocket(`${wsUrl}/api/projects/${projectId}/runs/${runId}/events`);
  },
};

// ------------------------------------------------------------------ //
//  Health & Auth
// ------------------------------------------------------------------ //
export const healthApi = {
  check: (): Promise<{ status: string; version: string }> =>
    apiClient.get('/health').then((r) => r.data),
};

export const authApi = {
  login: (email: string, password: string): Promise<{ access_token: string; token_type: string; user: any }> =>
    apiClient.post('/auth/login', { email, password }).then((r) => r.data),

  register: (data: { email: string; password: string; name?: string; role?: string }): Promise<{ access_token: string; token_type: string; user: any }> =>
    apiClient.post('/auth/register', data).then((r) => r.data),

  me: (): Promise<any> =>
    apiClient.get('/auth/me').then((r) => r.data),

  logout: (): Promise<any> =>
    apiClient.post('/auth/logout').then((r) => r.data),
};

export { BASE_URL };
export default apiClient;

