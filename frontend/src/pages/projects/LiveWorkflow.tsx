import React, { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import {
  Sparkles,
  Bot,
  Cpu,
  Clock,
  Wrench,
  CheckCircle2,
  Circle,
  AlertTriangle,
  RefreshCw,
  ArrowRight,
  Database,
  FileCode,
  Layers,
  ChevronDown,
  ChevronUp,
  AlertCircle,
  Play,
  Sliders,
  ShieldCheck,
  TrendingUp,
} from 'lucide-react'
import { projectsApi, RunStatusResponse } from '../../services/api'

export function LiveWorkflow() {
  const { projectId = '', runId = '' } = useParams<{ projectId: string; runId: string }>()
  const navigate = useNavigate()

  const [runState, setRunState] = useState<RunStatusResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [submittingDecision, setSubmittingDecision] = useState(false)
  const [isLogExpanded, setIsLogExpanded] = useState(true)
  const [wsConnected, setWsConnected] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const logEndRef = useRef<HTMLDivElement>(null)
  const pageBottomRef = useRef<HTMLDivElement>(null)

  // Fetch run status from backend polling fallback
  const fetchStatus = async () => {
    try {
      const data = await projectsApi.getRunStatus(projectId, runId)
      setRunState(data)
      setLoading(false)
    } catch (err: any) {
      console.warn('Poll status error:', err)
      setError(err.message)
    }
  }

  // Smooth auto-scroll down to completion buttons when finished
  useEffect(() => {
    if (runState?.status === 'COMPLETED') {
      const timer = setTimeout(() => {
        pageBottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
      }, 400)
      return () => clearTimeout(timer)
    }
  }, [runState?.status])

  // WebSocket real-time subscription with polling fallback
  useEffect(() => {
    if (!projectId || !runId) return

    fetchStatus()

    // 1. Establish WebSocket connection
    let ws: WebSocket | null = null
    try {
      ws = projectsApi.createWebSocket(projectId, runId)

      ws.onopen = () => {
        setWsConnected(true)
        console.log('LiveWorkflow WebSocket connected')
      }

      ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data)
          if (payload.event === 'stage.started' || payload.event === 'stage.completed' || payload.event === 'agent.warning' || payload.event === 'job.completed') {
            fetchStatus()
          }
        } catch (e) {
          // ignore ping
        }
      }

      ws.onerror = () => {
        setWsConnected(false)
      }

      ws.onclose = () => {
        setWsConnected(false)
      }
    } catch (e) {
      setWsConnected(false)
    }

    // 2. Fallback polling interval every 1.5 seconds while RUNNING or PAUSED
    const interval = setInterval(() => {
      fetchStatus()
    }, 1500)

    return () => {
      clearInterval(interval)
      if (ws) ws.close()
    }
  }, [projectId, runId])

  // Scroll to bottom of activity logs
  useEffect(() => {
    if (logEndRef.current) {
      logEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [runState?.logs])

  // Handle Human-in-the-loop decision submission
  const handleDecision = async (optionValue: string) => {
    if (!runState?.pending_decision) return
    setSubmittingDecision(true)

    try {
      await projectsApi.submitDecision(
        projectId,
        runId,
        runState.pending_decision.category,
        optionValue,
        `Selected by user: ${optionValue}`
      )
      // Immediately refresh status
      await fetchStatus()
    } catch (err: any) {
      alert(`Failed to submit decision: ${err.message}`)
    } finally {
      setSubmittingDecision(false)
    }
  }

  const formatElapsed = (sec: number) => {
    const mins = Math.floor(sec / 60)
    const s = Math.floor(sec % 60)
    return `${mins.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
  }

  if (loading && !runState) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '60vh' }}>
        <RefreshCw size={32} className="animate-spin" color="var(--primary)" style={{ marginBottom: '16px' }} />
        <h2 style={{ fontSize: '1.2rem', fontWeight: 700 }}>Connecting to Agent Orchestrator...</h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Subscribing to LangGraph execution events for run {runId}</p>
      </div>
    )
  }

  const isCompleted = runState?.status === 'COMPLETED'
  const isPaused = runState?.status === 'PAUSED'
  const isRunning = runState?.status === 'RUNNING'

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', maxWidth: '1440px', margin: '0 auto', paddingBottom: '60px' }}>
      {/* Top Banner: Run Status & Navigation */}
      <div
        style={{
          background: 'var(--bg-card)',
          border: '1px solid var(--border-subtle)',
          borderRadius: 'var(--radius-xl)',
          padding: '18px 24px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '16px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div
            style={{
              width: '42px',
              height: '42px',
              borderRadius: '12px',
              background: isCompleted
                ? 'rgba(16, 185, 129, 0.12)'
                : isPaused
                ? 'rgba(245, 158, 11, 0.12)'
                : 'rgba(99, 102, 241, 0.12)',
              color: isCompleted ? 'var(--success)' : isPaused ? '#f59e0b' : 'var(--primary-light)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            {isCompleted ? <CheckCircle2 size={24} /> : isPaused ? <AlertTriangle size={24} /> : <Bot size={24} />}
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <h1 style={{ fontSize: '1.35rem', fontWeight: 800, margin: 0 }}>
                {isCompleted ? 'Analysis Complete' : isPaused ? 'Action Required (Paused)' : 'Autonomous Agents Working'}
              </h1>
              <span
                style={{
                  fontSize: '0.72rem',
                  fontWeight: 700,
                  padding: '2px 8px',
                  borderRadius: 'var(--radius-full)',
                  background: isCompleted
                    ? 'rgba(16, 185, 129, 0.15)'
                    : isPaused
                    ? 'rgba(245, 158, 11, 0.15)'
                    : 'rgba(99, 102, 241, 0.15)',
                  color: isCompleted ? 'var(--success)' : isPaused ? '#f59e0b' : 'var(--primary-light)',
                }}
              >
                {runState?.status}
              </span>
            </div>
            <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '2px' }}>
              Project: <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{projectId}</span> • Run ID: <span style={{ fontFamily: 'var(--font-mono)' }}>{runId}</span> • Stream:{' '}
              <span style={{ color: wsConnected ? 'var(--success)' : 'var(--text-muted)' }}>
                {wsConnected ? '● WebSocket Live' : '○ Polling Fallback'}
              </span>
            </div>
          </div>
        </div>

        {/* Action Button */}
        {isCompleted && (
          <button
            type="button"
            onClick={() => navigate(`/projects/${projectId}/results/${runId}`)}
            style={{
              padding: '10px 20px',
              borderRadius: 'var(--radius-md)',
              background: 'linear-gradient(135deg, var(--success) 0%, #059669 100%)',
              color: '#fff',
              border: 'none',
              fontWeight: 700,
              fontSize: '0.9rem',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              cursor: 'pointer',
              boxShadow: '0 4px 14px rgba(16, 185, 129, 0.35)',
            }}
          >
            <span>Open Final Results Workspace</span>
            <ArrowRight size={16} />
          </button>
        )}
      </div>

      {/* Human-in-the-Loop Approval Modal / Card */}
      {runState?.pending_decision && (
        <div
          style={{
            background: 'linear-gradient(135deg, rgba(245, 158, 11, 0.12) 0%, rgba(217, 119, 6, 0.05) 100%)',
            border: '2px solid rgba(245, 158, 11, 0.4)',
            borderRadius: 'var(--radius-xl)',
            padding: '24px 28px',
            boxShadow: '0 8px 32px rgba(245, 158, 11, 0.15)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: '14px', marginBottom: '14px' }}>
            <div style={{ width: '40px', height: '40px', borderRadius: '10px', background: 'rgba(245, 158, 11, 0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#f59e0b', flexShrink: 0 }}>
              <AlertTriangle size={22} />
            </div>
            <div>
              <span style={{ fontSize: '0.72rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.08em', color: '#f59e0b' }}>
                Human-In-The-Loop Decision Required
              </span>
              <h2 style={{ fontSize: '1.25rem', fontWeight: 800, margin: '2px 0 6px 0', color: 'var(--text-primary)' }}>
                {runState.pending_decision.title}
              </h2>
              <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', margin: 0, lineHeight: 1.5 }}>
                {runState.pending_decision.message}
              </p>
              {runState.pending_decision.explanation && (
                <div style={{ marginTop: '8px', fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                  💡 {runState.pending_decision.explanation}
                </div>
              )}
            </div>
          </div>

          {/* Decision Options */}
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px', marginTop: '16px' }}>
            {runState.pending_decision.options.map((opt) => {
              const isRecommended = opt.value === runState.pending_decision?.recommended_choice
              return (
                <button
                  key={opt.value}
                  type="button"
                  disabled={submittingDecision}
                  onClick={() => handleDecision(opt.value)}
                  style={{
                    padding: '10px 18px',
                    borderRadius: 'var(--radius-md)',
                    background: isRecommended ? '#f59e0b' : 'var(--bg-primary)',
                    color: isRecommended ? '#000' : 'var(--text-primary)',
                    border: isRecommended ? 'none' : '1px solid var(--border-default)',
                    fontWeight: 700,
                    fontSize: '0.85rem',
                    cursor: submittingDecision ? 'not-allowed' : 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    transition: 'all 0.15s',
                  }}
                >
                  {isRecommended && <span>★ Recommended:</span>}
                  <span>{opt.label}</span>
                </button>
              )
            })}
          </div>
        </div>
      )}

      {/* 4-Quadrant Workbench Layout */}
      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1fr) minmax(0, 2fr) minmax(0, 1fr)', gap: '20px' }}>
        {/* LEFT QUADRANT: Pipeline Steps (Vertical Timeline) */}
        <div
          style={{
            background: 'var(--bg-card)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-xl)',
            padding: '20px',
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '12px' }}>
            <h3 style={{ fontSize: '0.92rem', fontWeight: 800, margin: 0, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Pipeline Stages
            </h3>
            <span style={{ fontSize: '0.8rem', fontWeight: 800, color: 'var(--primary-light)' }}>
              {runState?.progress_pct}%
            </span>
          </div>

          {/* Actual Workflow Driven Timeline */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', overflowY: 'auto', maxHeight: '540px' }}>
            {runState?.timeline.map((stage, idx) => {
              const isCompleted = stage.state === 'COMPLETED'
              const isRunning = stage.state === 'RUNNING'
              const isWarning = stage.state === 'WARNING'

              return (
                <div
                  key={stage.id}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '10px',
                    padding: '8px 10px',
                    borderRadius: 'var(--radius-md)',
                    background: isRunning
                      ? 'rgba(99, 102, 241, 0.08)'
                      : isWarning
                      ? 'rgba(245, 158, 11, 0.08)'
                      : 'transparent',
                    border: isRunning
                      ? '1px solid rgba(99, 102, 241, 0.25)'
                      : isWarning
                      ? '1px solid rgba(245, 158, 11, 0.25)'
                      : '1px solid transparent',
                  }}
                >
                  <div style={{ flexShrink: 0 }}>
                    {isCompleted ? (
                      <CheckCircle2 size={16} color="var(--success)" />
                    ) : isRunning ? (
                      <RefreshCw size={16} className="animate-spin" color="var(--primary-light)" />
                    ) : isWarning ? (
                      <AlertTriangle size={16} color="#f59e0b" />
                    ) : (
                      <Circle size={16} color="var(--text-muted)" style={{ opacity: 0.4 }} />
                    )}
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: '0.82rem', fontWeight: isRunning ? 700 : 500, color: isRunning ? 'var(--primary-light)' : isCompleted ? 'var(--text-primary)' : 'var(--text-muted)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {stage.name}
                    </div>
                  </div>
                  <span
                    style={{
                      fontSize: '0.68rem',
                      fontWeight: 700,
                      padding: '2px 6px',
                      borderRadius: '3px',
                      background: isCompleted
                        ? 'rgba(16, 185, 129, 0.1)'
                        : isRunning
                        ? 'rgba(99, 102, 241, 0.15)'
                        : isWarning
                        ? 'rgba(245, 158, 11, 0.15)'
                        : 'rgba(255, 255, 255, 0.03)',
                      color: isCompleted
                        ? 'var(--success)'
                        : isRunning
                        ? 'var(--primary-light)'
                        : isWarning
                        ? '#f59e0b'
                        : 'var(--text-muted)',
                    }}
                  >
                    {stage.state}
                  </span>
                </div>
              )
            })}
          </div>
        </div>

        {/* CENTER QUADRANT: Current Agent Activity & Agent Pipeline Graph */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Agent Activity Card */}
          <div
            style={{
              background: 'var(--bg-card)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-xl)',
              padding: '22px 26px',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
              <div>
                <span style={{ fontSize: '0.72rem', textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--primary-light)', fontWeight: 700 }}>
                  Active Agent
                </span>
                <h2 style={{ fontSize: '1.35rem', fontWeight: 800, margin: '4px 0 0 0' }}>
                  {runState?.current_agent}
                </h2>
              </div>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  background: 'rgba(15, 23, 42, 0.5)',
                  padding: '6px 12px',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--border-default)',
                  fontSize: '0.85rem',
                  fontFamily: 'var(--font-mono)',
                }}
              >
                <Clock size={15} color="var(--primary-light)" />
                <span>Elapsed: {formatElapsed(runState?.elapsed_seconds || 0)}</span>
              </div>
            </div>

            {/* Task Summary */}
            <div
              style={{
                padding: '14px 18px',
                borderRadius: 'var(--radius-md)',
                background: 'var(--bg-primary)',
                border: '1px solid var(--border-subtle)',
                marginBottom: '16px',
              }}
            >
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '4px' }}>
                Current Analytical Task:
              </div>
              <div style={{ fontSize: '0.94rem', fontWeight: 600, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                {isRunning && <RefreshCw size={15} className="animate-spin" color="var(--primary-light)" />}
                <span>{runState?.current_task}</span>
              </div>
            </div>

            {/* Tools In Use */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
              <Wrench size={14} color="var(--primary-light)" />
              <span style={{ fontWeight: 600 }}>Specialized Tools:</span>
              <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>{runState?.current_tools}</span>
            </div>
          </div>

          {/* Interactive Agent Pipeline Graph */}
          <div
            style={{
              background: 'var(--bg-card)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-xl)',
              padding: '22px 26px',
            }}
          >
            <h3 style={{ fontSize: '0.92rem', fontWeight: 800, margin: '0 0 16px 0', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              LangGraph Multi-Agent Topology
            </h3>

            {/* Visual Node Grid */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '10px' }}>
              {runState?.agent_graph.slice(0, 12).map((node, i) => {
                const isNodeDone = node.state === 'COMPLETED'
                const isNodeRunning = node.state === 'RUNNING'

                return (
                  <div
                    key={node.id}
                    style={{
                      padding: '10px 12px',
                      borderRadius: 'var(--radius-md)',
                      background: isNodeRunning
                        ? 'rgba(99, 102, 241, 0.12)'
                        : isNodeDone
                        ? 'rgba(16, 185, 129, 0.08)'
                        : 'var(--bg-primary)',
                      border: isNodeRunning
                        ? '1px solid var(--primary)'
                        : isNodeDone
                        ? '1px solid rgba(16, 185, 129, 0.25)'
                        : '1px solid var(--border-subtle)',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '4px',
                      transition: 'all 0.2s',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontSize: '0.68rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
                        #{i + 1}
                      </span>
                      {isNodeDone ? (
                        <CheckCircle2 size={13} color="var(--success)" />
                      ) : isNodeRunning ? (
                        <RefreshCw size={13} className="animate-spin" color="var(--primary-light)" />
                      ) : (
                        <Circle size={12} color="var(--text-muted)" style={{ opacity: 0.3 }} />
                      )}
                    </div>
                    <div style={{ fontSize: '0.78rem', fontWeight: 700, color: isNodeRunning ? 'var(--primary-light)' : 'var(--text-primary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {node.name.replace(' Analysis', '').replace(' Selection', '')}
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </div>

        {/* RIGHT QUADRANT: Dataset / Run Information */}
        <div
          style={{
            background: 'var(--bg-card)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-xl)',
            padding: '20px',
            display: 'flex',
            flexDirection: 'column',
            gap: '16px',
          }}
        >
          <h3 style={{ fontSize: '0.92rem', fontWeight: 800, margin: 0, textTransform: 'uppercase', letterSpacing: '0.05em', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '12px' }}>
            Run Metadata
          </h3>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', fontSize: '0.82rem' }}>
            <div>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.74rem' }}>DATASET</div>
              <div style={{ fontWeight: 600, marginTop: '2px', wordBreak: 'break-all' }}>{runState?.dataset_name || 'telecom_churn.csv'}</div>
            </div>

            <div>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.74rem' }}>TARGET VARIABLE</div>
              <div style={{ fontWeight: 600, marginTop: '2px', color: 'var(--primary-light)' }}>
                {runState?.results?.target || 'churn'}
              </div>
            </div>

            <div>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.74rem' }}>EXECUTION MODE</div>
              <div style={{ fontWeight: 600, marginTop: '2px' }}>Autonomous LangGraph Agent</div>
            </div>

            <div>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.74rem' }}>OPTIMIZATION GOAL</div>
              <div style={{ fontWeight: 600, marginTop: '2px' }}>Maximize Generalization (F1 / Recall)</div>
            </div>

            <div>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.74rem' }}>USER INTENT PROMPT</div>
              <div style={{ fontStyle: 'italic', color: 'var(--text-secondary)', marginTop: '4px', fontSize: '0.8rem', lineHeight: 1.4, background: 'var(--bg-primary)', padding: '8px 10px', borderRadius: 'var(--radius-sm)' }}>
                "{runState?.prompt || 'Predict churn with high recall'}"
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* BOTTOM QUADRANT: AI Activity Log (Safe Summaries) */}
      <div
        style={{
          background: 'var(--bg-card)',
          border: '1px solid var(--border-subtle)',
          borderRadius: 'var(--radius-xl)',
          overflow: 'hidden',
        }}
      >
        <div
          onClick={() => setIsLogExpanded(!isLogExpanded)}
          style={{
            padding: '16px 24px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            cursor: 'pointer',
            background: 'rgba(15, 23, 42, 0.4)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <FileCode size={16} color="var(--primary-light)" />
            <span style={{ fontSize: '0.9rem', fontWeight: 700 }}>AI Agent Activity Log</span>
            <span style={{ fontSize: '0.72rem', background: 'rgba(255,255,255,0.06)', padding: '2px 8px', borderRadius: '12px', color: 'var(--text-muted)' }}>
              {runState?.logs.length || 0} entries
            </span>
          </div>
          {isLogExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </div>

        {isLogExpanded && (
          <div
            style={{
              padding: '16px 24px',
              maxHeight: '260px',
              overflowY: 'auto',
              fontFamily: 'var(--font-mono)',
              fontSize: '0.82rem',
              display: 'flex',
              flexDirection: 'column',
              gap: '8px',
              background: 'var(--bg-primary)',
            }}
          >
            {runState?.logs.map((log, index) => (
              <div key={index} style={{ display: 'flex', gap: '12px', alignItems: 'flex-start' }}>
                <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem', flexShrink: 0 }}>
                  [{log.timestamp}]
                </span>
                <span style={{ color: 'var(--primary-light)', fontWeight: 600, flexShrink: 0 }}>
                  {log.agent}:
                </span>
                <span style={{ color: 'var(--text-primary)', wordBreak: 'break-word' }}>
                  {log.message}
                </span>
              </div>
            ))}
            <div ref={logEndRef} />
          </div>
        )}
      </div>

      {/* COMPLETION HERO CALLOUT & ACTION BUTTONS DOWN AT THE BOTTOM */}
      {isCompleted && (
        <div
          ref={pageBottomRef}
          style={{
            background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.12) 0%, rgba(99, 102, 241, 0.1) 100%)',
            border: '2px solid rgba(16, 185, 129, 0.4)',
            borderRadius: 'var(--radius-xl)',
            padding: '30px 36px',
            display: 'flex',
            flexDirection: 'column',
            gap: '18px',
            boxShadow: '0 12px 40px rgba(16, 185, 129, 0.18)',
            marginTop: '8px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
              <div
                style={{
                  width: '48px',
                  height: '48px',
                  borderRadius: '12px',
                  background: 'rgba(16, 185, 129, 0.2)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'var(--success)',
                  boxShadow: '0 4px 16px rgba(16, 185, 129, 0.3)',
                }}
              >
                <CheckCircle2 size={26} />
              </div>
              <div>
                <span style={{ fontSize: '0.72rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.1em', color: 'var(--success)' }}>
                  Autonomous Pipeline Completed
                </span>
                <h2 style={{ fontSize: '1.4rem', fontWeight: 800, margin: '2px 0 0 0', color: 'var(--text-primary)' }}>
                  Model Trained & Ready For Predictions
                </h2>
                <div style={{ fontSize: '0.84rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
                  Target: <strong style={{ color: 'var(--primary-light)' }}>{runState?.results?.target || 'target'}</strong> • Champion Model: <strong>{runState?.results?.champion_model || 'Best ML Model'}</strong> • Ready for real-time input inference
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
              <button
                type="button"
                onClick={() => navigate(`/projects/${projectId}/predict`)}
                style={{
                  padding: '12px 24px',
                  borderRadius: 'var(--radius-md)',
                  background: 'linear-gradient(135deg, var(--primary) 0%, #4338ca 100%)',
                  color: '#fff',
                  border: 'none',
                  fontWeight: 800,
                  fontSize: '0.95rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  cursor: 'pointer',
                  boxShadow: '0 6px 20px rgba(99, 102, 241, 0.45)',
                }}
              >
                <Sparkles size={18} />
                <span>Predict on New Inputs (AI Agent)</span>
                <ArrowRight size={16} />
              </button>

              <button
                type="button"
                onClick={() => navigate(`/projects/${projectId}/results/${runId}`)}
                style={{
                  padding: '12px 20px',
                  borderRadius: 'var(--radius-md)',
                  background: 'linear-gradient(135deg, var(--success) 0%, #059669 100%)',
                  color: '#fff',
                  border: 'none',
                  fontWeight: 700,
                  fontSize: '0.9rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  cursor: 'pointer',
                  boxShadow: '0 4px 14px rgba(16, 185, 129, 0.35)',
                }}
              >
                <span>View Results & Artifacts</span>
                <ArrowRight size={16} />
              </button>
            </div>
          </div>
        </div>
      )}
      {!isCompleted && <div ref={pageBottomRef} />}
    </div>
  )
}
