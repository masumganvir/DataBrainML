import React, { useState } from 'react';
import { 
  FlaskConical, CheckCircle2, AlertCircle, ArrowUpDown, 
  BarChart3, Eye, Download, Search, RefreshCw, Zap,
  TrendingUp, Award, Layers, Sliders, Check, FileCode,
  Activity, ExternalLink, X
} from 'lucide-react';
import { useAuthStore } from '../../services/authStore';
import { getProjectDomainMeta } from '../../lib/projectDomain';

interface ModelExperiment {
  id: string;
  name: string;
  framework: string;
  status: 'COMPLETED' | 'TRAINING' | 'FAILED' | 'QUEUED';
  cvScore: number;
  valScore: number;
  testScore: number;
  metric1Name: string;
  metric1Val: number;
  metric2Name: string;
  metric2Val: number;
  trainTimeSec: number;
  inferenceLatencyMs: number;
  modelSizeMb: number;
  isChampion?: boolean;
  folds: number[];
  hyperparams: Record<string, any>;
}

interface OptunaTrial {
  trialNumber: number;
  score: number;
  status: 'COMPLETE' | 'PRUNED';
  params: Record<string, number | string>;
}

export const ExperimentsLab: React.FC = () => {
  const { activeProject } = useAuthStore();
  const projectName = activeProject?.name || 'Student Exam Performance Prediction';
  const domainMeta = getProjectDomainMeta(projectName, activeProject?.description);
  const isRegression = domainMeta.taskType === 'Regression';

  const initialModels: ModelExperiment[] = [
    {
      id: 'exp-xgb-01',
      name: `XGBoost ${isRegression ? 'Gradient Regressor' : 'Baseline Classifier'}`,
      framework: 'XGBoost 2.0.3',
      status: 'COMPLETED',
      cvScore: 0.9412,
      valScore: 0.9430,
      testScore: 0.9482,
      metric1Name: isRegression ? 'R² Score' : 'F1-Score',
      metric1Val: isRegression ? 0.9382 : 0.9082,
      metric2Name: isRegression ? 'RMSE' : 'ROC-AUC',
      metric2Val: isRegression ? 3.42 : 0.9741,
      trainTimeSec: 24.6,
      inferenceLatencyMs: 4.2,
      modelSizeMb: 12.4,
      isChampion: true,
      folds: [0.939, 0.944, 0.941, 0.938, 0.944],
      hyperparams: {
        learning_rate: 0.042,
        max_depth: 6,
        n_estimators: 280,
        subsample: 0.85,
        colsample_bytree: 0.80,
        reg_alpha: 0.15
      }
    },
    {
      id: 'exp-lgb-02',
      name: `LightGBM ${isRegression ? 'Fast Tree Regressor' : 'Early Stopping'}`,
      framework: 'LightGBM 4.3.0',
      status: 'COMPLETED',
      cvScore: 0.9385,
      valScore: 0.9392,
      testScore: 0.9421,
      metric1Name: isRegression ? 'R² Score' : 'F1-Score',
      metric1Val: isRegression ? 0.9315 : 0.9003,
      metric2Name: isRegression ? 'RMSE' : 'ROC-AUC',
      metric2Val: isRegression ? 3.65 : 0.9698,
      trainTimeSec: 14.1,
      inferenceLatencyMs: 2.1,
      modelSizeMb: 8.2,
      folds: [0.935, 0.940, 0.938, 0.939, 0.941],
      hyperparams: {
        learning_rate: 0.055,
        num_leaves: 31,
        n_estimators: 220,
        feature_fraction: 0.85
      }
    },
    {
      id: 'exp-cat-03',
      name: `CatBoost Symmetric ${isRegression ? 'Predictor' : 'Classifier'}`,
      framework: 'CatBoost 1.2.5',
      status: 'COMPLETED',
      cvScore: 0.9320,
      valScore: 0.9344,
      testScore: 0.9380,
      metric1Name: isRegression ? 'R² Score' : 'F1-Score',
      metric1Val: isRegression ? 0.9240 : 0.8878,
      metric2Name: isRegression ? 'RMSE' : 'ROC-AUC',
      metric2Val: isRegression ? 3.88 : 0.9652,
      trainTimeSec: 42.0,
      inferenceLatencyMs: 6.8,
      modelSizeMb: 18.7,
      folds: [0.930, 0.932, 0.935, 0.931, 0.932],
      hyperparams: {
        depth: 6,
        iterations: 400,
        l2_leaf_reg: 3.5
      }
    },
    {
      id: 'exp-rf-04',
      name: `RandomForest (150 Estimators)`,
      framework: 'Scikit-Learn 1.4.1',
      status: 'COMPLETED',
      cvScore: 0.9120,
      valScore: 0.9150,
      testScore: 0.9189,
      metric1Name: isRegression ? 'R² Score' : 'F1-Score',
      metric1Val: isRegression ? 0.8980 : 0.8615,
      metric2Name: isRegression ? 'RMSE' : 'ROC-AUC',
      metric2Val: isRegression ? 4.50 : 0.9420,
      trainTimeSec: 18.2,
      inferenceLatencyMs: 12.4,
      modelSizeMb: 45.1,
      folds: [0.910, 0.915, 0.911, 0.913, 0.911],
      hyperparams: {
        n_estimators: 150,
        max_features: 'sqrt',
        min_samples_split: 4
      }
    },
    {
      id: 'exp-mlp-05',
      name: `Tabular Deep MLP (PyTorch)`,
      framework: 'PyTorch 2.2.0',
      status: 'TRAINING',
      cvScore: 0.8940,
      valScore: 0.9010,
      testScore: 0.8980,
      metric1Name: isRegression ? 'R² Score' : 'F1-Score',
      metric1Val: isRegression ? 0.8840 : 0.8405,
      metric2Name: isRegression ? 'RMSE' : 'ROC-AUC',
      metric2Val: isRegression ? 5.12 : 0.9230,
      trainTimeSec: 110.5,
      inferenceLatencyMs: 8.5,
      modelSizeMb: 3.2,
      folds: [0.890, 0.895, 0.894, 0.896, 0.895],
      hyperparams: {
        hidden_layers: [128, 64, 32],
        dropout: 0.2,
        lr: 0.001
      }
    }
  ];

  const optunaTrials: OptunaTrial[] = [
    { trialNumber: 1, score: 0.884, status: 'COMPLETE', params: { lr: 0.01, depth: 4 } },
    { trialNumber: 5, score: 0.902, status: 'COMPLETE', params: { lr: 0.03, depth: 5 } },
    { trialNumber: 12, score: 0.861, status: 'PRUNED', params: { lr: 0.15, depth: 3 } },
    { trialNumber: 19, score: 0.928, status: 'COMPLETE', params: { lr: 0.04, depth: 6 } },
    { trialNumber: 27, score: 0.941, status: 'COMPLETE', params: { lr: 0.042, depth: 6 } },
    { trialNumber: 30, score: 0.939, status: 'COMPLETE', params: { lr: 0.045, depth: 7 } },
  ];

  const [models] = useState<ModelExperiment[]>(initialModels);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedModel, setSelectedModel] = useState<ModelExperiment>(initialModels[0]);
  const [sortKey, setSortKey] = useState<keyof ModelExperiment>('metric1Val');
  const [sortAsc, setSortAsc] = useState(false);
  const [showInspectorModal, setShowInspectorModal] = useState(false);
  const [showOptunaTab, setShowOptunaTab] = useState(false);

  const sortedModels = [...models]
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
            <h1 className="text-2xl font-bold tracking-tight">Experiment Lab & Leaderboard</h1>
            <span className="badge badge-neutral text-xs">Run: exp-run-2026-v1</span>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Deterministic AutoML Model Search & Benchmark for <strong className="text-slate-200">{projectName}</strong>
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button 
            onClick={() => setShowOptunaTab(!showOptunaTab)}
            className="btn btn-secondary text-xs flex items-center gap-1.5"
          >
            <Sliders className="w-3.5 h-3.5" />
            {showOptunaTab ? 'Show Benchmark Leaderboard' : 'View Optuna Bayesian Search'}
          </button>
          <button 
            onClick={() => alert('Triggered Stratified 5-Fold cross-validation hyperparameter sweep with Optuna TPE engine.')}
            className="btn btn-primary text-xs flex items-center gap-1.5"
          >
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
          <div className="text-xs text-slate-400">Best Validation {selectedModel.metric1Name}</div>
          <div className="text-2xl font-bold mt-1 text-emerald-400">
            {models[0].metric1Val.toFixed(4)}
          </div>
          <div className="text-xs text-emerald-500/80 mt-1">
            {models[0].name.split(' ')[0]} Baseline (+1.4% over LightGBM)
          </div>
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

      {/* Visual Model Comparison Bar Chart */}
      <div className="panel p-5 space-y-4">
        <div className="flex items-center justify-between border-b border-border pb-3">
          <div className="flex items-center gap-2">
            <BarChart3 className="w-4 h-4 text-primary-light" />
            <h3 className="text-sm font-bold text-slate-200">
              Interactive Metric Comparison Visualizer ({models[0].metric1Name})
            </h3>
          </div>
          <span className="text-xs text-slate-400">Normalized Cross-Validation Score</span>
        </div>

        <div className="space-y-3 pt-2">
          {models.map((m) => {
            const pct = Math.round((m.metric1Val / 1.0) * 100);
            const isSel = selectedModel.id === m.id;
            return (
              <div 
                key={m.id} 
                onClick={() => setSelectedModel(m)}
                className={`p-2.5 rounded-lg border transition-all cursor-pointer ${
                  isSel ? 'border-primary bg-primary/10' : 'border-border/60 hover:border-slate-600 bg-surface-elevated/20'
                }`}
              >
                <div className="flex items-center justify-between text-xs mb-1.5">
                  <div className="flex items-center gap-2">
                    {m.isChampion && (
                      <span className="badge badge-success text-[10px] py-0 px-1 font-semibold uppercase">Champion</span>
                    )}
                    <span className="font-semibold text-slate-200">{m.name}</span>
                    <span className="text-[11px] text-slate-400">({m.framework})</span>
                  </div>
                  <div className="font-mono text-xs flex items-center gap-3">
                    <span className="text-emerald-400 font-bold">{m.metric1Name}: {m.metric1Val.toFixed(4)}</span>
                    <span className="text-slate-400">{m.inferenceLatencyMs} ms</span>
                  </div>
                </div>

                <div className="w-full bg-slate-800 rounded-full h-2.5 overflow-hidden">
                  <div 
                    className={`h-full rounded-full transition-all duration-500 ${m.isChampion ? 'bg-emerald-400' : 'bg-primary'}`}
                    style={{ width: `${pct}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Main Content: Split Table and Detail Inspector */}
      {showOptunaTab ? (
        /* Optuna Bayesian Tuning View */
        <div className="panel p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-border pb-3">
            <div className="flex items-center gap-2">
              <Sliders className="w-4 h-4 text-amber-400" />
              <h3 className="text-sm font-bold text-slate-200">Optuna Bayesian Hyperparameter Optimization History</h3>
            </div>
            <span className="badge badge-warning text-xs">Tree-structured Parzen Estimator (TPE)</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {optunaTrials.map((t) => (
              <div key={t.trialNumber} className="p-3 bg-surface-elevated/40 rounded-lg border border-border text-xs space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-mono font-bold text-slate-200">Trial #{t.trialNumber}</span>
                  <span className={`badge ${t.status === 'COMPLETE' ? 'badge-success' : 'badge-danger'} text-[10px]`}>
                    {t.status}
                  </span>
                </div>
                <div className="text-slate-400">
                  Validation Score: <strong className="font-mono text-emerald-400">{t.score.toFixed(4)}</strong>
                </div>
                <div className="p-2 bg-surface-base rounded font-mono text-[11px] text-slate-400">
                  {Object.entries(t.params).map(([k, v]) => (
                    <div key={k}>{k}: {v}</div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        /* Standard Benchmark Table + Inspector */
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Models Table (2 cols) */}
          <div className="lg:col-span-2 panel flex flex-col">
            <div className="p-4 border-b border-border flex items-center justify-between gap-4">
              <div className="relative flex-1 max-w-sm">
                <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
                <input
                  type="text"
                  placeholder="Filter candidate models..."
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
                    <th>Model Architecture</th>
                    <th onClick={() => handleSort('metric1Val')} className="cursor-pointer">
                      <div className="flex items-center gap-1">
                        {models[0].metric1Name}
                        <ArrowUpDown className="w-3 h-3 text-slate-500" />
                      </div>
                    </th>
                    <th onClick={() => handleSort('metric2Val')} className="cursor-pointer">
                      <div className="flex items-center gap-1">
                        {models[0].metric2Name}
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
                        <td className="font-mono text-emerald-400 font-semibold">{m.metric1Val.toFixed(4)}</td>
                        <td className="font-mono text-sky-400">{m.metric2Val.toFixed(4)}</td>
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
                              setShowInspectorModal(true);
                            }}
                            className="btn btn-secondary text-xs py-1 px-2.5"
                            title="Inspect Deep Details"
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
                    <span className="text-slate-400 block">{selectedModel.metric1Name}</span>
                    <span className="text-lg font-bold font-mono text-emerald-400">{selectedModel.metric1Val.toFixed(4)}</span>
                  </div>
                  <div className="bg-surface-elevated/40 p-3 rounded-lg border border-border">
                    <span className="text-slate-400 block">{selectedModel.metric2Name}</span>
                    <span className="text-lg font-bold font-mono text-sky-400">{selectedModel.metric2Val.toFixed(4)}</span>
                  </div>
                  <div className="bg-surface-elevated/40 p-3 rounded-lg border border-border">
                    <span className="text-slate-400 block">Cross-Val Mean</span>
                    <span className="text-base font-semibold font-mono text-slate-200">{selectedModel.cvScore.toFixed(4)}</span>
                  </div>
                  <div className="bg-surface-elevated/40 p-3 rounded-lg border border-border">
                    <span className="text-slate-400 block">Inference P99</span>
                    <span className="text-base font-semibold font-mono text-slate-200">{selectedModel.inferenceLatencyMs} ms</span>
                  </div>
                </div>

                {/* 5-Fold Cross Validation breakdown */}
                <div>
                  <span className="text-xs uppercase tracking-wider text-slate-400 font-semibold block mb-2">5-Fold Cross Validation Scores</span>
                  <div className="grid grid-cols-5 gap-1.5 text-center text-xs">
                    {selectedModel.folds.map((f, idx) => (
                      <div key={idx} className="bg-surface-elevated/60 p-2 rounded border border-border font-mono text-[11px]">
                        <span className="text-slate-500 block text-[10px]">F{idx+1}</span>
                        <span className="text-slate-200 font-semibold">{f.toFixed(3)}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Hyperparameters preview */}
                <div>
                  <span className="text-xs uppercase tracking-wider text-slate-400 font-semibold block mb-2">Tuned Hyperparameters</span>
                  <div className="bg-surface-elevated/60 p-3 rounded-lg font-mono text-[11px] text-slate-300 border border-border space-y-1">
                    {Object.entries(selectedModel.hyperparams).map(([k, v]) => (
                      <div key={k}>{k}: <span className="text-sky-300">{JSON.stringify(v)}</span></div>
                    ))}
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="pt-2 flex flex-col gap-2">
                  <button 
                    onClick={() => setShowInspectorModal(true)}
                    className="btn btn-primary text-xs w-full flex items-center justify-center gap-1.5 py-2"
                  >
                    <Eye className="w-3.5 h-3.5" />
                    Open Deep Inspector Modal
                  </button>
                  <button 
                    onClick={() => alert(`Downloaded candidate weights package for ${selectedModel.name}`)}
                    className="btn btn-secondary text-xs w-full flex items-center justify-center gap-1.5 py-2"
                  >
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
      )}

      {/* Deep-Dive Modal */}
      {showInspectorModal && selectedModel && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="panel max-w-2xl w-full p-6 space-y-5 border-border max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-border pb-3">
              <div>
                <span className="text-xs uppercase tracking-wider text-slate-400 font-semibold">Deep Dive Model Inspector</span>
                <h2 className="text-xl font-bold text-slate-100">{selectedModel.name}</h2>
              </div>
              <button 
                onClick={() => setShowInspectorModal(false)}
                className="p-1 rounded-lg hover:bg-surface-elevated text-slate-400 hover:text-slate-200"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
              <div className="bg-surface-elevated/40 p-3 rounded-lg border border-border">
                <span className="text-slate-400 block">{selectedModel.metric1Name}</span>
                <span className="text-lg font-bold font-mono text-emerald-400">{selectedModel.metric1Val.toFixed(4)}</span>
              </div>
              <div className="bg-surface-elevated/40 p-3 rounded-lg border border-border">
                <span className="text-slate-400 block">{selectedModel.metric2Name}</span>
                <span className="text-lg font-bold font-mono text-sky-400">{selectedModel.metric2Val.toFixed(4)}</span>
              </div>
              <div className="bg-surface-elevated/40 p-3 rounded-lg border border-border">
                <span className="text-slate-400 block">Train Time</span>
                <span className="text-lg font-bold font-mono text-slate-200">{selectedModel.trainTimeSec}s</span>
              </div>
              <div className="bg-surface-elevated/40 p-3 rounded-lg border border-border">
                <span className="text-slate-400 block">Disk Footprint</span>
                <span className="text-lg font-bold font-mono text-slate-200">{selectedModel.modelSizeMb} MB</span>
              </div>
            </div>

            <div>
              <h4 className="text-sm font-bold text-slate-200 mb-2">Mathematical Formulation & Loss Function</h4>
              <p className="text-xs text-slate-300 leading-relaxed bg-surface-elevated/30 p-3 rounded-lg border border-border">
                Trained using objective formulation for {domainMeta.domain}. Minimized cross-entropy/squared-error loss across 5 stratified folds with early stopping patience of 25 iterations. Hyperparameters discovered via 30 Optuna TPE iterations.
              </p>
            </div>

            <div>
              <h4 className="text-sm font-bold text-slate-200 mb-2">Complete Parameter Dictionary</h4>
              <div className="p-3 bg-surface-base rounded-lg border border-border font-mono text-xs text-slate-300">
                <pre>{JSON.stringify(selectedModel.hyperparams, null, 2)}</pre>
              </div>
            </div>

            <div className="flex items-center justify-end gap-3 pt-3 border-t border-border">
              <button 
                onClick={() => setShowInspectorModal(false)}
                className="btn btn-secondary text-xs"
              >
                Close Inspector
              </button>
              <button 
                onClick={() => {
                  alert(`Promoted ${selectedModel.name} to Champion!`);
                  setShowInspectorModal(false);
                }}
                className="btn btn-primary text-xs flex items-center gap-1.5"
              >
                <Award className="w-3.5 h-3.5" />
                Set as Active Champion
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
