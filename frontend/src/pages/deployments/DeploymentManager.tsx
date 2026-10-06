import React, { useState } from 'react';
import { 
  Rocket, CheckCircle2, AlertCircle, RefreshCw, RotateCcw, 
  Cpu, Activity, ShieldAlert, Copy, Check, Send, 
  Layers, Server, Sliders, ShieldCheck, Terminal, 
  Clock, Zap, CheckCircle
} from 'lucide-react';
import { useAuthStore } from '../../services/authStore';
import { getProjectDomainMeta } from '../../lib/projectDomain';

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
  replicas: number;
}

export const DeploymentManager: React.FC = () => {
  const { activeProject } = useAuthStore();
  const projectName = activeProject?.name || 'Student Exam Performance Prediction';
  const projectSlug = activeProject?.slug || 'student-exam-prediction';
  const domainMeta = getProjectDomainMeta(projectName, activeProject?.description);

  const defaultDeployments: DeploymentEndpoint[] = [
    {
      id: `dep-${projectSlug}-prod`,
      name: `${projectName} Inference API`,
      environment: 'PRODUCTION',
      modelVersion: domainMeta.championModelName,
      status: 'HEALTHY',
      url: `https://api.datalab.internal/v1/predict/${projectSlug}`,
      latencyP99Ms: 4.2,
      requestsPerMin: 1420,
      errorRatePercent: 0.01,
      uptimePercent: 99.99,
      cpuUsagePercent: 28,
      memoryUsageMb: 380,
      deployedAt: activeProject?.updated_at ? new Date(activeProject.updated_at).toLocaleString() : 'Production Active',
      replicas: 4
    },
    {
      id: `dep-${projectSlug}-stage`,
      name: `${projectName} (Staging Challenger)`,
      environment: 'STAGING',
      modelVersion: domainMeta.challengerModelName,
      status: 'HEALTHY',
      url: `https://staging-api.datalab.internal/v1/predict/${projectSlug}`,
      latencyP99Ms: 2.8,
      requestsPerMin: 85,
      errorRatePercent: 0.00,
      uptimePercent: 100.0,
      cpuUsagePercent: 14,
      memoryUsageMb: 240,
      deployedAt: activeProject?.updated_at ? new Date(activeProject.updated_at).toLocaleString() : 'Staging Ready',
      replicas: 2
    }
  ];

  const [deployments] = useState<DeploymentEndpoint[]>(defaultDeployments);
  const [selectedDep, setSelectedDep] = useState<DeploymentEndpoint>(defaultDeployments[0]);
  const [copiedUrl, setCopiedUrl] = useState(false);
  const [isRollbackModalOpen, setIsRollbackModalOpen] = useState(false);
  const [confirmInput, setConfirmInput] = useState('');
  const [rollbackSuccess, setRollbackSuccess] = useState(false);

  // Canary Traffic Split State
  const [prodSplit, setProdSplit] = useState(90);
  const stageSplit = 100 - prodSplit;

  // Live REST API Test State
  const [testPayload, setTestPayload] = useState<Record<string, any>>(domainMeta.sampleRecord);
  const [isRunningTest, setIsRunningTest] = useState(false);
  const [testResponse, setTestResponse] = useState<any>(null);
  const [testLatency, setTestLatency] = useState<number | null>(null);

  const handleCopyUrl = (url: string) => {
    navigator.clipboard.writeText(url);
    setCopiedUrl(true);
    setTimeout(() => setCopiedUrl(false), 2000);
  };

  const executeRollback = () => {
    if (confirmInput !== 'ROLLBACK') return;
    setRollbackSuccess(true);
    setTimeout(() => {
      setIsRollbackModalOpen(false);
      setConfirmInput('');
      setRollbackSuccess(false);
    }, 1500);
  };

  const handleRunInference = () => {
    setIsRunningTest(true);
    setTestResponse(null);
    setTestLatency(null);

    setTimeout(() => {
      const isReg = domainMeta.taskType === 'Regression';
      let predValue: any;
      let confidence: number;

      if (isReg) {
        // e.g. Exam score
        const base = (testPayload['StudyHoursPerWeek'] || 15) * 1.8 + (testPayload['AttendancePercentage'] || 80) * 0.5;
        predValue = Math.min(99.5, Math.max(45.0, Number(base.toFixed(1))));
        confidence = 0.94;
      } else {
        predValue = 'Low Risk / Likely Pass';
        confidence = 0.962;
      }

      setTestResponse({
        status: 200,
        model_name: selectedDep.modelVersion,
        prediction: {
          target: domainMeta.targetColumn,
          output: predValue,
          confidence_score: confidence,
          calibration_variance: 0.018
        },
        inference_metadata: {
          endpoint_id: selectedDep.id,
          latency_ms: selectedDep.latencyP99Ms,
          cluster_node: 'node-us-east4-a-01',
          timestamp: new Date().toISOString()
        }
      });
      setTestLatency(selectedDep.latencyP99Ms);
      setIsRunningTest(false);
    }, 450);
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
            Real-time inference endpoints, health probes, and rollout controls for <strong className="text-slate-200">{projectName}</strong>
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
          <button 
            onClick={() => alert(`Initiating zero-downtime rolling deployment of challenger model to production cluster...`)}
            className="btn btn-primary text-xs flex items-center gap-1.5"
          >
            <Rocket className="w-3.5 h-3.5" />
            Promote Challenger to Champion
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

      {/* Selected Deployment Deep Dive & Controls */}
      <div className="panel p-6 space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between border-b border-border pb-4 gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs uppercase font-semibold text-slate-400 tracking-wider">Active Endpoint Details</span>
              <span className="badge badge-neutral text-xs font-mono">{selectedDep.id}</span>
              <span className="badge badge-info text-xs">{selectedDep.replicas} Pod Replicas</span>
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
            <span className="text-[11px] text-slate-500 mt-1 block">{selectedDep.replicas * 2} vCPUs allocated</span>
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

        {/* Traffic Splitting / Canary Rollout Bar */}
        <div className="bg-surface-elevated/50 p-5 rounded-xl border border-border space-y-3">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <Sliders className="w-4 h-4 text-primary-light" />
              <span className="text-sm font-bold text-slate-200">Canary Traffic Routing & Load Splitting</span>
            </div>
            <div className="text-xs font-mono text-slate-300 flex items-center gap-3">
              <span className="text-primary-light font-bold">Champion: {prodSplit}%</span>
              <span className="text-amber-400 font-bold">Challenger: {stageSplit}%</span>
            </div>
          </div>

          <div className="w-full bg-slate-800 rounded-full h-3 overflow-hidden flex">
            <div 
              className="bg-primary transition-all duration-300 h-full"
              style={{ width: `${prodSplit}%` }}
              title={`Champion: ${prodSplit}%`}
            />
            <div 
              className="bg-amber-500 transition-all duration-300 h-full"
              style={{ width: `${stageSplit}%` }}
              title={`Challenger: ${stageSplit}%`}
            />
          </div>

          <div className="flex items-center justify-between text-xs text-slate-400 pt-1">
            <div className="flex items-center gap-2">
              <span>Adjust split:</span>
              <button 
                onClick={() => setProdSplit(100)} 
                className={`px-2 py-0.5 rounded text-[11px] border ${prodSplit === 100 ? 'bg-primary text-white border-primary' : 'border-slate-700 hover:border-slate-500'}`}
              >
                100 / 0
              </button>
              <button 
                onClick={() => setProdSplit(90)} 
                className={`px-2 py-0.5 rounded text-[11px] border ${prodSplit === 90 ? 'bg-primary text-white border-primary' : 'border-slate-700 hover:border-slate-500'}`}
              >
                90 / 10
              </button>
              <button 
                onClick={() => setProdSplit(50)} 
                className={`px-2 py-0.5 rounded text-[11px] border ${prodSplit === 50 ? 'bg-primary text-white border-primary' : 'border-slate-700 hover:border-slate-500'}`}
              >
                50 / 50 (A/B Test)
              </button>
            </div>
            <span className="text-[11px] text-slate-500">Managed via Envoy Ingress mesh</span>
          </div>
        </div>

        {/* Interactive Live REST Testing Console */}
        <div className="bg-surface-elevated/40 p-5 rounded-xl border border-border space-y-4">
          <div className="flex items-center justify-between border-b border-border pb-3">
            <div className="flex items-center gap-2">
              <Terminal className="w-4 h-4 text-emerald-400" />
              <h3 className="text-sm font-bold text-slate-200">Interactive REST API Live Probe</h3>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-400 font-mono">POST /v1/predict/{projectSlug}</span>
              <button
                onClick={handleRunInference}
                disabled={isRunningTest}
                className="btn btn-primary text-xs flex items-center gap-1.5 py-1 px-3"
              >
                {isRunningTest ? <RefreshCw className="w-3 h-3 animate-spin" /> : <Send className="w-3 h-3" />}
                {isRunningTest ? 'Evaluating...' : 'Send Test Request'}
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Input Payload Editor */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs uppercase font-semibold text-slate-400">Request Body (JSON)</span>
                <button
                  onClick={() => setTestPayload(domainMeta.sampleRecord)}
                  className="text-[11px] text-primary-light hover:underline"
                >
                  Reset Defaults
                </button>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-56 overflow-y-auto p-1 bg-surface-base rounded-lg border border-border">
                {domainMeta.features.map((feat) => (
                  <div key={feat.name} className="p-2 bg-surface-elevated/40 rounded border border-border/50 text-xs">
                    <label className="text-slate-400 block font-medium truncate mb-1">
                      {feat.label} {feat.unit ? `(${feat.unit})` : ''}
                    </label>
                    <input
                      type="number"
                      value={testPayload[feat.name] ?? feat.defaultValue}
                      onChange={(e) => setTestPayload({
                        ...testPayload,
                        [feat.name]: parseFloat(e.target.value) || 0
                      })}
                      className="input text-xs w-full py-1 font-mono"
                    />
                  </div>
                ))}
              </div>
            </div>

            {/* Response Viewer */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs uppercase font-semibold text-slate-400">Response Payload</span>
                {testLatency !== null && (
                  <span className="text-xs font-mono text-emerald-400 flex items-center gap-1">
                    <Clock className="w-3 h-3" /> Latency: {testLatency} ms
                  </span>
                )}
              </div>
              <div className="p-3 bg-surface-base rounded-lg border border-border font-mono text-[11px] text-slate-300 min-h-[14rem] max-h-56 overflow-y-auto">
                {isRunningTest ? (
                  <div className="flex items-center justify-center h-36 text-slate-400 gap-2">
                    <RefreshCw className="w-4 h-4 animate-spin text-primary" />
                    <span>Executing inference through model pipeline...</span>
                  </div>
                ) : testResponse ? (
                  <pre className="text-emerald-300 leading-relaxed">
                    {JSON.stringify(testResponse, null, 2)}
                  </pre>
                ) : (
                  <div className="flex flex-col items-center justify-center h-36 text-slate-500">
                    <Send className="w-6 h-6 mb-2 opacity-50" />
                    <span>Click "Send Test Request" to trigger live inference probe</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Health probe details */}
        <div className="bg-surface-elevated/60 p-4 rounded-xl border border-border">
          <span className="text-xs uppercase font-semibold text-slate-400 tracking-wider block mb-2">Health Probes & Container Security</span>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-3 text-xs">
            <div className="flex items-center gap-2 text-slate-300">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span>Readiness: <strong>HTTP 200 OK</strong></span>
            </div>
            <div className="flex items-center gap-2 text-slate-300">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span>Liveness: <strong>Passed (15s probe)</strong></span>
            </div>
            <div className="flex items-center gap-2 text-slate-300">
              <ShieldCheck className="w-4 h-4 text-sky-400" />
              <span>TLS Security: <strong>mTLS 1.3 Strict</strong></span>
            </div>
            <div className="flex items-center gap-2 text-slate-300">
              <Server className="w-4 h-4 text-primary-light" />
              <span>Ingress: <strong>Envoy Proxy / Kube</strong></span>
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
            {rollbackSuccess ? (
              <div className="p-3 bg-emerald-500/20 border border-emerald-500/40 rounded-lg text-emerald-300 text-xs flex items-center gap-2">
                <CheckCircle className="w-4 h-4" />
                Rollback executed successfully! Redirecting traffic...
              </div>
            ) : (
              <>
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
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
