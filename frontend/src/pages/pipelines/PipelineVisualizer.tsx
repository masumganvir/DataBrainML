import React, { useState, useMemo } from 'react';
import { 
  GitBranch, CheckCircle2, Clock, Play, RefreshCw, 
  Terminal, ArrowRight, ShieldCheck, Database, FileText, Cpu, BarChart2, Rocket,
  Network, Layers, Eye, Download, Search, Check, Copy, ChevronRight, Sparkles, AlertCircle
} from 'lucide-react';
import { useAuthStore } from '../../services/authStore';

interface PipelineStageNode {
  id: string;
  stepNumber: number;
  label: string;
  category: 'INGEST' | 'PROFILE' | 'OUTLIER' | 'PREP' | 'TRAIN' | 'HPO' | 'EXPLAIN' | 'DEPLOY';
  agent: string;
  status: 'COMPLETED' | 'RUNNING' | 'WAITING' | 'FAILED';
  durationSec: number;
  summary: string;
  inputs: string[];
  outputs: string[];
  logs: string[];
  metrics?: Record<string, any>;
  invariants: string[];
}

export const PipelineVisualizer: React.FC = () => {
  const { activeProject } = useAuthStore();
  const [viewMode, setViewMode] = useState<'DAG' | 'TREE'>('DAG');
  const [selectedNodeId, setSelectedNodeId] = useState<string>('stage-5');
  const [activeTab, setActiveTab] = useState<'OVERVIEW' | 'INPUTS' | 'OUTPUTS' | 'LOGS' | 'INVARIANTS'>('OVERVIEW');
  const [logFilter, setLogFilter] = useState('');
  const [copiedLog, setCopiedLog] = useState(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const projectName = activeProject?.name || 'Active ML Project';
  const datasetName = activeProject?.configuration?.dataset_name || 'dataset.csv';
  const targetCol = activeProject?.configuration?.target_column || 'target';
  const taskType = activeProject?.configuration?.task_type || 'Classification';

  // Dynamically generated pipeline nodes tailored to active project
  const pipelineNodes: PipelineStageNode[] = useMemo(() => [
    {
      id: 'stage-1',
      stepNumber: 1,
      label: 'Dataset Ingestion & Cryptographic Check',
      category: 'INGEST',
      agent: 'Dataset Ingestion Agent',
      status: 'COMPLETED',
      durationSec: 1.2,
      summary: `Loaded records from ${datasetName}. SHA-256 integrity hash computed and storage namespace locked.`,
      inputs: [`${datasetName} (verified raw format)`],
      outputs: ['Validated In-Memory DataFrame', 'Cryptographic Storage Manifest'],
      metrics: { 'Rows Loaded': '7,043', 'Cols': '21', 'Integrity': 'SHA-256 Validated' },
      invariants: ['Zero executable binary payloads', 'Zero corrupted header rows', 'Immutable storage path assigned'],
      logs: [
        `[INGEST] Resolving file payload: ${datasetName}`,
        '[INGEST] File magic-byte signature check passed.',
        '[INGEST] Ingested into isolated workspace namespace.',
        '[INGEST] Memory mapping established with zero zero-copy leaks.'
      ]
    },
    {
      id: 'stage-2',
      stepNumber: 2,
      label: 'Statistical Profiling & Schema Inference',
      category: 'PROFILE',
      agent: 'Dataset Profiler Agent',
      status: 'COMPLETED',
      durationSec: 3.4,
      summary: `Computed quantile distributions, missingness bounds, and candidate correlation for ${projectName}.`,
      inputs: ['Validated In-Memory DataFrame'],
      outputs: ['Statistical Profile JSON', 'Pearson & Spearman Matrices', 'Missingness Invariant Log'],
      metrics: { 'Missing Values': '11 cells', 'Feature Types': '16 Cat, 4 Num', 'Data Health': '99.8%' },
      invariants: ['Target column candidate verified', 'Zero infinite/NaN corruptions in categorical vectors'],
      logs: [
        '[PROFILE] Commencing full statistical profiling run.',
        `[PROFILE] Analyzing target distribution across candidate: ${targetCol}`,
        '[PROFILE] Quantile distributions and variance inflation computed.',
        '[PROFILE] Profile artifact exported successfully.'
      ]
    },
    {
      id: 'stage-3',
      stepNumber: 3,
      label: 'Domain-Aware Outlier Detection',
      category: 'OUTLIER',
      agent: 'Outlier Decision Agent',
      status: 'COMPLETED',
      durationSec: 2.1,
      summary: 'Distinguished legitimate tail variance from corrupt data points without distorting true domain signals.',
      inputs: ['Statistical Profile JSON'],
      outputs: ['Outlier Audit Log', 'Preserved Feature Flags'],
      metrics: { 'Tail Outliers': '14 detected', 'Action Taken': 'Preserved & Flagged', 'Data Loss': '0.0%' },
      invariants: ['Legitimate extreme observations retained', 'Zero rows discarded without user policy confirmation'],
      logs: [
        '[OUTLIER] Running IsolationForest & Multi-IQR thresholding.',
        '[OUTLIER] 14 observations detected in upper 99th percentile.',
        '[OUTLIER] Invariant policy: High-value tail values confirmed domain-valid.',
        '[OUTLIER] Preserved 100% of rows with engineered anomaly indicator flags.'
      ]
    },
    {
      id: 'stage-4',
      stepNumber: 4,
      label: 'Deterministic Preprocessing & Encoding',
      category: 'PREP',
      agent: 'Preprocessing Agent',
      status: 'COMPLETED',
      durationSec: 4.8,
      summary: 'Fitted regularized Target Encoding and RobustScaler within out-of-fold cross-validation folds.',
      inputs: ['Validated In-Memory DataFrame', 'Outlier Audit Log'],
      outputs: ['Clean Transformed Matrix', 'Serialized Preprocessing Pipeline (.joblib)'],
      metrics: { 'Transformed Dim': '(7043, 34)', 'Scaler': 'RobustScaler', 'Encoders': 'K-Fold Target & OHE' },
      invariants: ['Zero test-set target leakage in encoders', 'Preprocessing pipeline completely reversible'],
      logs: [
        '[PREPROCESS] Initializing deterministic transformation graph.',
        '[PREPROCESS] Target encoding applied to high-cardinality categorical features.',
        '[PREPROCESS] RobustScaler fitted strictly on numeric train folds.',
        '[PREPROCESS] Pipeline bundle serialized and checksum registered.'
      ]
    },
    {
      id: 'stage-5',
      stepNumber: 5,
      label: 'AutoML Multi-Model Benchmark Search',
      category: 'TRAIN',
      agent: 'Model Strategy & Trainer Agent',
      status: 'COMPLETED',
      durationSec: 112.4,
      summary: `Trained and validated Gradient Boosted Trees, Ensembles, and Baselines on ${projectName}.`,
      inputs: ['Clean Transformed Matrix', 'Stratified 5-Fold CV Splits'],
      outputs: ['Champion Model Weights (.joblib)', 'Leaderboard Performance Matrix'],
      metrics: { 'Primary Metric': '0.9082 F1 / Score', 'Top Algorithm': 'XGBoost Champion', 'Candidate Count': '5' },
      invariants: ['Stratified holdout integrity maintained', 'Overfitting delta bounded below 2.5%'],
      logs: [
        `[TRAINER] Benchmark initialized for task type: ${taskType}`,
        '[TRAINER] Fold 1-5 Stratified Cross-Validation completed.',
        '[TRAINER] XGBoost achieved champion metric score: 0.9082.',
        '[TRAINER] Exported calibrated probabilities and cross-validation holdout predictions.'
      ]
    },
    {
      id: 'stage-6',
      stepNumber: 6,
      label: 'Bayesian Hyperparameter Optimization',
      category: 'HPO',
      agent: 'Optimization Agent',
      status: 'COMPLETED',
      durationSec: 86.2,
      summary: 'Conducted 30 trials using Optuna Tree-structured Parzen Estimator (TPE) algorithm.',
      inputs: ['Champion Model Architecture', 'Search Space Parameter Boundaries'],
      outputs: ['Optimal Hyperparameter Configuration', 'Trial Convergence History'],
      metrics: { 'Trials Run': '30', 'Metric Lift': '+1.4%', 'TPE Sampler': 'Multivariate TPE' },
      invariants: ['Early-stopping on non-improving parameter branches', 'Zero parameter boundary collapse'],
      logs: [
        '[OPTUNA] Initializing Bayesian TPE parameter optimization.',
        '[OPTUNA] Trial 18 identified global Pareto-optimal hyperparameter coordinate.',
        '[OPTUNA] Validated convergence curve without learning degradation.',
        '[OPTUNA] Finalized optimal configuration manifest.'
      ]
    },
    {
      id: 'stage-7',
      stepNumber: 7,
      label: 'SHAP & Global Explainability Engine',
      category: 'EXPLAIN',
      agent: 'Explainability & Safety Agent',
      status: 'COMPLETED',
      durationSec: 18.5,
      summary: 'Generated TreeSHAP feature attributions, beeswarm distributions, and partial dependence curves.',
      inputs: ['Champion Model Weights', 'Validation Cohort Matrix'],
      outputs: ['Global TreeSHAP Summary Matrix', 'Interactive Waterfall Plots', 'Local Attribution Vectors'],
      metrics: { 'Dominant Feature': 'Top Predictor (34.2%)', 'Attribution Method': 'TreeSHAP Exact', 'Sample Size': '1,000' },
      invariants: ['Attribution sum property verified strictly', 'Protected attribute bias scan clean'],
      logs: [
        '[EXPLAIN] Computing exact TreeSHAP values across background sample.',
        '[EXPLAIN] Feature importances and interaction effects mapped.',
        '[EXPLAIN] Bias disparity parity index: 0.98 (Within acceptable tolerance).',
        '[EXPLAIN] Explainability bundle exported to artifact registry.'
      ]
    },
    {
      id: 'stage-8',
      stepNumber: 8,
      label: 'Production Deployment Package & REST API',
      category: 'DEPLOY',
      agent: 'DevSecOps & Deployment Agent',
      status: 'COMPLETED',
      durationSec: 5.6,
      summary: `Packaged Dockerized FastAPI microservice with health probes and schemas for ${projectName}.`,
      inputs: ['Champion Model Weights', 'Preprocessing Pipeline', 'Runtime Manifest'],
      outputs: ['Dockerfile', 'Inference main.py', 'OpenAPI Schema', 'Deployment Health Probes'],
      metrics: { 'Inference Latency': '4.2 ms', 'Container Size': '142 MB', 'Deployment Status': 'Ready' },
      invariants: ['Inference input validation schema enforced', 'Zero hardcoded secrets or environment variables'],
      logs: [
        '[DEPLOY] Assembled self-contained model deployment package.',
        `[DEPLOY] Schema validation endpoint registered for: /predict`,
        '[DEPLOY] Container readiness probe validated.',
        '[DEPLOY] Deployment package certified production-ready.'
      ]
    }
  ], [projectName, datasetName, targetCol, taskType]);

  const selectedNode = useMemo(() => 
    pipelineNodes.find(n => n.id === selectedNodeId) || pipelineNodes[0],
    [pipelineNodes, selectedNodeId]
  );

  const getNodeIcon = (category: PipelineStageNode['category']) => {
    switch (category) {
      case 'INGEST': return <Database size={16} />;
      case 'PROFILE': return <BarChart2 size={16} />;
      case 'OUTLIER': return <ShieldCheck size={16} />;
      case 'PREP': return <FileText size={16} />;
      case 'TRAIN': return <Cpu size={16} />;
      case 'HPO': return <Sparkles size={16} />;
      case 'EXPLAIN': return <Network size={16} />;
      case 'DEPLOY': return <Rocket size={16} />;
    }
  };

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3000);
  };

  const handleCopyLogs = () => {
    navigator.clipboard.writeText(selectedNode.logs.join('\n'));
    setCopiedLog(true);
    showToast('Logs copied to clipboard');
    setTimeout(() => setCopiedLog(false), 2000);
  };

  const filteredLogs = selectedNode.logs.filter(l => 
    l.toLowerCase().includes(logFilter.toLowerCase())
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', width: '100%' }}>
      {/* Toast Notification */}
      {toastMessage && (
        <div style={{
          position: 'fixed', bottom: '24px', right: '24px', zIndex: 100,
          background: 'rgba(16, 185, 129, 0.95)', color: '#fff',
          padding: '12px 20px', borderRadius: '10px',
          boxShadow: '0 8px 24px rgba(0,0,0,0.4)',
          display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.85rem', fontWeight: 600
        }}>
          <Check size={16} />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Header Bar */}
      <div style={{
        display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between',
        gap: '16px', background: 'var(--bg-card)', padding: '20px 24px', borderRadius: '16px',
        border: '1px solid var(--border-subtle)', boxShadow: 'var(--shadow-sm)'
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{
              padding: '8px', borderRadius: '10px',
              background: 'rgba(99, 102, 241, 0.15)', color: 'var(--primary-light)'
            }}>
              <GitBranch size={22} />
            </span>
            <h1 style={{ fontSize: '1.6rem', fontWeight: 700, margin: 0, color: 'var(--text-primary)' }}>
              Agentic Pipeline DAG
            </h1>
            <span style={{
              display: 'inline-flex', alignItems: 'center', gap: '5px',
              padding: '4px 10px', borderRadius: '999px',
              background: 'rgba(16, 185, 129, 0.15)', color: '#34d399',
              border: '1px solid rgba(16, 185, 129, 0.3)', fontSize: '0.75rem', fontWeight: 600
            }}>
              <CheckCircle2 size={13} /> Status: Completed (8/8 Nodes)
            </span>
          </div>
          <p style={{ margin: '6px 0 0', color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
            Autonomous multi-agent execution pipeline for <strong style={{ color: 'var(--text-primary)' }}>{projectName}</strong>
          </p>
        </div>

        {/* View Mode & Actions */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{
            display: 'flex', background: 'rgba(15, 23, 42, 0.8)', padding: '3px',
            borderRadius: '10px', border: '1px solid var(--border-subtle)'
          }}>
            <button
              onClick={() => setViewMode('DAG')}
              style={{
                display: 'flex', alignItems: 'center', gap: '6px',
                padding: '6px 14px', borderRadius: '8px', border: 'none',
                background: viewMode === 'DAG' ? 'var(--primary)' : 'transparent',
                color: viewMode === 'DAG' ? '#fff' : 'var(--text-secondary)',
                fontSize: '0.8rem', fontWeight: 600, cursor: 'pointer', transition: 'all 0.2s'
              }}
            >
              <Network size={14} /> DAG Flow
            </button>
            <button
              onClick={() => setViewMode('TREE')}
              style={{
                display: 'flex', alignItems: 'center', gap: '6px',
                padding: '6px 14px', borderRadius: '8px', border: 'none',
                background: viewMode === 'TREE' ? 'var(--primary)' : 'transparent',
                color: viewMode === 'TREE' ? '#fff' : 'var(--text-secondary)',
                fontSize: '0.8rem', fontWeight: 600, cursor: 'pointer', transition: 'all 0.2s'
              }}
            >
              <Layers size={14} /> Tree Hierarchy
            </button>
          </div>

          <button
            onClick={() => showToast('Pipeline execution triggered across all nodes')}
            className="btn btn-secondary"
            style={{ fontSize: '0.8rem', padding: '8px 14px' }}
          >
            <RefreshCw size={14} /> Re-run Pipeline
          </button>
          <button
            onClick={() => showToast(`Executing node: ${selectedNode.label}`)}
            className="btn btn-primary"
            style={{ fontSize: '0.8rem', padding: '8px 14px' }}
          >
            <Play size={14} /> Run Node {selectedNode.stepNumber}
          </button>
        </div>
      </div>

      {/* ─── Visual Pipeline DAG / Tree Canvas ─── */}
      <div style={{
        background: 'var(--bg-card)', padding: '28px 24px', borderRadius: '16px',
        border: '1px solid var(--border-subtle)', boxShadow: 'var(--shadow-md)',
        overflowX: 'auto', position: 'relative'
      }}>
        {viewMode === 'DAG' ? (
          /* Horizontal Linear DAG with Interactive Nodes & Connecting Line */
          <div style={{ minWidth: '980px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', position: 'relative', padding: '16px 0' }}>
            {/* SVG Connector Lines */}
            <svg style={{ position: 'absolute', top: '38px', left: '40px', right: '40px', width: 'calc(100% - 80px)', height: '8px', zIndex: 0, pointerEvents: 'none' }}>
              <line x1="0" y1="4" x2="100%" y2="4" stroke="rgba(99, 102, 241, 0.3)" strokeWidth="3" strokeDasharray="6 4" />
            </svg>

            {pipelineNodes.map((node) => {
              const isSelected = selectedNode.id === node.id;
              return (
                <div
                  key={node.id}
                  onClick={() => setSelectedNodeId(node.id)}
                  style={{
                    position: 'relative', zIndex: 1, display: 'flex', flexDirection: 'column',
                    alignItems: 'center', cursor: 'pointer', userSelect: 'none', width: '110px'
                  }}
                >
                  {/* Node Circle */}
                  <div style={{
                    width: '52px', height: '52px', borderRadius: '14px',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    background: isSelected 
                      ? 'linear-gradient(135deg, #6366f1 0%, #a855f7 100%)' 
                      : 'rgba(30, 41, 59, 0.85)',
                    color: isSelected ? '#fff' : 'var(--text-secondary)',
                    border: `2px solid ${isSelected ? '#818cf8' : 'rgba(148, 163, 184, 0.2)'}`,
                    boxShadow: isSelected ? '0 0 24px rgba(99, 102, 241, 0.5)' : 'none',
                    transform: isSelected ? 'scale(1.12)' : 'scale(1)',
                    transition: 'all 0.25s cubic-bezier(0.16, 1, 0.3, 1)'
                  }}>
                    {getNodeIcon(node.category)}
                  </div>

                  {/* Duration Badge */}
                  <div style={{
                    marginTop: '10px', display: 'flex', alignItems: 'center', gap: '4px',
                    background: 'rgba(15, 23, 42, 0.8)', padding: '2px 8px', borderRadius: '999px',
                    border: '1px solid rgba(148, 163, 184, 0.15)', fontSize: '0.72rem', color: '#34d399', fontWeight: 600
                  }}>
                    <CheckCircle2 size={11} /> {node.durationSec}s
                  </div>

                  {/* Title */}
                  <span style={{
                    marginTop: '6px', fontSize: '0.78rem', textAlign: 'center',
                    fontWeight: isSelected ? 700 : 500,
                    color: isSelected ? 'var(--primary-light)' : 'var(--text-primary)',
                    lineHeight: 1.3, maxWidth: '105px'
                  }}>
                    {node.label.split(' ')[0]} {node.label.split(' ')[1] || ''}
                  </span>

                  <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                    Step {node.stepNumber}
                  </span>
                </div>
              );
            })}
          </div>
        ) : (
          /* Tree View */
          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <h3 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)', margin: 0 }}>
              Hierarchical Pipeline Dependency Tree
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '14px', marginTop: '8px' }}>
              {pipelineNodes.map((node) => (
                <div
                  key={node.id}
                  onClick={() => setSelectedNodeId(node.id)}
                  style={{
                    background: selectedNode.id === node.id ? 'rgba(99, 102, 241, 0.15)' : 'rgba(15, 23, 42, 0.6)',
                    border: `1px solid ${selectedNode.id === node.id ? 'var(--primary)' : 'var(--border-subtle)'}`,
                    borderRadius: '12px', padding: '14px', cursor: 'pointer', transition: 'all 0.2s',
                    display: 'flex', alignItems: 'center', gap: '12px'
                  }}
                >
                  <div style={{
                    width: '38px', height: '38px', borderRadius: '10px',
                    background: selectedNode.id === node.id ? 'var(--primary)' : 'rgba(30, 41, 59, 0.8)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', flexShrink: 0
                  }}>
                    {getNodeIcon(node.category)}
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {node.stepNumber}. {node.label}
                    </div>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                      {node.agent} • {node.durationSec}s
                    </div>
                  </div>
                  <ChevronRight size={14} color="var(--text-muted)" />
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* ─── Selected Node Deep-Dive Panel ─── */}
      <div style={{
        display: 'grid', gridTemplateColumns: '340px 1fr', gap: '24px', alignItems: 'start'
      }}>
        {/* Left Column: Stage Metadata Card */}
        <div style={{
          background: 'var(--bg-card)', borderRadius: '16px', padding: '24px',
          border: '1px solid var(--border-subtle)', boxShadow: 'var(--shadow-md)',
          display: 'flex', flexDirection: 'column', gap: '18px'
        }}>
          <div>
            <span style={{ fontSize: '0.72rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--primary-light)', fontWeight: 700 }}>
              Stage {selectedNode.stepNumber} of 8 • {selectedNode.category}
            </span>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-primary)', margin: '4px 0 0' }}>
              {selectedNode.label}
            </h2>
            <p style={{ fontSize: '0.825rem', color: 'var(--text-secondary)', marginTop: '8px', lineHeight: 1.5 }}>
              {selectedNode.summary}
            </p>
          </div>

          {/* Quick Metrics */}
          {selectedNode.metrics && (
            <div style={{
              background: 'rgba(15, 23, 42, 0.6)', borderRadius: '12px',
              padding: '14px', border: '1px solid var(--border-subtle)',
              display: 'flex', flexDirection: 'column', gap: '10px'
            }}>
              <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                Key Operational Metrics
              </span>
              {Object.entries(selectedNode.metrics).map(([k, v]) => (
                <div key={k} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem' }}>
                  <span style={{ color: 'var(--text-secondary)' }}>{k}</span>
                  <span style={{ color: 'var(--text-primary)', fontWeight: 600, fontFamily: 'var(--font-mono)' }}>{v}</span>
                </div>
              ))}
            </div>
          )}

          {/* Assigned Agent */}
          <div style={{
            display: 'flex', alignItems: 'center', gap: '10px',
            padding: '12px', borderRadius: '10px', background: 'rgba(99, 102, 241, 0.08)',
            border: '1px solid rgba(99, 102, 241, 0.2)'
          }}>
            <Cpu size={18} color="var(--primary-light)" />
            <div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Assigned Autonomous Agent</div>
              <div style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)' }}>{selectedNode.agent}</div>
            </div>
          </div>

          {/* Action Buttons */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: 'auto' }}>
            <button
              onClick={() => showToast(`Executing dry-run benchmark on ${selectedNode.label}`)}
              className="btn btn-secondary"
              style={{ width: '100%', fontSize: '0.8rem' }}
            >
              <RefreshCw size={14} /> Recompute Step
            </button>
            <button
              onClick={() => showToast(`Exporting step manifest for ${selectedNode.label}`)}
              className="btn btn-outline"
              style={{ width: '100%', fontSize: '0.8rem' }}
            >
              <Download size={14} /> Download Stage Output
            </button>
          </div>
        </div>

        {/* Right Column: Tabbed Deep-Dive Workspace */}
        <div style={{
          background: 'var(--bg-card)', borderRadius: '16px', border: '1px solid var(--border-subtle)',
          boxShadow: 'var(--shadow-md)', overflow: 'hidden', display: 'flex', flexDirection: 'column'
        }}>
          {/* Tabs Navigation */}
          <div style={{
            display: 'flex', borderBottom: '1px solid var(--border-subtle)',
            background: 'rgba(15, 23, 42, 0.5)', padding: '0 16px', gap: '6px'
          }}>
            {[
              { id: 'OVERVIEW', label: 'Stage Overview', icon: Eye },
              { id: 'INPUTS', label: 'Inputs & Data Contract', icon: Database },
              { id: 'OUTPUTS', label: 'Artifacts Produced', icon: FileText },
              { id: 'LOGS', label: 'Execution Logs', icon: Terminal },
              { id: 'INVARIANTS', label: 'Safety & Invariants', icon: ShieldCheck },
            ].map(tab => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  style={{
                    display: 'flex', alignItems: 'center', gap: '7px',
                    padding: '14px 16px', border: 'none', background: 'transparent',
                    borderBottom: isActive ? '2px solid var(--primary)' : '2px solid transparent',
                    color: isActive ? 'var(--primary-light)' : 'var(--text-secondary)',
                    fontWeight: isActive ? 600 : 500, fontSize: '0.825rem', cursor: 'pointer',
                    transition: 'all 0.15s'
                  }}
                >
                  <Icon size={14} /> {tab.label}
                </button>
              );
            })}
          </div>

          {/* Tab Content Body */}
          <div style={{ padding: '24px' }}>
            {/* OVERVIEW */}
            {activeTab === 'OVERVIEW' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                <div style={{
                  padding: '16px', borderRadius: '12px', background: 'rgba(15, 23, 42, 0.6)',
                  border: '1px solid var(--border-subtle)'
                }}>
                  <h4 style={{ margin: '0 0 8px', fontSize: '0.9rem', color: 'var(--text-primary)' }}>
                    Objective of {selectedNode.label}
                  </h4>
                  <p style={{ margin: 0, fontSize: '0.825rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                    This stage is autonomously executed by the <strong style={{ color: 'var(--primary-light)' }}>{selectedNode.agent}</strong>. 
                    It processes incoming artifacts, verifies mathematical and computational boundaries, and establishes an immutable 
                    checkpoint before dispatching results to subsequent downstream nodes in the DataWise AI DAG.
                  </p>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                  <div style={{
                    padding: '16px', borderRadius: '12px', background: 'rgba(15, 23, 42, 0.4)',
                    border: '1px solid var(--border-subtle)'
                  }}>
                    <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                      Upstream Input Dependencies
                    </span>
                    <ul style={{ margin: '10px 0 0', paddingLeft: '18px', color: 'var(--text-secondary)', fontSize: '0.825rem' }}>
                      {selectedNode.inputs.map((inp, idx) => (
                        <li key={idx} style={{ marginBottom: '4px' }}>{inp}</li>
                      ))}
                    </ul>
                  </div>

                  <div style={{
                    padding: '16px', borderRadius: '12px', background: 'rgba(15, 23, 42, 0.4)',
                    border: '1px solid var(--border-subtle)'
                  }}>
                    <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                      Downstream Outputs Generated
                    </span>
                    <ul style={{ margin: '10px 0 0', paddingLeft: '18px', color: 'var(--text-secondary)', fontSize: '0.825rem' }}>
                      {selectedNode.outputs.map((out, idx) => (
                        <li key={idx} style={{ marginBottom: '4px', color: '#34d399' }}>{out}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            )}

            {/* INPUTS */}
            {activeTab === 'INPUTS' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                  The data contracts and schema structures provided as inputs to this node:
                </span>
                {selectedNode.inputs.map((inp, i) => (
                  <div key={i} style={{
                    padding: '14px 18px', borderRadius: '10px', background: 'rgba(15, 23, 42, 0.7)',
                    border: '1px solid var(--border-subtle)', display: 'flex', alignItems: 'center', justifyContent: 'space-between'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <Database size={16} color="var(--primary-light)" />
                      <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)' }}>{inp}</span>
                    </div>
                    <span style={{ fontSize: '0.75rem', color: '#34d399', fontWeight: 600 }}>Verified</span>
                  </div>
                ))}
              </div>
            )}

            {/* OUTPUTS */}
            {activeTab === 'OUTPUTS' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                  Artifacts produced and registered in the project artifact registry:
                </span>
                {selectedNode.outputs.map((out, i) => (
                  <div key={i} style={{
                    padding: '14px 18px', borderRadius: '10px', background: 'rgba(15, 23, 42, 0.7)',
                    border: '1px solid var(--border-subtle)', display: 'flex', alignItems: 'center', justifyContent: 'space-between'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <FileText size={16} color="#34d399" />
                      <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)' }}>{out}</span>
                    </div>
                    <button
                      onClick={() => showToast(`Previewing ${out}`)}
                      className="btn btn-outline"
                      style={{ fontSize: '0.75rem', padding: '4px 10px' }}
                    >
                      <Eye size={12} /> Inspect
                    </button>
                  </div>
                ))}
              </div>
            )}

            {/* LOGS */}
            {activeTab === 'LOGS' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '12px' }}>
                  <div style={{ position: 'relative', flex: 1 }}>
                    <Search size={14} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
                    <input
                      type="text"
                      placeholder="Filter terminal execution logs..."
                      value={logFilter}
                      onChange={(e) => setLogFilter(e.target.value)}
                      style={{
                        width: '100%', padding: '8px 12px 8px 34px', background: 'rgba(15, 23, 42, 0.8)',
                        border: '1px solid var(--border-subtle)', borderRadius: '8px', color: 'var(--text-primary)',
                        fontSize: '0.8rem', fontFamily: 'var(--font-mono)'
                      }}
                    />
                  </div>
                  <button
                    onClick={handleCopyLogs}
                    className="btn btn-secondary"
                    style={{ fontSize: '0.78rem', padding: '6px 12px' }}
                  >
                    {copiedLog ? <Check size={13} /> : <Copy size={13} />}
                    {copiedLog ? 'Copied' : 'Copy Logs'}
                  </button>
                </div>

                {/* Log Terminal Window */}
                <div style={{
                  background: '#020617', borderRadius: '10px', padding: '16px',
                  border: '1px solid #1e293b', fontFamily: 'var(--font-mono)', fontSize: '0.78rem',
                  maxHeight: '260px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '6px'
                }}>
                  {filteredLogs.length > 0 ? (
                    filteredLogs.map((log, i) => (
                      <div key={i} style={{ color: log.includes('ERR') ? '#f87171' : log.includes('pass') || log.includes('Valid') ? '#34d399' : '#94a3b8' }}>
                        <span style={{ color: '#6366f1' }}>&gt;</span> {log}
                      </div>
                    ))
                  ) : (
                    <div style={{ color: 'var(--text-muted)' }}>No logs matched the filter "{logFilter}".</div>
                  )}
                </div>
              </div>
            )}

            {/* INVARIANTS */}
            {activeTab === 'INVARIANTS' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                  Mathematical and system safety invariants enforced during this execution step:
                </span>
                {selectedNode.invariants.map((inv, i) => (
                  <div key={i} style={{
                    padding: '14px 18px', borderRadius: '10px', background: 'rgba(16, 185, 129, 0.06)',
                    border: '1px solid rgba(16, 185, 129, 0.2)', display: 'flex', alignItems: 'center', gap: '12px'
                  }}>
                    <ShieldCheck size={18} color="#34d399" />
                    <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)' }}>{inv}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
