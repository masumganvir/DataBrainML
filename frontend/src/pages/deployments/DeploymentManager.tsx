import React, { useState } from 'react';
import { 
  Rocket, CheckCircle2, AlertCircle, RefreshCw, RotateCcw, 
  Power, Cpu, Activity, ShieldAlert, ArrowUpRight, Copy, Check
} from 'lucide-react';
import { useAuthStore } from '../../services/authStore';

interface DeploymentEndpoint {
  id: string;
  name: string;
  environment: 'PRODUCTION' | 'STAGING' | 'DEVELOPMENT';
  modelVersion: string;
  status: 'HEALTHY' | 'DEGRADED' | 'OFFLINE';
  url: string;
  latencyP99Ms: number;
  requestsPerMin: number;
  errorRatePercent: number;
  uptimePercent: number;
  cpuUsagePercent: number;
  memoryUsageMb: number;
  deployedAt: string;
}

const DEPLOYMENTS: DeploymentEndpoint[] = [
  {
    id: 'dep-churn-prod',
    name: 'Customer Churn Predictor API',
    environment: 'PRODUCTION',
    modelVersion: 'v1.4.0 (XGBoost)',
    status: 'HEALTHY',
    url: 'https://api.datalab.internal/v1/predict/churn',
    latencyP99Ms: 4.8,
    requestsPerMin: 1240,
    errorRatePercent: 0.02,
    uptimePercent: 99.98,
    cpuUsagePercent: 24,
    memoryUsageMb: 340,
    deployedAt: '2026-09-30 09:20 UTC'
  },
  {
    id: 'dep-churn-stage',
    name: 'Customer Churn Predictor (Staging)',
    environment: 'STAGING',
    modelVersion: 'v1.3.2 (LightGBM)',
    status: 'HEALTHY',
    url: 'https://staging-api.datalab.internal/v1/predict/churn',
    latencyP99Ms: 3.2,
    requestsPerMin: 45,
    errorRatePercent: 0.00,
    uptimePercent: 100.0,
    cpuUsagePercent: 12,
    memoryUsageMb: 210,
    deployedAt: '2026-09-28 15:10 UTC'
  }
];

export const DeploymentManager: React.FC = () => {
  const { activeProject } = useAuthStore();
  const [deployments, setDeployments] = useState(DEPLOYMENTS);
  const [selectedDep, setSelectedDep] = useState(DEPLOYMENTS[0]);
  const [copiedUrl, setCopiedUrl] = useState(false);
  const [isRollbackModalOpen, setIsRollbackModalOpen] = useState(false);
  const [confirmInput, setConfirmInput] = useState('');

  const handleCopyUrl = (url: string) => {
    navigator.clipboard.writeText(url);
    setCopiedUrl(true);
    setTimeout(() => setCopiedUrl(false), 2000);
  };

  const executeRollback = () => {
    if (confirmInput !== 'ROLLBACK') return;
    alert(`Rollback initiated for ${selectedDep.name} to previous version.`);
    setIsRollbackModalOpen(false);
    setConfirmInput('');
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400">
              <Rocket className="w-5 h-5" />
            </span>
            <h1 className="text-2xl font-bold tracking-tight">Deployments & Endpoints</h1>
            <span className="badge badge-success text-xs">2 Active Clusters</span>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Real-time inference endpoints, health probes, and rollout controls for <strong className="text-slate-200">{activeProject?.name || 'Customer Churn Prevention'}</strong>
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button 
            onClick={() => setIsRollbackModalOpen(true)}
            className="btn btn-secondary text-xs flex items-center gap-1.5 text-rose-400 hover:text-rose-300"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            Rollback Endpoint
          </button>
          <button className="btn btn-primary text-xs flex items-center gap-1.5">
            <Rocket className="w-3.5 h-3.5" />
            Deploy New Challenger
          </button>
        </div>
      </div>

      {/* Deployment List Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {deployments.map((dep) => {
          const isSelected = selectedDep.id === dep.id;
          return (
            <div
              key={dep.id}
              onClick={() => setSelectedDep(dep)}
              className={`panel p-5 cursor-pointer transition-all duration-200 border-2 ${
                isSelected
                  ? 'border-primary bg-surface-elevated/70 shadow-lg shadow-primary/10'
                  : 'border-border/60 hover:border-slate-600 bg-surface/40'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className={`badge text-xs font-semibold ${
                  dep.environment === 'PRODUCTION' ? 'badge-danger' : 'badge-warning'
                }`}>
                  {dep.environment}
                </span>
                <span className="badge badge-success text-xs flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3" /> {dep.status}
                </span>
              </div>

              <h3 className="text-base font-bold text-slate-100 mt-3">{dep.name}</h3>
              <p className="text-xs text-slate-400 mt-0.5">Model: {dep.modelVersion}</p>

              <div className="grid grid-cols-3 gap-2 mt-4 pt-3 border-t border-border/60 text-xs">
                <div>
                  <span className="text-slate-500 block">P99 Latency</span>
                  <span className="font-mono font-semibold text-slate-200">{dep.latencyP99Ms} ms</span>
                </div>
                <div>
                  <span className="text-slate-500 block">Throughput</span>
                  <span className="font-mono font-semibold text-sky-400">{dep.requestsPerMin} req/m</span>
                </div>
                <div>
                  <span className="text-slate-500 block">Uptime</span>
                  <span className="font-mono font-semibold text-emerald-400">{dep.uptimePercent}%</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Selected Deployment Deep Dive */}
      <div className="panel p-6 space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between border-b border-border pb-4 gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs uppercase font-semibold text-slate-400 tracking-wider">Active Endpoint Details</span>
              <span className="badge badge-neutral text-xs font-mono">{selectedDep.id}</span>
            </div>
            <h2 className="text-xl font-bold text-slate-100 mt-1">{selectedDep.name}</h2>
          </div>

          <div className="flex items-center gap-2">
            <button 
              onClick={() => handleCopyUrl(selectedDep.url)}
              className="btn btn-secondary text-xs flex items-center gap-1.5"
            >
              {copiedUrl ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              {copiedUrl ? 'Copied URL!' : 'Copy Inference URL'}
            </button>
          </div>
        </div>

        {/* Live Metrics Row */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-surface-elevated/40 p-4 rounded-xl border border-border">
            <span className="text-xs text-slate-400 flex items-center gap-1.5">
              <Activity className="w-4 h-4 text-sky-400" />
              P99 Latency
            </span>
            <div className="text-2xl font-bold font-mono text-slate-100 mt-1">{selectedDep.latencyP99Ms} ms</div>
            <span className="text-[11px] text-emerald-400 mt-1 block">Well within 50ms SLA</span>
          </div>

          <div className="bg-surface-elevated/40 p-4 rounded-xl border border-border">
            <span className="text-xs text-slate-400 flex items-center gap-1.5">
              <RefreshCw className="w-4 h-4 text-emerald-400" />
              Throughput
            </span>
            <div className="text-2xl font-bold font-mono text-slate-100 mt-1">{selectedDep.requestsPerMin}</div>
            <span className="text-[11px] text-slate-500 mt-1 block">Requests per minute</span>
          </div>

          <div className="bg-surface-elevated/40 p-4 rounded-xl border border-border">
            <span className="text-xs text-slate-400 flex items-center gap-1.5">
              <Cpu className="w-4 h-4 text-amber-400" />
              CPU Utilization
            </span>
            <div className="text-2xl font-bold font-mono text-slate-100 mt-1">{selectedDep.cpuUsagePercent}%</div>
            <span className="text-[11px] text-slate-500 mt-1 block">4 vCPUs allocated</span>
          </div>

          <div className="bg-surface-elevated/40 p-4 rounded-xl border border-border">
            <span className="text-xs text-slate-400 flex items-center gap-1.5">
              <AlertCircle className="w-4 h-4 text-rose-400" />
              Error Rate
            </span>
            <div className="text-2xl font-bold font-mono text-slate-100 mt-1">{selectedDep.errorRatePercent}%</div>
            <span className="text-[11px] text-emerald-400 mt-1 block">0 HTTP 5xx errors</span>
          </div>
        </div>

        {/* Health probe details */}
        <div className="bg-surface-elevated/60 p-4 rounded-xl border border-border">
          <span className="text-xs uppercase font-semibold text-slate-400 tracking-wider block mb-2">Health Probes & Security Guard</span>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
            <div className="flex items-center gap-2 text-slate-300">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span>Readiness Probe: <strong>HTTP 200 OK</strong></span>
            </div>
            <div className="flex items-center gap-2 text-slate-300">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span>Liveness Probe: <strong>Passed (15s interval)</strong></span>
            </div>
            <div className="flex items-center gap-2 text-slate-300">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span>TLS Certificate: <strong>Valid (Let's Encrypt)</strong></span>
            </div>
          </div>
        </div>
      </div>

      {/* Rollback Confirmation Modal */}
      {isRollbackModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="panel max-w-md w-full p-6 space-y-4 border-rose-500/30">
            <div className="flex items-center gap-2 text-rose-400">
              <ShieldAlert className="w-5 h-5" />
              <h3 className="text-lg font-bold text-slate-100">Confirm Production Rollback</h3>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              This action will instantly point the production ingress traffic away from <strong>{selectedDep.modelVersion}</strong> back to the previous stable release.
            </p>
            <div>
              <label className="text-xs text-slate-400 block mb-1">
                Type <strong>ROLLBACK</strong> to proceed:
              </label>
              <input
                type="text"
                value={confirmInput}
                onChange={(e) => setConfirmInput(e.target.value)}
                placeholder="ROLLBACK"
                className="input text-xs w-full"
              />
            </div>
            <div className="flex items-center justify-end gap-2 pt-2">
              <button 
                onClick={() => {
                  setIsRollbackModalOpen(false);
                  setConfirmInput('');
                }}
                className="btn btn-secondary text-xs"
              >
                Cancel
              </button>
              <button 
                onClick={executeRollback}
                disabled={confirmInput !== 'ROLLBACK'}
                className="btn btn-danger text-xs"
              >
                Execute Production Rollback
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
