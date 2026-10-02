import React, { useState } from 'react';
import { 
  Activity, AlertTriangle, CheckCircle2, TrendingUp, 
  BarChart3, RefreshCw, Zap, ShieldAlert, ArrowRight
} from 'lucide-react';
import { useAuthStore } from '../../services/authStore';

interface DriftFeature {
  name: string;
  type: 'NUMERIC' | 'CATEGORICAL';
  metric: 'PSI' | 'KS_TEST' | 'WASSERSTEIN';
  score: number;
  threshold: number;
  status: 'STABLE' | 'WARNING' | 'DRIFT_DETECTED';
  pVal?: number;
}

const DRIFT_FEATURES: DriftFeature[] = [
  {
    name: 'MonthlyCharges',
    type: 'NUMERIC',
    metric: 'PSI',
    score: 0.042,
    threshold: 0.100,
    status: 'STABLE',
    pVal: 0.842
  },
  {
    name: 'TotalCharges',
    type: 'NUMERIC',
    metric: 'PSI',
    score: 0.068,
    threshold: 0.100,
    status: 'STABLE',
    pVal: 0.412
  },
  {
    name: 'ContractType',
    type: 'CATEGORICAL',
    metric: 'PSI',
    score: 0.142,
    threshold: 0.100,
    status: 'DRIFT_DETECTED',
    pVal: 0.003
  },
  {
    name: 'TenureMonths',
    type: 'NUMERIC',
    metric: 'KS_TEST',
    score: 0.031,
    threshold: 0.050,
    status: 'STABLE',
    pVal: 0.620
  },
  {
    name: 'InternetService',
    type: 'CATEGORICAL',
    metric: 'PSI',
    score: 0.088,
    threshold: 0.100,
    status: 'WARNING',
    pVal: 0.082
  }
];

export const MonitoringDashboard: React.FC = () => {
  const { activeProject } = useAuthStore();
  const [features] = useState(DRIFT_FEATURES);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-2 rounded-lg bg-amber-500/10 text-amber-400">
              <Activity className="w-5 h-5" />
            </span>
            <h1 className="text-2xl font-bold tracking-tight">Data & Model Drift Monitor</h1>
            <span className="badge badge-warning text-xs">1 Drift Detected</span>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Real-time Kolmogorov-Smirnov and Population Stability Index (PSI) drift tracking for <strong className="text-slate-200">{activeProject?.name || 'Customer Churn Prevention'}</strong>
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button className="btn btn-secondary text-xs flex items-center gap-1.5">
            <RefreshCw className="w-3.5 h-3.5" />
            Recompute Baseline PSI
          </button>
          <button className="btn btn-primary text-xs flex items-center gap-1.5">
            <Zap className="w-3.5 h-3.5" />
            Trigger Retraining Job
          </button>
        </div>
      </div>

      {/* KPI Overview Strip */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="panel p-4">
          <div className="text-xs text-slate-400">Overall Feature Drift</div>
          <div className="text-2xl font-bold mt-1 text-amber-400">1 of 18 Features</div>
          <div className="text-xs text-slate-500 mt-1">ContractType exceeded PSI 0.10</div>
        </div>
        <div className="panel p-4">
          <div className="text-xs text-slate-400">Prediction Drift (Kolmogorov)</div>
          <div className="text-2xl font-bold mt-1 text-emerald-400">KS = 0.038</div>
          <div className="text-xs text-emerald-500/80 mt-1">p-value: 0.42 (Distribution stable)</div>
        </div>
        <div className="panel p-4">
          <div className="text-xs text-slate-400">P99 Inference Latency</div>
          <div className="text-2xl font-bold mt-1 text-sky-400">4.8 ms</div>
          <div className="text-xs text-slate-500 mt-1">Over past 10,000 requests</div>
        </div>
        <div className="panel p-4">
          <div className="text-xs text-slate-400">Inference Request Volume</div>
          <div className="text-2xl font-bold mt-1 text-slate-100">1.24k req/min</div>
          <div className="text-xs text-slate-500 mt-1">100% successful executions</div>
        </div>
      </div>

      {/* Drift Detection Table */}
      <div className="panel flex flex-col">
        <div className="p-4 border-b border-border flex items-center justify-between">
          <div className="flex items-center gap-2">
            <BarChart3 className="w-4 h-4 text-primary-light" />
            <span className="text-sm font-bold text-slate-200">Feature Distribution Stability (Baseline vs Production Ingress)</span>
          </div>
          <span className="text-xs text-slate-400">Evaluation Window: Last 7 Days</span>
        </div>

        <div className="overflow-x-auto">
          <table className="data-table">
            <thead>
              <tr>
                <th>Feature Name</th>
                <th>Type</th>
                <th>Statistical Metric</th>
                <th>Score</th>
                <th>Threshold</th>
                <th>Status</th>
                <th>P-Value</th>
              </tr>
            </thead>
            <tbody>
              {features.map((f, i) => (
                <tr key={i}>
                  <td className="font-semibold text-slate-200">{f.name}</td>
                  <td>
                    <span className="badge badge-neutral text-[10px] font-mono">{f.type}</span>
                  </td>
                  <td className="font-mono text-xs text-slate-400">{f.metric}</td>
                  <td className="font-mono font-bold text-slate-200">{f.score.toFixed(3)}</td>
                  <td className="font-mono text-slate-400">{f.threshold.toFixed(3)}</td>
                  <td>
                    {f.status === 'STABLE' ? (
                      <span className="badge badge-success text-xs flex items-center gap-1 w-fit">
                        <CheckCircle2 className="w-3 h-3" /> Stable
                      </span>
                    ) : f.status === 'WARNING' ? (
                      <span className="badge badge-warning text-xs flex items-center gap-1 w-fit">
                        <AlertTriangle className="w-3 h-3" /> Warning
                      </span>
                    ) : (
                      <span className="badge badge-danger text-xs flex items-center gap-1 w-fit">
                        <ShieldAlert className="w-3 h-3" /> Drift Detected
                      </span>
                    )}
                  </td>
                  <td className="font-mono text-xs text-slate-400">{f.pVal ? f.pVal.toFixed(3) : 'N/A'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Retraining Suggestion Banner */}
      <div className="panel p-5 bg-amber-500/5 border-amber-500/20 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-start gap-3">
          <div className="p-2 rounded-lg bg-amber-500/10 text-amber-400 shrink-0">
            <AlertTriangle className="w-5 h-5" />
          </div>
          <div>
            <h4 className="font-bold text-slate-100 text-sm">Automated Retraining Recommendation</h4>
            <p className="text-xs text-slate-300 mt-1 max-w-2xl leading-relaxed">
              Drift detected in <strong>ContractType</strong> (PSI: 0.142 vs threshold 0.100). The ratio of Month-to-Month customers has increased by 14% over baseline training data. An automated retraining job can be scheduled without downtime.
            </p>
          </div>
        </div>
        <button className="btn btn-primary text-xs shrink-0 flex items-center gap-1.5">
          Schedule Retrain Run
          <ArrowRight className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
};
