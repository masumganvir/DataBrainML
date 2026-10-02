import React, { useCallback, useEffect, useRef, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Sparkles, ArrowLeft, Upload, Send, Bot, User, Loader2,
  CheckCircle2, Circle, AlertTriangle, ChevronDown, ChevronUp,
  Play, Code2, BarChart3, Brain, ShieldCheck, Layers, Zap,
  Target, GitMerge, TrendingUp, X, Check, AlertCircle,
  Download, Eye, RefreshCw, Database, Building2, Shield, Settings2, Package,
  Sliders, Cpu, Filter
} from 'lucide-react'
import { sessionsApi, datasetsApi, analysisApi, mlApi, chatApi, workflowApi, decisionsApi, AgentInfo } from '@/services/api'
import { ContextModal } from '@/components/ContextModal'
import { AutoMLDashboard } from '@/components/AutoMLDashboard'
import { DownloadCenter } from '@/components/DownloadCenter'
import type { TrainingResponse } from '@/types'


// ─── Types ────────────────────────────────────────────────────────────────────

interface ChatMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: Date
}

interface PendingDecision {
  decision_id: string
  stage: string
  category: string
  title: string
  message: string
  recommended_choice: string
  options: Array<{ value: string; label: string }>
  context?: Record<string, unknown>
}

interface WorkflowStage {
  id: string
  label: string
  icon: React.ReactNode
  description: string
}

// ─── Constants ────────────────────────────────────────────────────────────────

const WORKFLOW_STAGES: WorkflowStage[] = [
  { id: 'INGEST',             label: '1. Ingest',         icon: <Upload size={13} />,       description: 'Validate and ingest dataset file' },
  { id: 'PROFILE',            label: '2. Profile',        icon: <Database size={13} />,     description: 'Statistical distribution profiling' },
  { id: 'QUALITY',            label: '3. Data Quality',   icon: <ShieldCheck size={13} />,  description: 'Duplicates, missingness & PII audit' },
  { id: 'OUTLIERS',           label: '4. Outliers',       icon: <AlertCircle size={13} />,  description: 'Intelligent fraud-safe outlier treatment' },
  { id: 'MISSING_VALUES',     label: '5. Missing Values', icon: <Filter size={13} />,       description: 'Multivariate statistical imputation' },
  { id: 'ENCODING',           label: '6. Encoding',       icon: <Layers size={13} />,       description: 'Leak-free categorical encoding' },
  { id: 'SCALING',            label: '7. Scaling',        icon: <Sliders size={13} />,      description: 'Model-aware numerical scaling' },
  { id: 'TRANSFORMATION',     label: '8. Transform',      icon: <Sparkles size={13} />,     description: 'Power and log skewness correction' },
  { id: 'FEATURE_ENGINEERING',label: '9. Feature Eng.',   icon: <Zap size={13} />,          description: 'Capped polynomial and datetime features' },
  { id: 'FEATURE_SELECTION',  label: '10. Selection',     icon: <GitMerge size={13} />,     description: 'Mutual info & ANOVA redundancy filter' },
  { id: 'LEAKAGE_CHECK',      label: '11. Leakage',       icon: <Shield size={13} />,       description: 'Target correlation safeguard' },
  { id: 'ML_RECOMMENDATION',  label: '12. Models',        icon: <Brain size={13} />,        description: 'Candidate algorithm portfolio' },
  { id: 'TRAINING',           label: '13. Training',      icon: <Cpu size={13} />,          description: 'Leak-free cross-validated pipelines' },
  { id: 'TUNING',             label: '14. Optuna Tuning', icon: <Sliders size={13} />,      description: 'Bayesian hyperparameter optimization' },
  { id: 'EVALUATION',         label: '15. Evaluation',    icon: <BarChart3 size={13} />,    description: 'Multi-metric holdout performance' },
  { id: 'EXPLAINABILITY',     label: '16. SHAP Explain',  icon: <Eye size={13} />,          description: 'Attribution & permutation importance' },
  { id: 'ARTIFACTS',          label: '17. Artifacts',     icon: <Package size={13} />,      description: 'Joblib pipeline, metadata & notebooks' },
  { id: 'COMPLETE',           label: '18. Deployment',   icon: <TrendingUp size={13} />,   description: 'FastAPI microservice & drift monitoring' },
]

const WELCOME_MESSAGE = `# Welcome to DataWise AI 👋

I'm your autonomous **AI Data Scientist**. Here's what I can do for you:

- 📊 **Profile** your dataset — schema, statistics, anomaly detection
- 🔍 **Identify** missing values, outliers, and data quality issues
- ⚠️ **Pause for your approval** before any destructive operations
- ⚙️ **Engineer** new features and select the most informative ones
- 🔒 **Detect** data leakage risks that would corrupt your model
- 🧬 **Build** production-ready \`sklearn\` preprocessing pipelines
- 🤖 **Recommend** the best ML algorithms for your dataset

---

**To start:** Upload a CSV, Excel, or JSON file using the panel on the right, then click **"Run Full Analysis"** or ask me anything about your data.`

// ─── Helpers ──────────────────────────────────────────────────────────────────

function genId() { return Math.random().toString(36).slice(2) }

function StageIndicator({ currentStage, isPaused }: { currentStage: string; isPaused?: boolean }) {
  const currentIdx = WORKFLOW_STAGES.findIndex(s => s.id === currentStage)

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '3px' }}>
      {WORKFLOW_STAGES.map((stage, idx) => {
        const isDone = idx < currentIdx
        const isActive = idx === currentIdx
        const isWaitingApproval = isActive && isPaused

        let badgeText = 'pending'
        let badgeColor = 'var(--text-muted)'
        let badgeBg = 'rgba(255,255,255,0.03)'

        if (isDone) {
          badgeText = 'completed'
          badgeColor = '#34d399'
          badgeBg = 'rgba(16, 185, 129, 0.12)'
        } else if (isWaitingApproval) {
          badgeText = 'approval'
          badgeColor = '#f59e0b'
          badgeBg = 'rgba(245, 158, 11, 0.15)'
        } else if (isActive) {
          badgeText = 'running'
          badgeColor = '#818cf8'
          badgeBg = 'rgba(99, 102, 241, 0.2)'
        }

        return (
          <div
            key={stage.id}
            title={stage.description}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: '6px',
              padding: '5px 8px',
              borderRadius: '6px',
              background: isActive ? 'rgba(99, 102, 241, 0.12)' : 'transparent',
              border: isActive ? '1px solid rgba(99, 102, 241, 0.35)' : '1px solid transparent',
              transition: 'all 0.2s',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', overflow: 'hidden' }}>
              <div style={{
                width: '16px',
                height: '16px',
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0,
                background: isDone ? 'rgba(16, 185, 129, 0.2)' : isActive ? 'rgba(99, 102, 241, 0.3)' : 'rgba(255,255,255,0.05)',
                color: isDone ? '#34d399' : isActive ? '#818cf8' : 'var(--text-muted)',
              }}>
                {isDone ? <CheckCircle2 size={11} /> : isWaitingApproval ? <AlertTriangle size={11} color="#f59e0b" /> : isActive ? <Loader2 size={11} style={{ animation: 'spin 1s linear infinite' }} /> : <Circle size={10} />}
              </div>
              <span style={{
                fontSize: '0.72rem',
                fontWeight: isActive ? 600 : 400,
                color: isDone ? '#e2e8f0' : isActive ? '#c7d2fe' : 'var(--text-muted)',
                display: 'flex',
                alignItems: 'center',
                gap: '5px',
                whiteSpace: 'nowrap',
                textOverflow: 'ellipsis',
                overflow: 'hidden',
              }}>
                {stage.icon}
                {stage.label}
              </span>
            </div>

            <span style={{
              fontSize: '0.62rem',
              fontWeight: 600,
              textTransform: 'uppercase',
              letterSpacing: '0.04em',
              padding: '1px 5px',
              borderRadius: '4px',
              color: badgeColor,
              background: badgeBg,
              flexShrink: 0,
            }}>
              {badgeText}
            </span>
          </div>
        )
      })}
    </div>
  )
}

function MarkdownContent({ content }: { content: string }) {
  // Simple markdown renderer for chat messages
  const rendered = content
    .replace(/^# (.+)$/gm, '<h1 style="font-size:1.1rem;font-weight:700;margin:0 0 8px;color:#f1f5f9">$1</h1>')
    .replace(/^## (.+)$/gm, '<h2 style="font-size:0.95rem;font-weight:600;margin:8px 0 4px;color:#e2e8f0">$1</h2>')
    .replace(/^### (.+)$/gm, '<h3 style="font-size:0.875rem;font-weight:600;margin:6px 0 4px;color:#cbd5e1">$1</h3>')
    .replace(/\*\*(.+?)\*\*/g, '<strong style="color:#f1f5f9;font-weight:600">$1</strong>')
    .replace(/`([^`]+)`/g, '<code style="background:rgba(99,102,241,0.2);color:#a5b4fc;padding:1px 5px;border-radius:4px;font-size:0.85em;font-family:monospace">$1</code>')
    .replace(/^- (.+)$/gm, '<li style="margin:2px 0;color:#cbd5e1">$1</li>')
    .replace(/(<li[^>]*>.*<\/li>\n?)+/g, (match) => `<ul style="margin:6px 0;padding-left:18px">${match}</ul>`)
    .replace(/^---$/gm, '<hr style="border:none;border-top:1px solid rgba(255,255,255,0.1);margin:12px 0">')
    .replace(/\n\n/g, '<br/><br/>')
    .replace(/\n/g, '<br/>')

  return <div dangerouslySetInnerHTML={{ __html: rendered }} style={{ lineHeight: 1.7, fontSize: '0.875rem', color: '#cbd5e1' }} />
}

function DecisionPanel({ decision, onSubmit }: {
  decision: PendingDecision
  onSubmit: (key: string, value: string) => void
}) {
  const [selected, setSelected] = useState(decision.recommended_choice)
  const [submitting, setSubmitting] = useState(false)

  return (
    <div style={{
      background: 'linear-gradient(135deg, rgba(245, 158, 11, 0.08), rgba(239, 68, 68, 0.05))',
      border: '1px solid rgba(245, 158, 11, 0.3)',
      borderRadius: '12px',
      padding: '16px',
      marginBottom: '12px',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
        <AlertTriangle size={16} color="#f59e0b" />
        <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#fbbf24', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          {decision.category} — Action Required
        </span>
      </div>
      <h4 style={{ marginBottom: '8px', color: '#f1f5f9', fontSize: '0.95rem' }}>{decision.title}</h4>
      <p style={{ fontSize: '0.8rem', color: '#94a3b8', marginBottom: '14px', lineHeight: 1.5 }}>{decision.message}</p>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', marginBottom: '14px' }}>
        {decision.options.map(opt => (
          <label
            key={opt.value}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              padding: '8px 12px',
              borderRadius: '8px',
              border: `1px solid ${selected === opt.value ? 'rgba(99, 102, 241, 0.5)' : 'rgba(255,255,255,0.08)'}`,
              background: selected === opt.value ? 'rgba(99, 102, 241, 0.12)' : 'rgba(255,255,255,0.03)',
              cursor: 'pointer',
              transition: 'all 0.15s',
            }}
          >
            <input
              type="radio"
              name={decision.decision_id}
              value={opt.value}
              checked={selected === opt.value}
              onChange={() => setSelected(opt.value)}
              style={{ accentColor: '#818cf8' }}
            />
            <span style={{ fontSize: '0.8rem', color: selected === opt.value ? '#c7d2fe' : '#94a3b8' }}>
              {opt.label}
            </span>
            {opt.value === decision.recommended_choice && (
              <span style={{ marginLeft: 'auto', fontSize: '0.65rem', color: '#34d399', background: 'rgba(16,185,129,0.1)', padding: '1px 6px', borderRadius: '4px', border: '1px solid rgba(16,185,129,0.2)' }}>
                Recommended
              </span>
            )}
          </label>
        ))}
      </div>

      <button
        className="btn btn-primary"
        style={{ width: '100%', justifyContent: 'center' }}
        disabled={submitting}
        onClick={async () => {
          setSubmitting(true)
          await onSubmit(decision.decision_id, selected)
          setSubmitting(false)
        }}
      >
        {submitting ? <Loader2 size={14} style={{ animation: 'spin 1s linear infinite' }} /> : <Check size={14} />}
        Confirm Decision
      </button>
    </div>
  )
}

// ─── Main Analysis Page ───────────────────────────────────────────────────────

export default function Analysis() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const navigate = useNavigate()

  const [session, setSession] = useState<Record<string, unknown> | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [isSending, setIsSending] = useState(false)
  const [isRunningWorkflow, setIsRunningWorkflow] = useState(false)
  const [currentStage, setCurrentStage] = useState('INGEST')
  const [pendingDecision, setPendingDecision] = useState<PendingDecision | null>(null)
  const [isUploadVisible, setIsUploadVisible] = useState(true)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadedFile, setUploadedFile] = useState<string | null>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [workflowResult, setWorkflowResult] = useState<Record<string, unknown> | null>(null)
  const [readinessScore, setReadinessScore] = useState<number | null>(null)
  const [activeTab, setActiveTab] = useState<'chat' | 'pipeline' | 'results' | 'models' | 'downloads'>('chat')
  const [pipelineCode, setPipelineCode] = useState<string | null>(null)
  const [availableAgents, setAvailableAgents] = useState<AgentInfo[]>([])
  const [selectedAgent, setSelectedAgent] = useState<string>('')
  const [isContextModalOpen, setIsContextModalOpen] = useState(false)
  const [datasetDomain, setDatasetDomain] = useState<string>('')
  const [predictionObjective, setPredictionObjective] = useState<string>('')
  const [executionMode, setExecutionMode] = useState<'guided' | 'autonomous'>('guided')
  const [trainingData, setTrainingData] = useState<TrainingResponse | null>(null)

  const chatEndRef = useRef<HTMLDivElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // ── Load session ──────────────────────────────────────────────────────────
  useEffect(() => {
    if (!sessionId) return
    loadSession()
    loadChatHistory()
    loadAgents()
    loadComparison()
  }, [sessionId])

  const loadComparison = async () => {
    if (!sessionId) return
    try {
      const data = await mlApi.getComparison(sessionId)
      if (data && data.trained) {
        setTrainingData(data)
      }
    } catch {
      /* non-critical */
    }
  }


  const loadAgents = async () => {
    if (!sessionId) return
    try {
      const agents = await chatApi.getAgents(sessionId)
      setAvailableAgents(agents)
    } catch (err) {
      console.error('Failed to load agents:', err)
    }
  }

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const loadSession = async () => {
    if (!sessionId) return
    try {
      const data = await sessionsApi.get(sessionId)
      setSession(data as unknown as Record<string, unknown>)
      setCurrentStage((data.current_stage as string) || 'INGEST')
    } catch (err) {
      console.error('Failed to load session:', err)
    }
  }

  const loadChatHistory = async () => {
    if (!sessionId) return
    try {
      const history = await chatApi.history(sessionId) as Array<Record<string, unknown>>
      if (history.length === 0) {
        setMessages([{
          id: genId(),
          role: 'assistant',
          content: WELCOME_MESSAGE,
          timestamp: new Date(),
        }])
      } else {
        setMessages(history.map((m) => ({
          id: genId(),
          role: (m.role as 'user' | 'assistant') || 'assistant',
          content: m.content as string,
          timestamp: new Date(m.created_at as string),
        })))
      }
    } catch {
      setMessages([{
        id: genId(),
        role: 'assistant',
        content: WELCOME_MESSAGE,
        timestamp: new Date(),
      }])
    }
  }

  // ── File Upload ───────────────────────────────────────────────────────────
  const handleFileUpload = useCallback(async (file: File) => {
    if (!sessionId) return
    const allowed = ['text/csv', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      'application/vnd.ms-excel', 'application/json']
    if (!allowed.some(t => file.type.includes(t.split('/')[1])) && !file.name.match(/\.(csv|xlsx|xls|json)$/i)) {
      addSystemMessage('❌ Unsupported file type. Please upload CSV, XLSX, XLS, or JSON.')
      return
    }
    try {
      setIsUploading(true)
      setUploadProgress(0)
      await datasetsApi.upload(sessionId, file, setUploadProgress)
      setUploadedFile(file.name)
      setCurrentStage('PROFILE')
      setIsUploadVisible(false)
      addSystemMessage(`✅ **${file.name}** uploaded successfully! Click **"Run Full Analysis"** to start the autonomous pipeline.`)
      await loadSession()
    } catch (err: unknown) {
      addSystemMessage(`❌ Upload failed: ${(err as Error).message}`)
    } finally {
      setIsUploading(false)
    }
  }, [sessionId])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    const file = e.dataTransfer.files[0]
    if (file) handleFileUpload(file)
  }, [handleFileUpload])

  // ── Chat ──────────────────────────────────────────────────────────────────
  const addSystemMessage = (content: string) => {
    setMessages(prev => [...prev, {
      id: genId(), role: 'assistant', content, timestamp: new Date()
    }])
  }

  const sendMessage = async () => {
    if (!input.trim() || isSending || !sessionId) return
    const userMessage: ChatMessage = {
      id: genId(), role: 'user', content: input.trim(), timestamp: new Date()
    }
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsSending(true)
    try {
      const response = await chatApi.send(sessionId, userMessage.content, selectedAgent || undefined)
      setMessages(prev => [...prev, {
        id: genId(), role: 'assistant', content: response.content, timestamp: new Date()
      }])
    } catch (err: unknown) {
      addSystemMessage(`❌ Error: ${(err as Error).message}`)
    } finally {
      setIsSending(false)
    }
  }

  // ── Workflow ───────────────────────────────────────────────────────────────
  const runWorkflow = async () => {
    if (!sessionId || isRunningWorkflow) return
    setIsRunningWorkflow(true)
    addSystemMessage('🚀 **Starting autonomous analysis pipeline...** This may take a moment depending on dataset size.')
    try {
      const result = await workflowApi.run(sessionId) as Record<string, unknown>
      setWorkflowResult(result)
      setCurrentStage(result.current_stage as string || 'COMPLETE')
      if ((result.ml_readiness_score as number) !== undefined) {
        setReadinessScore(result.ml_readiness_score as number)
      }
      if (result.has_pending_decision && result.pending_decision) {
        setPendingDecision(result.pending_decision as PendingDecision)
        addSystemMessage('⏸️ **Workflow paused** — a decision requires your review below.')
      } else {
        addSystemMessage(
          `✅ **Analysis complete!** ML Readiness Score: **${result.ml_readiness_score ?? 'N/A'}/100**\n\n` +
          `Completed stages: ${(result.completed_stages as string[]).join(' → ')}\n\n` +
          `Switch to the **Results** tab to see ML recommendations and the generated pipeline.`
        )
        // Load pipeline code
        try {
          const pipeline = await mlApi.buildPipeline(sessionId) as Record<string, unknown>
          setPipelineCode(pipeline.generated_code as string)
        } catch { /* non-critical */ }
      }
      await loadSession()
    } catch (err: unknown) {
      addSystemMessage(`❌ **Workflow error:** ${(err as Error).message}`)
    } finally {
      setIsRunningWorkflow(false)
    }
  }

  // ── Decision submission ────────────────────────────────────────────────────
  const handleDecisionSubmit = async (key: string, value: string) => {
    if (!sessionId) return
    try {
      await decisionsApi.submit(sessionId, key, value)
      setPendingDecision(null)
      addSystemMessage(`✅ **Decision recorded**: "${value}". Continuing analysis...`)
      await runWorkflow()
    } catch (err: unknown) {
      addSystemMessage(`❌ Decision error: ${(err as Error).message}`)
    }
  }

  // ── Render ─────────────────────────────────────────────────────────────────
  const sessionName = (session as Record<string, unknown> | null)?.name as string || 'Analysis Session'

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      {/* ── Header ── */}
      <header style={{
        height: '56px',
        borderBottom: '1px solid var(--border-subtle)',
        background: 'rgba(9, 13, 22, 0.92)',
        backdropFilter: 'blur(16px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 20px',
        flexShrink: 0,
        zIndex: 50,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <button
            className="btn btn-sm btn-outline"
            style={{ padding: '6px 10px' }}
            onClick={() => navigate('/')}
          >
            <ArrowLeft size={14} />
          </button>
          <div style={{ width: '1px', height: '20px', background: 'var(--border-subtle)' }} />
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{ width: '28px', height: '28px', borderRadius: '8px', background: 'var(--primary-gradient)', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 0 10px rgba(99,102,241,0.4)' }}>
              <Sparkles size={14} color="#fff" />
            </div>
            <span style={{ fontWeight: 700, fontSize: '0.95rem' }}>{sessionName}</span>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {/* Execution Mode button */}
          <button
            onClick={() => setIsContextModalOpen(true)}
            className="btn btn-sm btn-outline"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              fontSize: '0.75rem',
              borderColor: executionMode === 'autonomous' ? 'rgba(16,185,129,0.4)' : 'rgba(99,102,241,0.4)',
              color: executionMode === 'autonomous' ? '#34d399' : '#818cf8',
              background: executionMode === 'autonomous' ? 'rgba(16,185,129,0.08)' : 'rgba(99,102,241,0.08)',
            }}
            title="Toggle between Guided Mode and Autonomous Mode"
          >
            {executionMode === 'autonomous' ? <Zap size={12} /> : <Shield size={12} />}
            {executionMode === 'autonomous' ? 'Autonomous Mode' : 'Guided Mode'}
          </button>

          {/* Domain & Objective Context button */}
          <button
            onClick={() => setIsContextModalOpen(true)}
            className="btn btn-sm btn-outline"
            style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.75rem' }}
            title="Set dataset domain and prediction objective"
          >
            <Building2 size={12} />
            {datasetDomain ? `${datasetDomain.toUpperCase()}` : 'Domain Context'}
          </button>

          {readinessScore !== null && (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '4px 10px',
              borderRadius: '6px',
              background: readinessScore >= 80 ? 'rgba(16,185,129,0.1)' : readinessScore >= 50 ? 'rgba(245,158,11,0.1)' : 'rgba(239,68,68,0.1)',
              border: `1px solid ${readinessScore >= 80 ? 'rgba(16,185,129,0.3)' : readinessScore >= 50 ? 'rgba(245,158,11,0.3)' : 'rgba(239,68,68,0.3)'}`,
              color: readinessScore >= 80 ? '#34d399' : readinessScore >= 50 ? '#fbbf24' : '#f87171',
              fontSize: '0.8rem',
              fontWeight: 700,
            }}>
              <TrendingUp size={13} />
              ML Readiness: {readinessScore}/100
            </div>
          )}
          <span className={`badge ${currentStage === 'COMPLETE' ? 'badge-primary' : 'badge-neutral'}`} style={{ fontSize: '0.72rem' }}>
            {currentStage}
          </span>
          <button
            className="btn btn-primary btn-sm"
            onClick={runWorkflow}
            disabled={isRunningWorkflow || !uploadedFile}
            title={!uploadedFile ? 'Upload a dataset first' : 'Run the full analysis pipeline'}
          >
            {isRunningWorkflow
              ? <Loader2 size={13} style={{ animation: 'spin 1s linear infinite' }} />
              : <Play size={13} />
            }
            {isRunningWorkflow ? 'Running...' : 'Run Analysis'}
          </button>
        </div>
      </header>


      {/* ── Body ── */}
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>

        {/* ── Left Sidebar: Workflow Progress ── */}
        <aside style={{
          width: '200px',
          flexShrink: 0,
          borderRight: '1px solid var(--border-subtle)',
          background: 'rgba(9, 13, 22, 0.6)',
          overflowY: 'auto',
          padding: '16px 12px',
        }}>
          <div style={{ fontSize: '0.65rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text-muted)', marginBottom: '10px' }}>
            Pipeline Progress
          </div>
          <StageIndicator currentStage={currentStage} />
        </aside>

        {/* ── Center: Chat + Tabs ── */}
        <main style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          {/* Tab bar */}
          <div style={{
            display: 'flex',
            borderBottom: '1px solid var(--border-subtle)',
            background: 'rgba(9, 13, 22, 0.5)',
            padding: '0 16px',
            gap: '2px',
            flexShrink: 0,
          }}>
            {[
              { id: 'chat', label: 'Chat', icon: <Bot size={13} /> },
              { id: 'pipeline', label: 'Pipeline Code', icon: <Code2 size={13} /> },
              { id: 'results', label: 'EDA & Quality', icon: <Brain size={13} /> },
              { id: 'models', label: 'AutoML & Models', icon: <TrendingUp size={13} /> },
              { id: 'downloads', label: 'Download Center', icon: <Download size={13} /> },
            ].map(tab => (

              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as typeof activeTab)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '10px 14px',
                  fontSize: '0.8rem',
                  fontWeight: 500,
                  color: activeTab === tab.id ? '#c7d2fe' : 'var(--text-muted)',
                  background: 'none',
                  border: 'none',
                  borderBottom: activeTab === tab.id ? '2px solid #818cf8' : '2px solid transparent',
                  cursor: 'pointer',
                  transition: 'all 0.15s',
                  marginBottom: '-1px',
                }}
              >
                {tab.icon}
                {tab.label}
              </button>
            ))}
          </div>

          {/* Tab content */}
          <div style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>

            {/* CHAT TAB */}
            {activeTab === 'chat' && (
              <>
                {/* Decision panel (pinned above messages) */}
                {pendingDecision && (
                  <div style={{ padding: '12px 16px', borderBottom: '1px solid rgba(245,158,11,0.2)', flexShrink: 0 }}>
                    <DecisionPanel decision={pendingDecision} onSubmit={handleDecisionSubmit} />
                  </div>
                )}

                {/* Messages */}
                <div style={{ flex: 1, overflowY: 'auto', padding: '16px' }}>
                  {messages.map(msg => (
                    <div
                      key={msg.id}
                      style={{
                        display: 'flex',
                        gap: '10px',
                        marginBottom: '16px',
                        flexDirection: msg.role === 'user' ? 'row-reverse' : 'row',
                      }}
                    >
                      {/* Avatar */}
                      <div style={{
                        width: '30px',
                        height: '30px',
                        borderRadius: '8px',
                        flexShrink: 0,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        background: msg.role === 'user' ? 'rgba(99,102,241,0.2)' : 'rgba(16,185,129,0.15)',
                        color: msg.role === 'user' ? '#818cf8' : '#34d399',
                        marginTop: '2px',
                      }}>
                        {msg.role === 'user' ? <User size={14} /> : <Bot size={14} />}
                      </div>

                      {/* Bubble */}
                      <div style={{
                        maxWidth: '75%',
                        padding: '10px 14px',
                        borderRadius: msg.role === 'user' ? '12px 4px 12px 12px' : '4px 12px 12px 12px',
                        background: msg.role === 'user'
                          ? 'rgba(99,102,241,0.15)'
                          : 'rgba(255,255,255,0.04)',
                        border: `1px solid ${msg.role === 'user' ? 'rgba(99,102,241,0.25)' : 'rgba(255,255,255,0.07)'}`,
                      }}>
                        <MarkdownContent content={msg.content} />
                        <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', marginTop: '6px' }}>
                          {msg.timestamp.toLocaleTimeString()}
                        </div>
                      </div>
                    </div>
                  ))}
                  {isSending && (
                    <div style={{ display: 'flex', gap: '10px', marginBottom: '16px' }}>
                      <div style={{ width: '30px', height: '30px', borderRadius: '8px', background: 'rgba(16,185,129,0.15)', color: '#34d399', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        <Bot size={14} />
                      </div>
                      <div style={{ padding: '12px 16px', borderRadius: '4px 12px 12px 12px', background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.07)' }}>
                        <div style={{ display: 'flex', gap: '4px', alignItems: 'center' }}>
                          {[0,1,2].map(i => (
                            <div key={i} style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#818cf8', animation: `bounce 1.2s ease-in-out ${i*0.2}s infinite` }} />
                          ))}
                        </div>
                      </div>
                    </div>
                  )}
                  <div ref={chatEndRef} />
                </div>

                {/* Chat input */}
                <div style={{
                  padding: '12px 16px',
                  borderTop: '1px solid var(--border-subtle)',
                  background: 'rgba(9,13,22,0.8)',
                  flexShrink: 0,
                }}>
                  {/* Specialized Agent Routing Selector */}
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    marginBottom: '8px',
                    gap: '8px',
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      <Brain size={12} style={{ color: '#818cf8' }} />
                      <span>Direct Agent Routing:</span>
                    </div>
                    <select
                      value={selectedAgent}
                      onChange={e => setSelectedAgent(e.target.value)}
                      style={{
                        background: 'rgba(15, 23, 42, 0.8)',
                        border: '1px solid rgba(99, 102, 241, 0.3)',
                        borderRadius: '6px',
                        color: selectedAgent ? '#a5b4fc' : 'var(--text-secondary)',
                        fontSize: '0.75rem',
                        padding: '3px 8px',
                        outline: 'none',
                        cursor: 'pointer',
                        maxWidth: '300px',
                      }}
                    >
                      <option value="">⚡ Auto-Coordinator (Intent Router)</option>
                      {availableAgents.map(ag => (
                        <option key={ag.id} value={ag.id}>
                          🤖 {ag.name} ({ag.role})
                        </option>
                      ))}
                    </select>
                  </div>

                  <div style={{ display: 'flex', gap: '8px', alignItems: 'flex-end' }}>
                    <textarea
                      value={input}
                      onChange={e => setInput(e.target.value)}
                      onKeyDown={e => {
                        if (e.key === 'Enter' && !e.shiftKey) {
                          e.preventDefault()
                          sendMessage()
                        }
                      }}
                      placeholder="Ask about your data, request analysis, or get ML recommendations… (Enter to send)"
                      rows={2}
                      className="form-input"
                      style={{ flex: 1, resize: 'none', lineHeight: 1.5, fontSize: '0.875rem' }}
                      disabled={isSending}
                    />
                    <button
                      className="btn btn-primary"
                      style={{ padding: '10px 14px', alignSelf: 'flex-end' }}
                      onClick={sendMessage}
                      disabled={isSending || !input.trim()}
                    >
                      {isSending ? <Loader2 size={15} style={{ animation: 'spin 1s linear infinite' }} /> : <Send size={15} />}
                    </button>
                  </div>
                </div>
              </>
            )}

            {/* PIPELINE TAB */}
            {activeTab === 'pipeline' && (
              <div style={{ flex: 1, overflow: 'auto', padding: '20px' }}>
                {pipelineCode ? (
                  <>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
                      <div>
                        <h2 style={{ marginBottom: '4px' }}>Generated sklearn Pipeline</h2>
                        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                          Production-ready Python code for your ML preprocessing pipeline
                        </p>
                      </div>
                      <button
                        className="btn btn-secondary btn-sm"
                        onClick={() => {
                          const blob = new Blob([pipelineCode], { type: 'text/plain' })
                          const url = URL.createObjectURL(blob)
                          const a = document.createElement('a')
                          a.href = url
                          a.download = 'datawise_pipeline.py'
                          a.click()
                        }}
                      >
                        <Download size={13} />
                        Download .py
                      </button>
                    </div>
                    <pre style={{
                      background: 'rgba(0,0,0,0.4)',
                      border: '1px solid var(--border-subtle)',
                      borderRadius: '10px',
                      padding: '20px',
                      fontSize: '0.8rem',
                      fontFamily: "'Fira Code', 'JetBrains Mono', monospace",
                      color: '#e2e8f0',
                      overflow: 'auto',
                      lineHeight: 1.7,
                      whiteSpace: 'pre-wrap',
                    }}>
                      {pipelineCode}
                    </pre>
                  </>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', gap: '16px', color: 'var(--text-muted)', textAlign: 'center' }}>
                    <Code2 size={48} style={{ opacity: 0.3 }} />
                    <div>
                      <p style={{ marginBottom: '8px', fontWeight: 600 }}>No pipeline generated yet</p>
                      <p style={{ fontSize: '0.85rem' }}>Run the full analysis to automatically generate a production-ready sklearn pipeline.</p>
                    </div>
                    <button className="btn btn-primary" onClick={runWorkflow} disabled={isRunningWorkflow || !uploadedFile}>
                      <Play size={14} />
                      Run Analysis
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* RESULTS TAB */}
            {activeTab === 'results' && (
              <div style={{ flex: 1, overflow: 'auto', padding: '20px' }}>
                {workflowResult ? (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                    {/* Readiness score card */}
                    {readinessScore !== null && (
                      <div className="glass-card" style={{ padding: '20px' }}>
                        <h3 style={{ marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <TrendingUp size={18} color="#818cf8" />
                          ML Readiness Assessment
                        </h3>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
                          <div style={{
                            width: '80px',
                            height: '80px',
                            borderRadius: '50%',
                            background: `conic-gradient(${readinessScore >= 80 ? '#34d399' : readinessScore >= 50 ? '#fbbf24' : '#f87171'} ${readinessScore * 3.6}deg, rgba(255,255,255,0.05) 0)`,
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            flexShrink: 0,
                          }}>
                            <div style={{ width: '64px', height: '64px', borderRadius: '50%', background: 'var(--bg-card)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column' }}>
                              <span style={{ fontSize: '1.2rem', fontWeight: 800, color: readinessScore >= 80 ? '#34d399' : readinessScore >= 50 ? '#fbbf24' : '#f87171' }}>{readinessScore}</span>
                              <span style={{ fontSize: '0.55rem', color: 'var(--text-muted)' }}>/ 100</span>
                            </div>
                          </div>
                          <div>
                            <div style={{ fontWeight: 700, marginBottom: '4px', color: readinessScore >= 80 ? '#34d399' : readinessScore >= 50 ? '#fbbf24' : '#f87171' }}>
                              {readinessScore >= 80 ? 'Ready for Baseline Training' : readinessScore >= 50 ? 'Needs Preprocessing' : 'Not Ready — Critical Issues'}
                            </div>
                            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                              {readinessScore >= 80
                                ? 'Your dataset is clean and well-structured. A baseline model can be trained now.'
                                : readinessScore >= 50
                                ? 'Address the flagged issues and apply the preprocessing pipeline before training.'
                                : 'Significant data quality problems must be resolved before any model training.'}
                            </p>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Completed stages */}
                    {Boolean((workflowResult.completed_stages as string[] | undefined)?.length) && (
                      <div className="glass-card" style={{ padding: '20px' }}>
                        <h3 style={{ marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <CheckCircle2 size={18} color="#34d399" />
                          Completed Analysis Stages
                        </h3>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                          {(workflowResult.completed_stages as string[]).map(stage => (
                            <span key={stage} style={{
                              padding: '4px 10px',
                              borderRadius: '6px',
                              background: 'rgba(16,185,129,0.1)',
                              border: '1px solid rgba(16,185,129,0.2)',
                              color: '#34d399',
                              fontSize: '0.75rem',
                              fontWeight: 600,
                            }}>
                              ✓ {stage}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Errors */}
                    {Boolean((workflowResult.errors as unknown[] | undefined)?.length) && (
                      <div className="glass-card" style={{ padding: '20px', borderColor: 'rgba(239,68,68,0.2)', background: 'rgba(239,68,68,0.03)' }}>
                        <h3 style={{ marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px', color: '#f87171' }}>
                          <AlertTriangle size={18} />
                          Issues Encountered
                        </h3>
                        {(workflowResult.errors as Array<{stage: string; error: string}>).map((e, i) => (
                          <div key={i} style={{ fontSize: '0.8rem', padding: '6px 10px', borderRadius: '6px', background: 'rgba(239,68,68,0.1)', marginBottom: '4px', color: '#fca5a5' }}>
                            <strong>{e.stage}:</strong> {e.error}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', gap: '16px', color: 'var(--text-muted)', textAlign: 'center' }}>
                    <Brain size={48} style={{ opacity: 0.3 }} />
                    <div>
                      <p style={{ marginBottom: '8px', fontWeight: 600 }}>No results yet</p>
                      <p style={{ fontSize: '0.85rem' }}>Upload a dataset and run the analysis pipeline to see ML recommendations and readiness scores.</p>
                    </div>
                  </div>
                )}
              </div>
            )}


            {/* AUTOML & MODELS TAB */}
            {activeTab === 'models' && (
              <div style={{ flex: 1, overflow: 'auto', padding: '20px' }}>
                <AutoMLDashboard
                  sessionId={sessionId!}
                  trainingData={trainingData}
                  onTrainingComplete={(data) => {
                    setTrainingData(data);
                    addSystemMessage(`🏆 **AutoML training complete!** Selected champion model: **${data.selected_final_model}** (${data.primary_metric} optimized).`);
                  }}
                  datasetDomain={datasetDomain}
                  predictionObjective={predictionObjective}
                  targetColumn={(session as any)?.target_column}
                  taskType={(session as any)?.task_type}
                />
              </div>
            )}

            {/* DOWNLOAD CENTER TAB */}
            {activeTab === 'downloads' && (
              <div style={{ flex: 1, overflow: 'auto', padding: '20px' }}>
                <DownloadCenter sessionId={sessionId!} />
              </div>
            )}
          </div>
        </main>


        {/* ── Right Panel: Upload ── */}
        <aside style={{
          width: isUploadVisible ? '280px' : '48px',
          flexShrink: 0,
          borderLeft: '1px solid var(--border-subtle)',
          background: 'rgba(9, 13, 22, 0.6)',
          transition: 'width 0.25s ease',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
        }}>
          {/* Toggle */}
          <button
            onClick={() => setIsUploadVisible(v => !v)}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: isUploadVisible ? 'flex-end' : 'center',
              padding: '12px',
              background: 'none',
              border: 'none',
              borderBottom: '1px solid var(--border-subtle)',
              cursor: 'pointer',
              color: 'var(--text-muted)',
              flexShrink: 0,
            }}
          >
            {isUploadVisible ? <ChevronDown size={16} /> : <Upload size={16} />}
          </button>

          {isUploadVisible && (
            <div style={{ padding: '16px', overflowY: 'auto', flex: 1 }}>
              <div style={{ fontSize: '0.7rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text-muted)', marginBottom: '12px' }}>
                Dataset Upload
              </div>

              {uploadedFile ? (
                <div style={{
                  padding: '12px',
                  borderRadius: '8px',
                  background: 'rgba(16,185,129,0.08)',
                  border: '1px solid rgba(16,185,129,0.2)',
                  marginBottom: '12px',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                    <CheckCircle2 size={14} color="#34d399" />
                    <span style={{ fontSize: '0.8rem', fontWeight: 600, color: '#34d399' }}>Uploaded</span>
                  </div>
                  <p style={{ fontSize: '0.75rem', color: '#94a3b8', wordBreak: 'break-all' }}>{uploadedFile}</p>
                </div>
              ) : (
                <div
                  onDragOver={e => { e.preventDefault(); setIsDragging(true) }}
                  onDragLeave={() => setIsDragging(false)}
                  onDrop={handleDrop}
                  onClick={() => fileInputRef.current?.click()}
                  style={{
                    border: `2px dashed ${isDragging ? 'rgba(99,102,241,0.7)' : 'rgba(255,255,255,0.12)'}`,
                    borderRadius: '10px',
                    padding: '24px 16px',
                    textAlign: 'center',
                    cursor: 'pointer',
                    background: isDragging ? 'rgba(99,102,241,0.06)' : 'rgba(255,255,255,0.02)',
                    transition: 'all 0.2s',
                    marginBottom: '12px',
                  }}
                >
                  {isUploading ? (
                    <>
                      <Loader2 size={28} color="#818cf8" style={{ animation: 'spin 1s linear infinite', margin: '0 auto 8px' }} />
                      <p style={{ fontSize: '0.75rem', color: '#818cf8', marginBottom: '6px' }}>Uploading…</p>
                      <div style={{ height: '4px', background: 'rgba(255,255,255,0.08)', borderRadius: '2px', overflow: 'hidden' }}>
                        <div style={{ height: '100%', width: `${uploadProgress}%`, background: 'var(--primary-gradient)', transition: 'width 0.2s', borderRadius: '2px' }} />
                      </div>
                    </>
                  ) : (
                    <>
                      <Upload size={28} color="#818cf8" style={{ margin: '0 auto 8px', opacity: 0.7 }} />
                      <p style={{ fontSize: '0.75rem', color: '#94a3b8', marginBottom: '4px' }}>Drop file or click</p>
                      <p style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>CSV · XLSX · XLS · JSON</p>
                      <p style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>Max 100 MB</p>
                    </>
                  )}
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".csv,.xlsx,.xls,.json"
                    style={{ display: 'none' }}
                    onChange={e => { const f = e.target.files?.[0]; if (f) handleFileUpload(f) }}
                  />
                </div>
              )}

              {/* Quick action buttons */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                <button
                  className="btn btn-primary"
                  style={{ justifyContent: 'center', fontSize: '0.8rem' }}
                  onClick={runWorkflow}
                  disabled={isRunningWorkflow || !uploadedFile}
                >
                  {isRunningWorkflow
                    ? <><Loader2 size={12} style={{ animation: 'spin 1s linear infinite' }} />Running…</>
                    : <><Play size={12} />Run Full Analysis</>
                  }
                </button>

                {uploadedFile && (
                  <button
                    className="btn btn-secondary"
                    style={{ justifyContent: 'center', fontSize: '0.8rem' }}
                    onClick={() => { setUploadedFile(null); setCurrentStage('INGEST') }}
                  >
                    <RefreshCw size={12} />
                    Replace File
                  </button>
                )}
              </div>

              {/* Tips */}
              <div style={{ marginTop: '20px', padding: '12px', borderRadius: '8px', background: 'rgba(99,102,241,0.06)', border: '1px solid rgba(99,102,241,0.12)' }}>
                <p style={{ fontSize: '0.7rem', fontWeight: 600, color: '#818cf8', marginBottom: '8px' }}>💡 Tips</p>
                <ul style={{ fontSize: '0.7rem', color: 'var(--text-muted)', paddingLeft: '14px', lineHeight: 1.6 }}>
                  <li>Works best with tabular datasets</li>
                  <li>Include a header row</li>
                  <li>UTF-8 encoding preferred</li>
                  <li>Ask me anything after upload!</li>
                </ul>
              </div>
            </div>
          )}
        </aside>
      </div>

      {/* ── Domain & Context Modal ── */}
      <ContextModal
        sessionId={sessionId!}
        initialDomain={datasetDomain}
        initialObjective={predictionObjective}
        initialMode={executionMode}
        isOpen={isContextModalOpen}
        onClose={() => setIsContextModalOpen(false)}
        onSaved={({ datasetDomain: d, predictionObjective: o, executionMode: m }) => {
          setDatasetDomain(d);
          setPredictionObjective(o);
          setExecutionMode(m);
          addSystemMessage(
            `🌐 **Context updated:** Domain = \`${d || 'General'}\`, Objective = \`${o || 'Supervised Learning'}\`, Mode = \`${m}\`.\n\n` +
            `The agent will now apply context-aware outlier reasoning and task-tailored metric optimization.`
          );
        }}
      />

      <style>{`
        @keyframes bounce {
          0%, 60%, 100% { transform: translateY(0); }
          30% { transform: translateY(-4px); }
        }
      `}</style>
    </div>

  )
}
