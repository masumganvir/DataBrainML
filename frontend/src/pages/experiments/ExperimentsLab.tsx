import React, { useState } from 'react';
import { 
  FlaskConical, CheckCircle2, AlertCircle, ArrowUpDown, 
  BarChart3, Eye, Download, Search, RefreshCw, Zap
} from 'lucide-react';
import { useAuthStore } from '../../services/authStore';

interface ModelExperiment {
  id: string;
  name: string;
  framework: string;
  status: 'COMPLETED' | 'TRAINING' | 'FAILED' | 'QUEUED';
  cvScore: number;
  valScore: number;
  testScore: number;
  precision: number;
  recall: number;
  f1: number;
  rocAuc: number;
  trainTimeSec: number;
  inferenceLatencyMs: number;
  modelSizeMb: number;
  isChampion?: boolean;
}

const EXPERIMENT_MODELS: ModelExperiment[] = [
  {
    id: 'exp-xgb-01',
    name: 'XGBoost Baseline Classifier',
    framework: 'XGBoost 2.0.3',
    status: 'COMPLETED',
    cvScore: 0.9412,
    valScore: 0.9430,
    testScore: 0.9482,
    precision: 0.9230,
    recall: 0.8940,
    f1: 0.9082,
    rocAuc: 0.9741,
    trainTimeSec: 24.6,
    inferenceLatencyMs: 4.2,
    modelSizeMb: 12.4,
    isChampion: true,
  },
  {
    id: 'exp-lgb-02',
    name: 'LightGBM Early Stopping',
    framework: 'LightGBM 4.3.0',
    status: 'COMPLETED',
    cvScore: 0.9385,
    valScore: 0.9392,
    testScore: 0.9421,
    precision: 0.9140,
    recall: 0.8870,
    f1: 0.9003,
    rocAuc: 0.9698,
    trainTimeSec: 14.1,
    inferenceLatencyMs: 2.1,
    modelSizeMb: 8.2,
  },
  {
    id: 'exp-cat-03',
    name: 'CatBoost Symmetric Trees',
    framework: 'CatBoost 1.2.5',
    status: 'COMPLETED',
    cvScore: 0.9320,
    valScore: 0.9344,
    testScore: 0.9380,
    precision: 0.9010,
    recall: 0.8750,
    f1: 0.8878,
    rocAuc: 0.9652,
    trainTimeSec: 42.0,
    inferenceLatencyMs: 6.8,
    modelSizeMb: 18.7,
  },
  {
    id: 'exp-rf-04',
    name: 'RandomForest (100 Estimators)',
    framework: 'Scikit-Learn 1.4.1',
    status: 'COMPLETED',
    cvScore: 0.9120,
    valScore: 0.9150,
    testScore: 0.9189,
    precision: 0.8830,
    recall: 0.8410,
    f1: 0.8615,
    rocAuc: 0.9420,
    trainTimeSec: 18.2,
    inferenceLatencyMs: 12.4,
    modelSizeMb: 45.1,
  },
  {
    id: 'exp-mlp-05',
    name: 'Tabular MLP (PyTorch)',
    framework: 'PyTorch 2.2.0',
    status: 'TRAINING',
    cvScore: 0.8940,
    valScore: 0.9010,
    testScore: 0.8980,
    precision: 0.8620,
    recall: 0.8200,
    f1: 0.8405,
    rocAuc: 0.9230,
    trainTimeSec: 110.5,
    inferenceLatencyMs: 8.5,
    modelSizeMb: 3.2,
  }
];

export const ExperimentsLab: React.FC = () => {
  const { activeProject } = useAuthStore();
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedModel, setSelectedModel] = useState<ModelExperiment | null>(EXPERIMENT_MODELS[0]);
  const [sortKey, setSortKey] = useState<keyof ModelExperiment>('f1');
  const [sortAsc, setSortAsc] = useState(false);

  const sortedModels = [...EXPERIMENT_MODELS]
    .filter(m => m.name.toLowerCase().includes(searchTerm.toLowerCase()) || m.framework.toLowerCase().includes(searchTerm.toLowerCase()))
    .sort((a, b) => {
      const valA = a[sortKey] ?? 0;
      const valB = b[sortKey] ?? 0;
      if (typeof valA === 'number' && typeof valB === 'number') {
        return sortAsc ? valA - valB : valB - valA;
      }
      return 0;
    });

  const handleSort = (key: keyof ModelExperiment) => {
    if (sortKey === key) {
      setSortAsc(!sortAsc);
    } else {
      setSortKey(key);
      setSortAsc(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400">
              <FlaskConical className="w-5 h-5" />
            </span>
            <h1 className="text-2xl font-bold tracking-tight">Experiment Lab</h1>
            <span className="badge badge-neutral text-xs">Run: exp-run-20260930-v1</span>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Deterministic AutoML Model Search & Benchmark for <strong className="text-slate-200">{activeProject?.name || 'Customer Churn Prevention'}</strong>
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button className="btn btn-secondary text-xs flex items-center gap-1.5">
            <RefreshCw className="w-3.5 h-3.5" />
            Re-run Benchmark
          </button>
          <button className="btn btn-primary text-xs flex items-center gap-1.5">
            <Zap className="w-3.5 h-3.5" />
            Start Hyperparameter Opt
          </button>
        </div>
      </div>

      {/* KPI Stats Strip */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="panel p-4">
          <div className="text-xs text-slate-400">Evaluated Models</div>
          <div className="text-2xl font-bold mt-1 text-slate-100">5 Candidate Architectures</div>
          <div className="text-xs text-slate-500 mt-1">Stratified 5-Fold Cross Validation</div>
        </div>
        <div className="panel p-4">
          <div className="text-xs text-slate-400">Best Validation F1-Score</div>
          <div className="text-2xl font-bold mt-1 text-emerald-400">0.9082</div>
          <div className="text-xs text-emerald-500/80 mt-1">XGBoost Baseline (+1.4% over LightGBM)</div>
        </div>
        <div className="panel p-4">
          <div className="text-xs text-slate-400">Fastest Inference</div>
          <div className="text-2xl font-bold mt-1 text-sky-400">2.1 ms / query</div>
          <div className="text-xs text-slate-500 mt-1">LightGBM (8.2 MB footprint)</div>
        </div>
        <div className="panel p-4">
          <div className="text-xs text-slate-400">Optimization Budget</div>
          <div className="text-2xl font-bold mt-1 text-slate-100">30 Trials</div>
          <div className="text-xs text-slate-500 mt-1">Optuna Bayesian TPE Engine</div>
        </div>
      </div>

      {/* Main Content: Split Table and Detail Inspector */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Models Table (2 cols) */}
        <div className="lg:col-span-2 panel flex flex-col">
          <div className="p-4 border-b border-border flex items-center justify-between gap-4">
            <div className="relative flex-1 max-w-sm">
              <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
              <input
                type="text"
                placeholder="Filter algorithms or frameworks..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="input pl-9 text-xs py-1.5"
              />
            </div>
            <div className="text-xs text-slate-400">
              Showing {sortedModels.length} candidate models
            </div>
          </div>

          <div className="overflow-x-auto flex-1">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Model</th>
                  <th onClick={() => handleSort('f1')} className="cursor-pointer">
                    <div className="flex items-center gap-1">
                      F1-Score
                      <ArrowUpDown className="w-3 h-3 text-slate-500" />
                    </div>
                  </th>
                  <th onClick={() => handleSort('rocAuc')} className="cursor-pointer">
                    <div className="flex items-center gap-1">
                      ROC-AUC
                      <ArrowUpDown className="w-3 h-3 text-slate-500" />
                    </div>
                  </th>
                  <th onClick={() => handleSort('inferenceLatencyMs')} className="cursor-pointer">
                    <div className="flex items-center gap-1">
                      Latency
                      <ArrowUpDown className="w-3 h-3 text-slate-500" />
                    </div>
                  </th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {sortedModels.map((m) => {
                  const isSelected = selectedModel?.id === m.id;
                  return (
                    <tr 
                      key={m.id}
                      onClick={() => setSelectedModel(m)}
                      className={`cursor-pointer transition-colors ${isSelected ? 'bg-primary/10' : ''}`}
                    >
                      <td>
                        <div className="flex items-center gap-2">
                          {m.isChampion && (
                            <span className="badge badge-success text-[10px] py-0 px-1 font-semibold uppercase">Champion</span>
                          )}
                          <div>
                            <div className="font-semibold text-slate-200">{m.name}</div>
                            <div className="text-[11px] text-slate-400">{m.framework}</div>
                          </div>
                        </div>
                      </td>
                      <td className="font-mono text-emerald-400 font-semibold">{m.f1.toFixed(4)}</td>
                      <td className="font-mono text-sky-400">{m.rocAuc.toFixed(4)}</td>
                      <td className="font-mono text-slate-300">{m.inferenceLatencyMs} ms</td>
                      <td>
                        {m.status === 'COMPLETED' ? (
                          <span className="badge badge-success text-xs flex items-center gap-1">
                            <CheckCircle2 className="w-3 h-3" /> Done
                          </span>
                        ) : (
                          <span className="badge badge-warning text-xs flex items-center gap-1">
                            <RefreshCw className="w-3 h-3 animate-spin" /> Training
                          </span>
                        )}
                      </td>
                      <td>
                        <button 
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedModel(m);
                          }}
                          className="btn btn-secondary text-xs py-1 px-2.5"
                        >
                          <Eye className="w-3.5 h-3.5" />
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* Selected Model Detail Panel (1 col) */}
        <div className="panel p-5 space-y-5">
          {selectedModel ? (
            <>
              <div className="border-b border-border pb-4">
                <div className="flex items-center justify-between">
                  <span className="text-xs uppercase tracking-wider text-slate-400 font-semibold">Model Artifact Spec</span>
                  {selectedModel.isChampion && (
                    <span className="badge badge-success text-xs font-semibold">Active Champion</span>
                  )}
                </div>
                <h3 className="text-lg font-bold text-slate-100 mt-1">{selectedModel.name}</h3>
                <p className="text-xs text-slate-400">{selectedModel.framework} • Run ID: {selectedModel.id}</p>
              </div>

              {/* Metrics Grid */}
              <div className="grid grid-cols-2 gap-3 text-xs">
                <div className="bg-surface-elevated/40 p-3 rounded-lg border border-border">
                  <span className="text-slate-400 block">F1-Score</span>
                  <span className="text-lg font-bold font-mono text-emerald-400">{selectedModel.f1.toFixed(4)}</span>
                </div>
                <div className="bg-surface-elevated/40 p-3 rounded-lg border border-border">
                  <span className="text-slate-400 block">ROC-AUC</span>
                  <span className="text-lg font-bold font-mono text-sky-400">{selectedModel.rocAuc.toFixed(4)}</span>
                </div>
                <div className="bg-surface-elevated/40 p-3 rounded-lg border border-border">
                  <span className="text-slate-400 block">Precision</span>
                  <span className="text-base font-semibold font-mono text-slate-200">{selectedModel.precision.toFixed(4)}</span>
                </div>
                <div className="bg-surface-elevated/40 p-3 rounded-lg border border-border">
                  <span className="text-slate-400 block">Recall</span>
                  <span className="text-base font-semibold font-mono text-slate-200">{selectedModel.recall.toFixed(4)}</span>
                </div>
                <div className="bg-surface-elevated/40 p-3 rounded-lg border border-border">
                  <span className="text-slate-400 block">Training Duration</span>
                  <span className="text-base font-semibold font-mono text-slate-200">{selectedModel.trainTimeSec}s</span>
                </div>
                <div className="bg-surface-elevated/40 p-3 rounded-lg border border-border">
                  <span className="text-slate-400 block">Artifact Size</span>
                  <span className="text-base font-semibold font-mono text-slate-200">{selectedModel.modelSizeMb} MB</span>
                </div>
              </div>

              {/* Hyperparameters preview */}
              <div>
                <span className="text-xs uppercase tracking-wider text-slate-400 font-semibold block mb-2">Tuned Hyperparameters</span>
                <div className="bg-surface-elevated/60 p-3 rounded-lg font-mono text-[11px] text-slate-300 border border-border space-y-1">
                  <div>learning_rate: 0.042</div>
                  <div>max_depth: 6</div>
                  <div>n_estimators: 280</div>
                  <div>subsample: 0.85</div>
                  <div>colsample_bytree: 0.80</div>
                  <div>scale_pos_weight: 3.2 (imbalance adjusted)</div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="pt-2 flex flex-col gap-2">
                <button className="btn btn-primary text-xs w-full flex items-center justify-center gap-1.5 py-2">
                  <BarChart3 className="w-3.5 h-3.5" />
                  View SHAP Feature Importance
                </button>
                <button className="btn btn-secondary text-xs w-full flex items-center justify-center gap-1.5 py-2">
                  <Download className="w-3.5 h-3.5" />
                  Download Model Bundle (.pkl.gz)
                </button>
              </div>
            </>
          ) : (
            <div className="text-center py-12 text-slate-400 text-sm">
              Select a candidate model to inspect metrics and parameters.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
