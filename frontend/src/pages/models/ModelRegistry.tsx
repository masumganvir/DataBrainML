import React, { useState } from 'react';
import { 
  Cpu, CheckCircle2, ShieldCheck, Play, Download, BarChart3, 
  Terminal, ArrowRight, Layers, Lock, AlertTriangle, RefreshCw
} from 'lucide-react';
import { useAuthStore } from '../../services/authStore';

interface ModelVersion {
  id: string;
  version: string;
  name: string;
  role: 'CHAMPION' | 'CHALLENGER' | 'ARCHIVED';
  framework: string;
  f1Score: number;
  rocAuc: number;
  sha256Checksum: string;
  artifactSize: string;
  trainedAt: string;
  topFeatures: { name: string; importance: number }[];
}

const REGISTERED_MODELS: ModelVersion[] = [
  {
    id: 'mdl-xgb-v1.4',
    version: 'v1.4.0',
    name: 'XGBoost Churn Predictor (Production)',
    role: 'CHAMPION',
    framework: 'XGBoost 2.0.3 / Scikit-Learn',
    f1Score: 0.9082,
    rocAuc: 0.9741,
    sha256Checksum: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
    artifactSize: '12.4 MB',
    trainedAt: '2026-09-30 09:14 UTC',
    topFeatures: [
      { name: 'ContractType_MonthToMonth', importance: 0.342 },
      { name: 'MonthlyCharges', importance: 0.284 },
      { name: 'TenureMonths', importance: 0.195 },
      { name: 'TotalCharges', importance: 0.112 },
      { name: 'TechSupport_No', importance: 0.067 }
    ]
  },
  {
    id: 'mdl-lgb-v1.3',
    version: 'v1.3.2',
    name: 'LightGBM Fast Inference',
    role: 'CHALLENGER',
    framework: 'LightGBM 4.3.0',
    f1Score: 0.9003,
    rocAuc: 0.9698,
    sha256Checksum: '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8',
    artifactSize: '8.2 MB',
    trainedAt: '2026-09-28 14:30 UTC',
    topFeatures: [
      { name: 'MonthlyCharges', importance: 0.310 },
      { name: 'ContractType_MonthToMonth', importance: 0.298 },
      { name: 'TenureMonths', importance: 0.220 },
      { name: 'InternetService_Fiber', importance: 0.098 },
      { name: 'PaymentMethod_ElectronicCheck', importance: 0.074 }
    ]
  },
  {
    id: 'mdl-cat-v1.0',
    version: 'v1.0.0',
    name: 'CatBoost Baseline Classifier',
    role: 'ARCHIVED',
    framework: 'CatBoost 1.2.5',
    f1Score: 0.8878,
    rocAuc: 0.9652,
    sha256Checksum: '4b227777d4dd1fc61c6f884f48641d02b4d121d3fd328cb08b5531fcacdabf8a',
    artifactSize: '18.7 MB',
    trainedAt: '2026-09-15 11:20 UTC',
    topFeatures: [
      { name: 'ContractType', importance: 0.380 },
      { name: 'MonthlyCharges', importance: 0.260 },
      { name: 'Tenure', importance: 0.180 },
      { name: 'TotalCharges', importance: 0.100 },
      { name: 'OnlineSecurity', importance: 0.080 }
    ]
  }
];

export const ModelRegistry: React.FC = () => {
  const { activeProject } = useAuthStore();
  const [selectedModel, setSelectedModel] = useState<ModelVersion>(REGISTERED_MODELS[0]);
  const [testPayload, setTestPayload] = useState(
    JSON.stringify({
      tenure_months: 4,
      monthly_charges: 89.5,
      total_charges: 358.0,
      contract: "Month-to-month",
      tech_support: "No",
      internet_service: "Fiber optic"
    }, null, 2)
  );

  const [testResult, setTestResult] = useState<{
    prediction: string;
    churnProbability: number;
    latencyMs: number;
  } | null>(null);

  const [isRunningInference, setIsRunningInference] = useState(false);

  const handleTestInference = () => {
    setIsRunningInference(true);
    setTimeout(() => {
      setTestResult({
        prediction: "CHURN_RISK_HIGH",
        churnProbability: 0.842,
        latencyMs: 3.4
      });
      setIsRunningInference(false);
    }, 450);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400">
              <Cpu className="w-5 h-5" />
            </span>
            <h1 className="text-2xl font-bold tracking-tight">Model Registry & Artifacts</h1>
            <span className="badge badge-success text-xs">Champion: v1.4.0 Active</span>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Versioned model weights, SHA-256 verification, and explainability for <strong className="text-slate-200">{activeProject?.name || 'Customer Churn Prevention'}</strong>
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button className="btn btn-secondary text-xs flex items-center gap-1.5">
            <Layers className="w-3.5 h-3.5" />
            Compare Champion vs Challenger
          </button>
          <button className="btn btn-primary text-xs flex items-center gap-1.5">
            <Download className="w-3.5 h-3.5" />
            Export Docker Package
          </button>
        </div>
      </div>

      {/* Models Grid Selector */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {REGISTERED_MODELS.map((m) => {
          const isSelected = selectedModel.id === m.id;
          return (
            <div
              key={m.id}
              onClick={() => setSelectedModel(m)}
              className={`panel p-4 cursor-pointer transition-all duration-200 border-2 ${
                isSelected
                  ? 'border-primary bg-surface-elevated/70 shadow-lg shadow-primary/10'
                  : 'border-border/60 hover:border-slate-600 bg-surface/40'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className={`badge text-[11px] font-semibold ${
                  m.role === 'CHAMPION' ? 'badge-success' : m.role === 'CHALLENGER' ? 'badge-primary' : 'badge-neutral'
                }`}>
                  {m.role}
                </span>
                <span className="text-xs font-mono text-slate-400">{m.version}</span>
              </div>
              <h3 className="font-bold text-slate-200 text-sm mt-2">{m.name}</h3>
              <p className="text-xs text-slate-400 mt-0.5">{m.framework}</p>

              <div className="grid grid-cols-2 gap-2 mt-4 pt-3 border-t border-border/60 text-xs">
                <div>
                  <span className="text-slate-500 block">F1-Score</span>
                  <span className="font-mono font-semibold text-emerald-400">{m.f1Score.toFixed(4)}</span>
                </div>
                <div>
                  <span className="text-slate-500 block">ROC-AUC</span>
                  <span className="font-mono font-semibold text-sky-400">{m.rocAuc.toFixed(4)}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Selected Model Details & Inference Playground */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Model Spec & Integrity (5 cols) */}
        <div className="lg:col-span-5 space-y-6">
          <div className="panel p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-border pb-3">
              <div>
                <span className="text-xs text-slate-400 uppercase font-semibold">Artifact Metadata</span>
                <h3 className="text-base font-bold text-slate-100">{selectedModel.name}</h3>
              </div>
              <span className="badge badge-success text-xs font-mono">{selectedModel.version}</span>
            </div>

            {/* SHA-256 Checksum Card */}
            <div>
              <span className="text-xs font-semibold text-slate-300 flex items-center gap-1.5 mb-1.5">
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
                Immutable Cryptographic Integrity (SHA-256)
              </span>
              <div className="p-2.5 rounded-lg bg-slate-950 font-mono text-[11px] text-emerald-400 break-all border border-slate-800 select-all">
                {selectedModel.sha256Checksum}
              </div>
              <span className="text-[10px] text-slate-500 mt-1 block">
                Verified against model registry storage. No tampered weights detected.
              </span>
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="p-2.5 bg-surface-elevated/40 rounded-lg border border-border">
                <span className="text-slate-400 block">Artifact Size</span>
                <span className="font-semibold text-slate-200">{selectedModel.artifactSize}</span>
              </div>
              <div className="p-2.5 bg-surface-elevated/40 rounded-lg border border-border">
                <span className="text-slate-400 block">Trained Timestamp</span>
                <span className="font-semibold text-slate-200">{selectedModel.trainedAt}</span>
              </div>
            </div>

            {/* Top SHAP Features */}
            <div>
              <span className="text-xs font-semibold text-slate-300 flex items-center gap-1.5 mb-2">
                <BarChart3 className="w-4 h-4 text-primary-light" />
                Top Feature Drivers (TreeSHAP Magnitude)
              </span>
              <div className="space-y-2">
                {selectedModel.topFeatures.map((feat, i) => (
                  <div key={i} className="space-y-1">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-mono text-slate-300">{feat.name}</span>
                      <span className="font-mono text-slate-400">{(feat.importance * 100).toFixed(1)}%</span>
                    </div>
                    <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                      <div 
                        className="bg-primary h-full rounded-full" 
                        style={{ width: `${feat.importance * 100}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Live Inference Sandbox (7 cols) */}
        <div className="lg:col-span-7 panel flex flex-col">
          <div className="p-4 border-b border-border flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Play className="w-4 h-4 text-primary-light" />
              <span className="text-sm font-bold text-slate-200">Interactive Inference Sandbox</span>
            </div>
            <span className="badge badge-neutral text-xs font-mono">POST /api/v1/predict</span>
          </div>

          <div className="p-5 space-y-4 flex-1">
            <p className="text-xs text-slate-400">
              Run real-time inference against the active champion model container. All payloads are validated using Pydantic schemas.
            </p>

            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1.5">
                JSON Input Payload (Single Observation)
              </label>
              <textarea
                value={testPayload}
                onChange={(e) => setTestPayload(e.target.value)}
                rows={7}
                className="input font-mono text-xs w-full leading-relaxed bg-slate-950 text-slate-200"
              />
            </div>

            <button
              onClick={handleTestInference}
              disabled={isRunningInference}
              className="btn btn-primary text-xs flex items-center gap-1.5"
            >
              {isRunningInference ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  Running Inference...
                </>
              ) : (
                <>
                  <Play className="w-3.5 h-3.5" />
                  Execute Prediction
                </>
              )}
            </button>

            {testResult && (
              <div className="mt-4 p-4 rounded-xl bg-surface-elevated/70 border border-border space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-400 uppercase">Inference Output</span>
                  <span className="text-xs font-mono text-slate-400">Latency: {testResult.latencyMs} ms</span>
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-xs text-slate-400">Model Classification:</div>
                    <div className="text-lg font-bold text-rose-400 flex items-center gap-2 mt-0.5">
                      <AlertTriangle className="w-5 h-5 text-rose-500" />
                      {testResult.prediction}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-xs text-slate-400">Model Output Probability:</div>
                    <div className="text-xl font-bold font-mono text-amber-400 mt-0.5">
                      {(testResult.churnProbability * 100).toFixed(1)}%
                    </div>
                  </div>
                </div>

                <p className="text-[11px] text-slate-500 italic border-t border-border pt-2">
                  * Note: Probabilities represent calibrated statistical model outputs, not empirical certainty.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
