import React, { useState } from 'react';
import { 
  GitBranch, CheckCircle2, Clock, AlertTriangle, Play, RefreshCw, 
  Terminal, ArrowRight, ShieldCheck, Database, FileText, Cpu, BarChart2, Rocket
} from 'lucide-react';
import { useAuthStore } from '../../services/authStore';

interface PipelineStageNode {
  id: string;
  label: string;
  category: 'INGEST' | 'PROFILE' | 'PREP' | 'TRAIN' | 'DEPLOY';
  agent: string;
  status: 'COMPLETED' | 'RUNNING' | 'WAITING' | 'FAILED';
  durationSec: number;
  summary: string;
  inputs: string[];
  outputs: string[];
  logs: string[];
}

const PIPELINE_NODES: PipelineStageNode[] = [
  {
    id: 'stage-1',
    label: 'Dataset Ingestion & Validation',
    category: 'INGEST',
    agent: 'Dataset Ingestion Agent',
    status: 'COMPLETED',
    durationSec: 1.2,
    summary: 'Loaded 7,043 rows, 21 columns from churn_data_clean.csv. Magic-byte signature verified safe.',
    inputs: ['churn_data_clean.csv (1.2 MB)'],
    outputs: ['Validated In-Memory DataFrame', 'Schema Manifest v1'],
    logs: [
      '[INGEST] File signature check: text/csv verified.',
      '[INGEST] Row count: 7043, Column count: 21.',
      '[INGEST] Zero binary executable payloads detected.',
      '[INGEST] Schema inferred: 16 categorical, 4 numeric, 1 datetime.'
    ]
  },
  {
    id: 'stage-2',
    label: 'Statistical Profiling & Invariant Check',
    category: 'PROFILE',
    agent: 'Dataset Profiler Agent',
    status: 'COMPLETED',
    durationSec: 3.4,
    summary: 'Computed quantile distributions, missingness matrices, and schema types.',
    inputs: ['Validated In-Memory DataFrame'],
    outputs: ['Statistical Profile JSON', 'Distribution Summary'],
    logs: [
      '[PROFILE] Total missing values: 11 (in TotalCharges).',
      '[PROFILE] Target balance: 73.4% Retained, 26.6% Churned.',
      '[PROFILE] Class imbalance flag: MODERATE_IMBALANCE detected.',
      '[PROFILE] Generated correlation heatmap matrix.'
    ]
  },
  {
    id: 'stage-3',
    label: 'Domain-Aware Outlier Detection',
    category: 'PREP',
    agent: 'Outlier Detection Agent',
    status: 'COMPLETED',
    durationSec: 2.1,
    summary: 'Preserved 14 legitimate high-value customers. Flagged 0 corrupt entries.',
    inputs: ['Statistical Profile JSON'],
    outputs: ['Outlier Audit Log', 'Preserved Data Integrity Log'],
    logs: [
      '[OUTLIER] Analyzed MonthlyCharges using IQR & IsolationForest.',
      '[OUTLIER] 14 observations detected in upper 99th percentile ($115-$118.75/mo).',
      '[OUTLIER] Invariant policy: High-value account balance is domain-valid.',
      '[OUTLIER] ZERO rows dropped. Outliers tagged with boolean feature flag.'
    ]
  },
  {
    id: 'stage-4',
    label: 'Deterministic Preprocessing & Encoding',
    category: 'PREP',
    agent: 'Preprocessing Agent',
    status: 'COMPLETED',
    durationSec: 4.8,
    summary: 'Target encoding with K-Fold regularization, median imputation for TotalCharges.',
    inputs: ['Preserved Data Integrity Log'],
    outputs: ['Clean Transformed Matrix (7043, 34)', 'Preprocessing Pipeline Bundle (.joblib)'],
    logs: [
      '[PREPROCESS] Target encoding applied to high-cardinality features.',
      '[PREPROCESS] One-hot encoding applied to low-cardinality nominal features.',
      '[PREPROCESS] RobustScaler fitted on numeric variables.',
      '[PREPROCESS] Preprocessing pipeline serialized with SHA-256 integrity hash.'
    ]
  },
  {
    id: 'stage-5',
    label: 'AutoML Model Benchmark Search',
    category: 'TRAIN',
    agent: 'Model Strategy Agent',
    status: 'COMPLETED',
    durationSec: 112.4,
    summary: 'Evaluated XGBoost, LightGBM, CatBoost, and Random Forest across 5-fold CV.',
    inputs: ['Clean Transformed Matrix'],
    outputs: ['Leaderboard Matrix', 'Candidate Weights (.pkl)'],
    logs: [
      '[AUTOML] Fold 1-5 Stratified split initialized.',
      '[AUTOML] XGBoost 5-fold CV F1: 0.9082.',
      '[AUTOML] LightGBM 5-fold CV F1: 0.9003.',
      '[AUTOML] CatBoost 5-fold CV F1: 0.8878.',
      '[AUTOML] Selection rule: Maximum Validation F1-Score under 10ms latency constraint.'
    ]
  },
  {
    id: 'stage-6',
    label: 'Bayesian Hyperparameter Optimization',
    category: 'TRAIN',
    agent: 'Hyperparameter Tuning Agent',
    status: 'COMPLETED',
    durationSec: 86.2,
    summary: '30 Optuna trials executed. Refined learning rate to 0.042 and depth to 6.',
    inputs: ['Leaderboard Matrix', 'XGBoost Baseline'],
    outputs: ['Optimized Hyperparameters', 'Champion Model Bundle'],
    logs: [
      '[OPTUNA] Initialized TPE sampler with pruning enabled.',
      '[OPTUNA] Trial 14 achieved peak ROC-AUC 0.9741.',
      '[OPTUNA] Parameters serialized to model metadata repository.'
    ]
  },
  {
    id: 'stage-7',
    label: 'SHAP Explainability & Artifact Packaging',
    category: 'TRAIN',
    agent: 'Explainability & Packaging Agent',
    status: 'COMPLETED',
    durationSec: 18.5,
    summary: 'Calculated TreeSHAP values for test holdout set. Generated FastAPI deployment wrapper.',
    inputs: ['Champion Model Bundle'],
    outputs: ['SHAP Summary Matrix', 'FastAPI Container Bundle', 'Jupyter Audit Notebook'],
    logs: [
      '[EXPLAIN] Top feature drivers: ContractType (SHAP +0.42), MonthlyCharges (SHAP +0.31).',
      '[PACKAGE] Generated standalone scoring script with input pydantic schemas.',
      '[PACKAGE] Created verified Docker container definition.'
    ]
  },
  {
    id: 'stage-8',
    label: 'Production Deployment & Gateway Guard',
    category: 'DEPLOY',
    agent: 'Deployment & MLOps Agent',
    status: 'COMPLETED',
    durationSec: 5.6,
    summary: 'Model live on /api/v1/predict/churn-prod-v1 with 99.9% uptime SLA.',
    inputs: ['FastAPI Container Bundle'],
    outputs: ['Live Inference Endpoint', 'Prometheus Metrics Collector'],
    logs: [
      '[DEPLOY] Container churn-prod-v1 deployed to isolated cluster.',
      '[DEPLOY] Readiness probe passed in 420ms.',
      '[DEPLOY] Drift monitoring hook registered with 1-hour aggregation window.'
    ]
  }
];

export const PipelineVisualizer: React.FC = () => {
  const { activeProject } = useAuthStore();
  const [selectedNode, setSelectedNode] = useState<PipelineStageNode>(PIPELINE_NODES[4]);

  const getNodeIcon = (category: PipelineStageNode['category']) => {
    switch (category) {
      case 'INGEST': return <Database className="w-4 h-4" />;
      case 'PROFILE': return <BarChart2 className="w-4 h-4" />;
      case 'PREP': return <FileText className="w-4 h-4" />;
      case 'TRAIN': return <Cpu className="w-4 h-4" />;
      case 'DEPLOY': return <Rocket className="w-4 h-4" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-2 rounded-lg bg-sky-500/10 text-sky-400">
              <GitBranch className="w-5 h-5" />
            </span>
            <h1 className="text-2xl font-bold tracking-tight">Agentic Pipeline DAG</h1>
            <span className="badge badge-success text-xs">Status: COMPLETED (8/8)</span>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Autonomous multi-agent execution pipeline for <strong className="text-slate-200">{activeProject?.name || 'Customer Churn Prevention'}</strong>
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button className="btn btn-secondary text-xs flex items-center gap-1.5">
            <RefreshCw className="w-3.5 h-3.5" />
            Re-run Pipeline
          </button>
          <button className="btn btn-primary text-xs flex items-center gap-1.5">
            <Play className="w-3.5 h-3.5" />
            Run from Selected Node
          </button>
        </div>
      </div>

      {/* Visual Horizontal Timeline / DAG Canvas */}
      <div className="panel p-6 overflow-x-auto">
        <div className="min-w-[950px] flex items-center justify-between relative py-4">
          {/* Connector Line behind nodes */}
          <div className="absolute top-1/2 left-8 right-8 h-0.5 bg-slate-700/60 -translate-y-1/2 z-0" />

          {PIPELINE_NODES.map((node, idx) => {
            const isSelected = selectedNode.id === node.id;
            return (
              <div 
                key={node.id}
                onClick={() => setSelectedNode(node)}
                className="relative z-10 flex flex-col items-center cursor-pointer group"
              >
                {/* Node Orb */}
                <div className={`w-12 h-12 rounded-xl flex items-center justify-center border-2 transition-all duration-200 ${
                  isSelected 
                    ? 'bg-primary text-white border-primary shadow-lg shadow-primary/30 scale-110' 
                    : 'bg-surface-elevated text-slate-300 border-slate-700 hover:border-slate-500 hover:scale-105'
                }`}>
                  {getNodeIcon(node.category)}
                </div>

                {/* Status Indicator */}
                <div className="mt-2 flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                  <span className="text-[11px] font-mono text-slate-400">{node.durationSec}s</span>
                </div>

                {/* Node Label */}
                <span className={`text-xs mt-1 text-center font-medium max-w-[110px] truncate ${
                  isSelected ? 'text-primary-light font-bold' : 'text-slate-300 group-hover:text-slate-100'
                }`}>
                  {node.label.split(' ')[0]} {node.label.split(' ')[1] || ''}
                </span>

                <span className="text-[10px] text-slate-500 text-center max-w-[100px] truncate">
                  Step {idx + 1}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Selected Node Details & Logs View */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Node Metadata (1 col) */}
        <div className="panel p-5 space-y-4">
          <div className="border-b border-border pb-3">
            <span className="text-xs uppercase tracking-wider text-slate-400 font-semibold">Active Node Details</span>
            <h3 className="text-lg font-bold text-slate-100 mt-1">{selectedNode.label}</h3>
            <div className="flex items-center gap-2 mt-2">
              <span className="badge badge-success text-xs flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3" /> {selectedNode.status}
              </span>
              <span className="badge badge-neutral text-xs font-mono">
                Duration: {selectedNode.durationSec}s
              </span>
            </div>
          </div>

          <div>
            <span className="text-xs uppercase tracking-wider text-slate-400 font-semibold block mb-1">Assigned Agent</span>
            <div className="p-2.5 rounded-lg bg-surface-elevated/60 border border-border flex items-center gap-2 text-xs text-slate-200">
              <ShieldCheck className="w-4 h-4 text-primary-light" />
              <span>{selectedNode.agent}</span>
            </div>
          </div>

          <div>
            <span className="text-xs uppercase tracking-wider text-slate-400 font-semibold block mb-1">Execution Summary</span>
            <p className="text-xs text-slate-300 leading-relaxed bg-surface-elevated/40 p-3 rounded-lg border border-border">
              {selectedNode.summary}
            </p>
          </div>

          <div>
            <span className="text-xs uppercase tracking-wider text-slate-400 font-semibold block mb-1">Node Inputs</span>
            <ul className="text-xs text-slate-400 space-y-1">
              {selectedNode.inputs.map((inp, i) => (
                <li key={i} className="flex items-center gap-1.5 font-mono text-[11px]">
                  <ArrowRight className="w-3 h-3 text-slate-600" />
                  {inp}
                </li>
              ))}
            </ul>
          </div>

          <div>
            <span className="text-xs uppercase tracking-wider text-slate-400 font-semibold block mb-1">Node Artifacts & Outputs</span>
            <ul className="text-xs text-slate-400 space-y-1">
              {selectedNode.outputs.map((out, i) => (
                <li key={i} className="flex items-center gap-1.5 font-mono text-[11px] text-emerald-400">
                  <CheckCircle2 className="w-3 h-3 text-emerald-500" />
                  {out}
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Node Safe Execution Terminal Logs (2 cols) */}
        <div className="lg:col-span-2 panel flex flex-col">
          <div className="p-4 border-b border-border flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Terminal className="w-4 h-4 text-emerald-400" />
              <span className="text-xs font-mono font-semibold text-slate-300">Sanitized Agent Execution Log</span>
            </div>
            <span className="text-xs text-slate-500">Zero secrets or raw credentials exposed</span>
          </div>

          <div className="p-4 flex-1 bg-slate-950 font-mono text-xs text-emerald-400/90 overflow-y-auto max-h-[360px] space-y-2 rounded-b-xl border-t border-slate-800">
            <div className="text-slate-600">// Agentic session started with security envelope</div>
            <div className="text-slate-600">// Authorization token validated for project {activeProject?.id || 'demo'}</div>
            {selectedNode.logs.map((log, i) => (
              <div key={i} className="leading-relaxed">
                <span className="text-slate-500 select-none">[{new Date().toISOString().substring(11, 19)}] </span>
                {log}
              </div>
            ))}
            <div className="text-emerald-500/70 font-semibold mt-4">// Node completed deterministically. Verification check passed.</div>
          </div>
        </div>
      </div>
    </div>
  );
};
