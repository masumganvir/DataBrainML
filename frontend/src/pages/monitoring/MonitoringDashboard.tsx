import React, { useState } from 'react';
import { 
  Activity, AlertTriangle, CheckCircle2, TrendingUp, 
  BarChart3, RefreshCw, Zap, ShieldAlert, ArrowRight,
  Sliders, Eye, Check, X
} from 'lucide-react';
import { useAuthStore } from '../../services/authStore';
import { getProjectDomainMeta } from '../../lib/projectDomain';

interface DriftFeature {
  name: string;
  label: string;
  type: 'NUMERIC' | 'CATEGORICAL';
  metric: 'PSI' | 'KS_TEST' | 'WASSERSTEIN';
  score: number;
  threshold: number;
  status: 'STABLE' | 'WARNING' | 'DRIFT_DETECTED';
  pVal?: number;
  baselineMean: number;
  currentMean: number;
}

export const MonitoringDashboard: React.FC = () => {
  const { activeProject } = useAuthStore();
  const projectName = activeProject?.name || 'Student Exam Performance Prediction';
  const domainMeta = getProjectDomainMeta(projectName, activeProject?.description);

  // Dynamically compute features based on project domain
  const dynamicFeatures: DriftFeature[] = domainMeta.features.map((feat, idx) => {
    const isDrift = idx === 1; // Mark second feature as mild drift for realistic alerting
    const score = isDrift ? 0.124 : 0.035 + idx * 0.012;
    const threshold = 0.100;
    return {
      name: feat.name,
      label: feat.label,
      type: feat.type,
      metric: 'PSI',
      score,
      threshold,
      status: isDrift ? 'DRIFT_DETECTED' : score > 0.08 ? 'WARNING' : 'STABLE',
      pVal: isDrift ? 0.008 : 0.42 + idx * 0.1,
      baselineMean: feat.defaultValue,
      currentMean: isDrift ? feat.defaultValue * 1.15 : feat.defaultValue * 0.98
    };
  });

  const [features] = useState<DriftFeature[]>(dynamicFeatures);
  const [selectedFeature, setSelectedFeature] = useState<DriftFeature>(dynamicFeatures[1] || dynamicFeatures[0]);
  const [metricFilter, setMetricFilter] = useState<'ALL' | 'DRIFT'>('ALL');
  const [isRetrainModalOpen, setIsRetrainModalOpen] = useState(false);
  const [retrainTriggered, setRetrainTriggered] = useState(false);

  const filteredFeatures = metricFilter === 'DRIFT'
    ? features.filter(f => f.status === 'DRIFT_DETECTED' || f.status === 'WARNING')
    : features;

  const driftedCount = features.filter(f => f.status === 'DRIFT_DETECTED').length;

  const handleTriggerRetrain = () => {
    setRetrainTriggered(true);
    setTimeout(() => {
      setIsRetrainModalOpen(false);
      setRetrainTriggered(false);
      alert('Autonomous retraining job submitted to Kubernetes queue with updated dataset window.');
    }, 1200);
  };

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
            <span className={`badge ${driftedCount > 0 ? 'badge-warning' : 'badge-success'} text-xs`}>
              {driftedCount > 0 ? `${driftedCount} Drift Detected` : 'All Features Stable'}
            </span>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Real-time Kolmogorov-Smirnov and Population Stability Index (PSI) drift tracking for <strong className="text-slate-200">{projectName}</strong>
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button 
            onClick={() => alert('Recalculating baseline empirical cumulative distribution functions (ECDF)...')}
            className="btn btn-secondary text-xs flex items-center gap-1.5"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Recompute Baseline PSI
          </button>
          <button 
            onClick={() => setIsRetrainModalOpen(true)}
            className="btn btn-primary text-xs flex items-center gap-1.5"
          >
            <Zap className="w-3.5 h-3.5" />
            Trigger Retraining Job
          </button>
        </div>
      </div>

      {/* KPI Overview Strip */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="panel p-4">
          <div className="text-xs text-slate-400">Overall Feature Drift</div>
          <div className="text-2xl font-bold mt-1 text-amber-400">
            {driftedCount} of {features.length} Features
          </div>
          <div className="text-xs text-slate-500 mt-1">
            {selectedFeature.label} exceeded PSI threshold
          </div>
        </div>
        <div className="panel p-4">
          <div className="text-xs text-slate-400">Prediction Distribution (KS)</div>
          <div className="text-2xl font-bold mt-1 text-emerald-400">KS = 0.038</div>
          <div className="text-xs text-emerald-500/80 mt-1">p-value: 0.42 (Output stable)</div>
        </div>
        <div className="panel p-4">
          <div className="text-xs text-slate-400">P99 Inference Latency</div>
          <div className="text-2xl font-bold mt-1 text-sky-400">4.2 ms</div>
          <div className="text-xs text-slate-500 mt-1">Over past 10,000 requests</div>
        </div>
        <div className="panel p-4">
          <div className="text-xs text-slate-400">Inference Request Volume</div>
          <div className="text-2xl font-bold mt-1 text-slate-100">1.42k req/min</div>
          <div className="text-xs text-slate-500 mt-1">100% successful executions</div>
        </div>
      </div>

      {/* Interactive Distribution Comparison Visualizer */}
      <div className="panel p-5 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-border pb-3 gap-2">
          <div className="flex items-center gap-2">
            <BarChart3 className="w-4 h-4 text-primary-light" />
            <h3 className="text-sm font-bold text-slate-200">
              Interactive Distribution Comparator: <span className="text-primary-light">{selectedFeature.label}</span>
            </h3>
          </div>
          <span className="text-xs text-slate-400">
            PSI Score: <strong className="font-mono text-amber-400">{selectedFeature.score.toFixed(3)}</strong> (Threshold: 0.100)
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-1">
          {/* Baseline Training Distribution */}
          <div className="p-4 bg-surface-elevated/40 rounded-xl border border-border">
            <div className="flex items-center justify-between text-xs mb-2">
              <span className="font-bold text-slate-300">Baseline Training Set</span>
              <span className="font-mono text-emerald-400">Mean: {selectedFeature.baselineMean.toFixed(1)}</span>
            </div>
            <div className="h-16 flex items-end gap-2 bg-surface-base p-2 rounded border border-border/60">
              {[30, 45, 75, 90, 70, 40, 20].map((h, i) => (
                <div key={i} className="flex-1 bg-emerald-500/60 rounded-t transition-all" style={{ height: `${h}%` }} />
              ))}
            </div>
            <span className="text-[11px] text-slate-500 block mt-2">Distribution established at training freeze</span>
          </div>

          {/* Current Production Ingress Window */}
          <div className="p-4 bg-surface-elevated/40 rounded-xl border border-border">
            <div className="flex items-center justify-between text-xs mb-2">
              <span className="font-bold text-slate-300">Live Ingress Window (Last 7d)</span>
              <span className="font-mono text-amber-400">Mean: {selectedFeature.currentMean.toFixed(1)}</span>
            </div>
            <div className="h-16 flex items-end gap-2 bg-surface-base p-2 rounded border border-border/60">
              {[15, 30, 60, 75, 95, 60, 45].map((h, i) => (
                <div key={i} className="flex-1 bg-amber-500/70 rounded-t transition-all" style={{ height: `${h}%` }} />
              ))}
            </div>
            <span className="text-[11px] text-amber-400/90 block mt-2">Rightward distribution shift (+15% deviation)</span>
          </div>
        </div>
      </div>

      {/* Drift Detection Table */}
      <div className="panel flex flex-col">
        <div className="p-4 border-b border-border flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <Sliders className="w-4 h-4 text-primary-light" />
            <span className="text-sm font-bold text-slate-200">Feature Distribution Stability (Baseline vs Ingress)</span>
          </div>
          <div className="flex items-center gap-2 text-xs">
            <button 
              onClick={() => setMetricFilter('ALL')}
              className={`filter-btn ${metricFilter === 'ALL' ? 'active' : ''}`}
            >
              All Features ({features.length})
            </button>
            <button 
              onClick={() => setMetricFilter('DRIFT')}
              className={`filter-btn ${metricFilter === 'DRIFT' ? 'active' : ''}`}
            >
              Alerts Only ({driftedCount})
            </button>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="data-table">
            <thead>
              <tr>
                <th>Feature Name</th>
                <th>Type</th>
                <th>Statistical Metric</th>
                <th>PSI Score</th>
                <th>Threshold</th>
                <th>Status</th>
                <th>P-Value</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredFeatures.map((f, i) => {
                const isSelected = selectedFeature.name === f.name;
                return (
                  <tr 
                    key={i}
                    onClick={() => setSelectedFeature(f)}
                    className={`cursor-pointer transition-colors ${isSelected ? 'bg-primary/10' : ''}`}
                  >
                    <td>
                      <div>
                        <div className="font-semibold text-slate-200">{f.label}</div>
                        <div className="text-[11px] font-mono text-slate-400">{f.name}</div>
                      </div>
                    </td>
                    <td>
                      <span className="badge badge-neutral text-[10px] font-mono">{f.type}</span>
                    </td>
                    <td className="font-mono text-xs text-slate-400">{f.metric}</td>
                    <td className={`font-mono font-bold ${f.score > f.threshold ? 'text-amber-400' : 'text-slate-200'}`}>
                      {f.score.toFixed(3)}
                    </td>
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
                    <td>
                      <button 
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedFeature(f);
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

      {/* Retraining Suggestion Banner */}
      <div className="panel p-5 bg-amber-500/5 border-amber-500/20 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-start gap-3">
          <div className="p-2 rounded-lg bg-amber-500/10 text-amber-400 shrink-0">
            <AlertTriangle className="w-5 h-5" />
          </div>
          <div>
            <h4 className="font-bold text-slate-100 text-sm">Automated Retraining Recommendation</h4>
            <p className="text-xs text-slate-300 mt-1 max-w-2xl leading-relaxed">
              Drift detected in <strong>{selectedFeature.label}</strong> (PSI: {selectedFeature.score.toFixed(3)} vs threshold 0.100). The recent ingress distribution has shifted by +15% over baseline data. An automated retraining pipeline run will incorporate these records without downtime.
            </p>
          </div>
        </div>
        <button 
          onClick={() => setIsRetrainModalOpen(true)}
          className="btn btn-primary text-xs shrink-0 flex items-center gap-1.5"
        >
          Schedule Retrain Run
          <ArrowRight className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Retrain Trigger Modal */}
      {isRetrainModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="panel max-w-md w-full p-6 space-y-4 border-amber-500/30">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-amber-400">
                <Zap className="w-5 h-5" />
                <h3 className="text-lg font-bold text-slate-100">Trigger Retraining Pipeline</h3>
              </div>
              <button onClick={() => setIsRetrainModalOpen(false)}>
                <X className="w-4 h-4 text-slate-400" />
              </button>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              This will launch an autonomous pipeline run for <strong>{projectName}</strong> combining the baseline training data with the recent 7-day inference window.
            </p>
            <div className="p-3 bg-surface-elevated rounded border border-border text-xs text-slate-400 space-y-1">
              <div>• Target Metric: {domainMeta.evaluationMetric}</div>
              <div>• Candidate: {domainMeta.championModelName}</div>
              <div>• Expected Training Time: ~45 seconds</div>
            </div>
            <div className="flex items-center justify-end gap-2 pt-2">
              <button 
                onClick={() => setIsRetrainModalOpen(false)}
                className="btn btn-secondary text-xs"
              >
                Cancel
              </button>
              <button 
                onClick={handleTriggerRetrain}
                disabled={retrainTriggered}
                className="btn btn-primary text-xs flex items-center gap-1.5"
              >
                {retrainTriggered ? <RefreshCw className="w-3 h-3 animate-spin" /> : <Zap className="w-3.5 h-3.5" />}
                {retrainTriggered ? 'Launching Agentic DAG...' : 'Confirm & Launch Retrain'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
