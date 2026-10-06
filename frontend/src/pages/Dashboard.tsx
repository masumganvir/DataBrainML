import React, { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  FolderGit2,
  Database,
  Box,
  Rocket,
  Activity,
  Bot,
  Play,
  Upload,
  ArrowUpRight,
  ShieldCheck,
  CheckCircle2,
  Clock,
  Sparkles,
  GitFork,
  FileText,
  FlaskConical,
} from 'lucide-react'

import { authStore } from '../services/authStore'
import { branding } from '../config/branding'

export function Dashboard() {
  const navigate = useNavigate()
  const [storeState, setStoreState] = useState(authStore.getState())

  useEffect(() => {
    return authStore.subscribe(() => setStoreState({ ...authStore.getState() }))
  }, [])

  const { currentProject, user } = storeState

  // Real-time Agent Fleet Status Simulation based on platform execution
  const agentFleet = [
    { name: 'Dataset Profiler Agent', role: 'Understanding', status: 'COMPLETED', time: '1.2s' },
    { name: 'Outlier Decision Agent', role: 'Preprocessing', status: 'COMPLETED', time: '0.8s' },
    { name: 'Leakage Prevention Agent', role: 'Preprocessing', status: 'COMPLETED', time: '0.5s' },
    { name: 'Classical ML & DL Engine', role: 'Modeling', status: 'COMPLETED', time: '4.8s' },
    { name: 'Optuna HPO Agent', role: 'Optimization', status: 'COMPLETED', time: '12.4s' },
    { name: 'Production Readiness Auditor', role: 'Evaluation', status: 'COMPLETED', time: '0.9s' },
    { name: 'Drift Detection Monitor', role: 'Monitoring', status: 'WATCHING', time: 'continuous' },
  ]

  const championModels = [
    {
      name: 'LightGBM Churn Classifier',
      family: 'Gradient Boosting',
      metric: 'F1: 0.891 | ROC-AUC: 0.942',
      latency: '6.4 ms',
      stage: 'Production',
      status: 'Healthy',
    },
    {
      name: 'Hybrid PyTorch-XGBoost Shield',
      family: 'Deep Ensemble',
      metric: 'F1: 0.925 | PR-AUC: 0.961',
      latency: '11.8 ms',
      stage: 'Production',
      status: 'Healthy',
    },
    {
      name: 'CatBoost LTV Regressor',
      family: 'Decision Trees',
      metric: 'RMSE: 142.5 | R²: 0.884',
      latency: '4.2 ms',
      stage: 'Staging',
      status: 'Candidate',
    },
  ]

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '28px' }}>
      {/* Welcome Banner */}
      <div
        style={{
          background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(6, 182, 212, 0.1) 100%)',
          border: '1px solid rgba(99, 102, 241, 0.25)',
          borderRadius: 'var(--radius-xl)',
          padding: '28px 32px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '20px',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--secondary-accent)' }}>
              ENTERPRISE AGENTIC AUTOML & MLOPS
            </span>
          </div>
          <h1 style={{ fontSize: '1.8rem', fontWeight: 800, letterSpacing: '-0.02em', margin: 0 }}>
            Welcome back, {user?.name || 'Engineer'}
          </h1>
          <p style={{ color: 'var(--text-secondary)', marginTop: '8px', maxWidth: '640px', fontSize: '0.95rem' }}>
            {branding.productName} is continuously orchestrating your 47+ deterministic Python ML agents, 
            tracking experiments, monitoring production inference distributions, and safeguarding data leakage.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '12px' }}>
          <button
            onClick={() => navigate('/app/datasets')}
            className="btn btn-secondary"
            style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
          >
            <Upload size={16} /> Upload Dataset
          </button>
          <button
            onClick={() => navigate('/app/experiments')}
            className="btn btn-primary"
            style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
          >
            <Play size={16} /> Run AutoML Workflow
          </button>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '18px' }}>
        <div className="metric-kpi-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>ACTIVE PROJECTS</div>
              <div style={{ fontSize: '1.8rem', fontWeight: 800, marginTop: '6px' }}>3</div>
            </div>
            <div style={{ padding: '8px', borderRadius: '8px', background: 'rgba(99, 102, 241, 0.1)', color: 'var(--primary-light)' }}>
              <FolderGit2 size={20} />
            </div>
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--success)', marginTop: '12px', display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span>✓ Multi-tenancy isolated</span>
          </div>
        </div>

        <div className="metric-kpi-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>MANAGED DATASETS</div>
              <div style={{ fontSize: '1.8rem', fontWeight: 800, marginTop: '6px' }}>6</div>
            </div>
            <div style={{ padding: '8px', borderRadius: '8px', background: 'rgba(6, 182, 212, 0.1)', color: 'var(--secondary-accent)' }}>
              <Database size={20} />
            </div>
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--secondary-accent)', marginTop: '12px' }}>
            <span>Parquet, CSV & SQL views</span>
          </div>
        </div>

        <div className="metric-kpi-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>CHAMPION MODELS</div>
              <div style={{ fontSize: '1.8rem', fontWeight: 800, marginTop: '6px' }}>4</div>
            </div>
            <div style={{ padding: '8px', borderRadius: '8px', background: 'rgba(16, 185, 129, 0.1)', color: 'var(--success)' }}>
              <Box size={20} />
            </div>
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--success)', marginTop: '12px' }}>
            <span>8-Point audit validated</span>
          </div>
        </div>

        <div className="metric-kpi-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>ACTIVE DEPLOYMENTS</div>
              <div style={{ fontSize: '1.8rem', fontWeight: 800, marginTop: '6px' }}>2</div>
            </div>
            <div style={{ padding: '8px', borderRadius: '8px', background: 'rgba(236, 72, 153, 0.1)', color: '#ec4899' }}>
              <Rocket size={20} />
            </div>
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '12px' }}>
            <span>p99 latency &lt; 12ms</span>
          </div>
        </div>

        <div className="metric-kpi-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>DRIFT STATUS</div>
              <div style={{ fontSize: '1.4rem', fontWeight: 800, marginTop: '6px', color: 'var(--warning)' }}>
                1 Warning
              </div>
            </div>
            <div style={{ padding: '8px', borderRadius: '8px', background: 'rgba(245, 158, 11, 0.1)', color: 'var(--warning)' }}>
              <Activity size={20} />
            </div>
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '12px' }}>
            <span>PSI: 0.28 (transaction_amount)</span>
          </div>
        </div>
      </div>

      {/* Main Grid: Champion Models + Agent Fleet */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(420px, 1fr))', gap: '24px' }}>
        {/* Production Models Leaderboard */}
        <div
          style={{
            background: 'var(--bg-card)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-xl)',
            padding: '24px',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
            <div>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 700, margin: 0 }}>Champion Model Registry</h3>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', margin: '4px 0 0 0' }}>
                Validated candidate models with live inference metrics
              </p>
            </div>
            <Link
              to="/app/models"
              style={{ fontSize: '0.8rem', color: 'var(--primary-light)', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '4px' }}
            >
              View Registry <ArrowUpRight size={14} />
            </Link>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {championModels.map((m) => (
              <div
                key={m.name}
                style={{
                  padding: '14px 16px',
                  borderRadius: 'var(--radius-md)',
                  background: 'rgba(15, 23, 42, 0.4)',
                  border: '1px solid var(--border-subtle)',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}
              >
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>{m.name}</span>
                    <span
                      style={{
                        fontSize: '0.65rem',
                        padding: '2px 6px',
                        borderRadius: '4px',
                        background: m.stage === 'Production' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(99, 102, 241, 0.15)',
                        color: m.stage === 'Production' ? 'var(--success)' : 'var(--primary-light)',
                        fontWeight: 600,
                      }}
                    >
                      {m.stage.toUpperCase()}
                    </span>
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                    {m.family} • {m.metric}
                  </div>
                </div>

                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: '0.85rem', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>{m.latency}</div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>p99 latency</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Real-time Agent Fleet Status */}
        <div
          style={{
            background: 'var(--bg-card)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-xl)',
            padding: '24px',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
            <div>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 700, margin: 0 }}>Specialized Agent Fleet</h3>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', margin: '4px 0 0 0' }}>
                Deterministic Python tools guided by LangGraph orchestration
              </p>
            </div>
            <Link
              to="/app/pipelines"
              style={{ fontSize: '0.8rem', color: 'var(--primary-light)', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '4px' }}
            >
              Pipeline Visualizer <ArrowUpRight size={14} />
            </Link>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {agentFleet.map((agent) => (
              <div
                key={agent.name}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '10px 14px',
                  borderRadius: 'var(--radius-md)',
                  background: 'rgba(15, 23, 42, 0.3)',
                  border: '1px solid var(--border-subtle)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <div
                    style={{
                      width: '8px',
                      height: '8px',
                      borderRadius: '50%',
                      background: agent.status === 'COMPLETED' ? 'var(--success)' : 'var(--secondary-accent)',
                      boxShadow: agent.status === 'COMPLETED' ? '0 0 6px var(--success)' : '0 0 8px var(--secondary-accent)',
                    }}
                  />
                  <div>
                    <span style={{ fontSize: '0.85rem', fontWeight: 500 }}>{agent.name}</span>
                    <span style={{ marginLeft: '8px', fontSize: '0.7rem', color: 'var(--text-muted)' }}>({agent.role})</span>
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <span style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>
                    {agent.time}
                  </span>
                  <span
                    style={{
                      fontSize: '0.65rem',
                      padding: '2px 6px',
                      borderRadius: '4px',
                      background: agent.status === 'COMPLETED' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(6, 182, 212, 0.1)',
                      color: agent.status === 'COMPLETED' ? 'var(--success)' : 'var(--secondary-accent)',
                      fontWeight: 600,
                    }}
                  >
                    {agent.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Quick Action Navigation Grid */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 700, margin: 0 }}>Quick Workspaces</h3>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
            4 active workspaces
          </span>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '16px' }}>
          <Link to="/app/datasets" className="workspace-card">
            <span className="workspace-card-icon">
              <Database size={26} color="var(--secondary-accent)" />
            </span>
            <div style={{ fontWeight: 700, fontSize: '0.95rem', marginBottom: '6px' }}>Data & Profiling Studio</div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', lineHeight: 1.5, marginBottom: '14px' }}>
              Drag-and-drop ingestion, MCAR diagnostics, and correlation matrices.
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.75rem', color: 'var(--secondary-accent)', fontWeight: 600 }}>
              <span>6 datasets</span>
              <ArrowUpRight size={12} />
            </div>
          </Link>

          <Link to="/app/experiments" className="workspace-card">
            <span className="workspace-card-icon">
              <FlaskConical size={26} color="var(--primary-light)" />
            </span>
            <div style={{ fontWeight: 700, fontSize: '0.95rem', marginBottom: '6px' }}>AutoML Experiment Lab</div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', lineHeight: 1.5, marginBottom: '14px' }}>
              Multi-model comparison, Optuna Bayesian HPO, and cross-validation metrics.
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.75rem', color: 'var(--primary-light)', fontWeight: 600 }}>
              <span>12 HPO runs</span>
              <ArrowUpRight size={12} />
            </div>
          </Link>

          <Link to="/app/assistant" className="workspace-card">
            <span className="workspace-card-icon">
              <Bot size={26} color="#a855f7" />
            </span>
            <div style={{ fontWeight: 700, fontSize: '0.95rem', marginBottom: '6px' }}>AI Data Scientist Assistant</div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', lineHeight: 1.5, marginBottom: '14px' }}>
              Ask analytical questions grounded in real dataset & experiment state.
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.75rem', color: '#a855f7', fontWeight: 600 }}>
              <span>AI-powered context</span>
              <ArrowUpRight size={12} />
            </div>
          </Link>

          <Link to="/app/reports" className="workspace-card">
            <span className="workspace-card-icon">
              <FileText size={26} color="var(--success)" />
            </span>
            <div style={{ fontWeight: 700, fontSize: '0.95rem', marginBottom: '6px' }}>Reports & Artifacts Center</div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', lineHeight: 1.5, marginBottom: '14px' }}>
              Download HTML/PDF executive summaries and Jupyter notebooks.
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.75rem', color: 'var(--success)', fontWeight: 600 }}>
              <span>3 reports ready</span>
              <ArrowUpRight size={12} />
            </div>
          </Link>

          <Link to="/app/pipelines" className="workspace-card">
            <span className="workspace-card-icon">
              <GitFork size={26} color="var(--warning)" />
            </span>
            <div style={{ fontWeight: 700, fontSize: '0.95rem', marginBottom: '6px' }}>Pipeline DAG Visualizer</div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', lineHeight: 1.5, marginBottom: '14px' }}>
              Interactive 8-stage pipeline graph with node inspector and log streams.
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.75rem', color: 'var(--warning)', fontWeight: 600 }}>
              <span>Last run: 2m ago</span>
              <ArrowUpRight size={12} />
            </div>
          </Link>

          <Link to="/app/monitoring" className="workspace-card">
            <span className="workspace-card-icon">
              <ShieldCheck size={26} color="#ec4899" />
            </span>
            <div style={{ fontWeight: 700, fontSize: '0.95rem', marginBottom: '6px' }}>Drift & Monitoring Center</div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', lineHeight: 1.5, marginBottom: '14px' }}>
              KS-stat & PSI drift tracking with live baseline vs ingress comparison.
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.75rem', color: '#ec4899', fontWeight: 600 }}>
              <span style={{ color: 'var(--warning)' }}>⚠ 1 drift alert</span>
              <ArrowUpRight size={12} />
            </div>
          </Link>
        </div>
      </div>
    </div>
  )
}

export default Dashboard
