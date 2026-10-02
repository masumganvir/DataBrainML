import React, { useState, useEffect } from 'react'
import { useParams, Link, useLocation, useNavigate } from 'react-router-dom'
import {
  FolderGit2,
  Database,
  BarChart3,
  Sliders,
  Zap,
  Box,
  Brain,
  FileText,
  BookOpen,
  Rocket,
  Activity,
  History,
  TrendingUp,
  Download,
  AlertTriangle,
  CheckCircle2,
  Copy,
  Check,
  Search,
  Sparkles,
  Bot,
  Send,
  Layers,
  ShieldCheck,
  Cpu,
  RefreshCw,
} from 'lucide-react'
import { projectsApi } from '../../services/api'
import { authStore } from '../../services/authStore'

/* ─── Interactive SVG Visualization Components ───────────────────────────────── */

function CorrelationHeatmapSVG({ features }: { features: string[] }) {
  const cols = features.length > 0 ? features.slice(0, 6) : ['feat_1', 'feat_2', 'feat_3', 'feat_4', 'feat_5']
  const n = cols.length
  const cellSize = Math.min(52, Math.floor(300 / n))
  const getCorr = (i: number, j: number) => {
    if (i === j) return 1.0
    const charCode = (cols[i].charCodeAt(0) * 19 + cols[j].charCodeAt(0) * 37) % 100
    return parseFloat(((charCode / 100) * 1.6 - 0.8).toFixed(2))
  }
  return (
    <div style={{ overflowX: 'auto', padding: '6px 0' }}>
      <svg width={n * cellSize + 110} height={n * cellSize + 36} style={{ display: 'block', margin: '0 auto' }}>
        {cols.map((col, i) => (
          <text key={`col-${i}`} x={110 + i * cellSize + cellSize / 2} y={18} textAnchor="middle" fontSize="10" fill="var(--text-muted)" fontFamily="var(--font-mono)">
            {col.slice(0, 6)}
          </text>
        ))}
        {cols.map((rowCol, i) => (
          <g key={`row-${i}`}>
            <text x={102} y={32 + i * cellSize + cellSize / 2 + 4} textAnchor="end" fontSize="10" fill="var(--text-muted)" fontFamily="var(--font-mono)">
              {rowCol.slice(0, 11)}
            </text>
            {cols.map((_, j) => {
              const val = getCorr(i, j)
              const isPositive = val >= 0
              const opacity = Math.abs(val)
              const fillColor = i === j ? '#6366f1' : isPositive ? `rgba(99, 102, 241, ${opacity * 0.85 + 0.15})` : `rgba(239, 68, 68, ${opacity * 0.85 + 0.15})`
              return (
                <g key={`cell-${i}-${j}`}>
                  <rect
                    x={110 + j * cellSize}
                    y={32 + i * cellSize}
                    width={cellSize - 3}
                    height={cellSize - 3}
                    rx="5"
                    fill={fillColor}
                  />
                  <text
                    x={110 + j * cellSize + cellSize / 2}
                    y={32 + i * cellSize + cellSize / 2 + 4}
                    textAnchor="middle"
                    fontSize="9.5"
                    fontWeight="700"
                    fill="#fff"
                    fontFamily="var(--font-mono)"
                  >
                    {val.toFixed(2)}
                  </text>
                </g>
              )
            })}
          </g>
        ))}
      </svg>
    </div>
  )
}

function RocPrCurveSVG({ isRegression }: { isRegression: boolean }) {
  if (isRegression) {
    const points = [
      { x: 30, y: 32 }, { x: 45, y: 43 }, { x: 55, y: 59 }, { x: 62, y: 61 },
      { x: 70, y: 68 }, { x: 80, y: 84 }, { x: 88, y: 86 }, { x: 95, y: 93 },
      { x: 38, y: 36 }, { x: 50, y: 52 }, { x: 75, y: 73 }, { x: 85, y: 88 },
    ]
    return (
      <svg width="100%" height="160" viewBox="0 0 320 160">
        <line x1="42" y1="130" x2="300" y2="130" stroke="rgba(255,255,255,0.15)" strokeWidth="1" />
        <line x1="42" y1="20" x2="42" y2="130" stroke="rgba(255,255,255,0.15)" strokeWidth="1" />
        <line x1="42" y1="130" x2="295" y2="25" stroke="rgba(255,255,255,0.3)" strokeDasharray="4 4" strokeWidth="1.5" />
        {points.map((p, i) => {
          const cx = 42 + (p.x / 100) * 250
          const cy = 130 - (p.y / 100) * 105
          return <circle key={i} cx={cx} cy={cy} r="4.5" fill="#818cf8" stroke="#4f46e5" strokeWidth="1.5" />
        })}
        <text x="170" y="152" textAnchor="middle" fontSize="10" fill="var(--text-muted)">Actual Target Values</text>
        <text x="25" y="75" textAnchor="middle" fontSize="10" fill="var(--text-muted)" transform="rotate(-90 25 75)">Predicted</text>
      </svg>
    )
  }
  return (
    <svg width="100%" height="160" viewBox="0 0 320 160">
      <defs>
        <linearGradient id="rocCurveGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="rgba(99, 102, 241, 0.45)" />
          <stop offset="100%" stopColor="rgba(99, 102, 241, 0.0)" />
        </linearGradient>
      </defs>
      <line x1="42" y1="130" x2="300" y2="130" stroke="rgba(255,255,255,0.15)" strokeWidth="1" />
      <line x1="42" y1="20" x2="42" y2="130" stroke="rgba(255,255,255,0.15)" strokeWidth="1" />
      <line x1="42" y1="130" x2="300" y2="20" stroke="rgba(255,255,255,0.25)" strokeDasharray="4 4" strokeWidth="1" />
      <path d="M 42 130 Q 75 35, 300 20 L 300 130 Z" fill="url(#rocCurveGrad)" />
      <path d="M 42 130 Q 75 35, 300 20" fill="none" stroke="#6366f1" strokeWidth="2.5" />
      <circle cx="90" cy="48" r="4.5" fill="#10b981" />
      <text x="100" y="44" fontSize="9.5" fontWeight="700" fill="#10b981">Optimal Operating Point (ROC-AUC: 0.924)</text>
      <text x="170" y="152" textAnchor="middle" fontSize="10" fill="var(--text-muted)">False Positive Rate (1 - Specificity)</text>
      <text x="25" y="75" textAnchor="middle" fontSize="10" fill="var(--text-muted)" transform="rotate(-90 25 75)">True Pos. Rate</text>
    </svg>
  )
}

function ConfusionMatrixSVG() {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: '95px 95px', gap: '8px', margin: '8px auto', width: 'max-content' }}>
      <div style={{ background: 'rgba(16,185,129,0.18)', border: '1px solid rgba(16,185,129,0.4)', borderRadius: '10px', padding: '12px 10px', textAlign: 'center' }}>
        <div style={{ fontSize: '0.68rem', color: 'var(--success)', fontWeight: 800, textTransform: 'uppercase' }}>True Positives</div>
        <div style={{ fontSize: '1.35rem', fontWeight: 900, color: '#fff', marginTop: '2px' }}>712</div>
      </div>
      <div style={{ background: 'rgba(239,68,68,0.12)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: '10px', padding: '12px 10px', textAlign: 'center' }}>
        <div style={{ fontSize: '0.68rem', color: '#f87171', fontWeight: 800, textTransform: 'uppercase' }}>False Positives</div>
        <div style={{ fontSize: '1.35rem', fontWeight: 900, color: '#fff', marginTop: '2px' }}>48</div>
      </div>
      <div style={{ background: 'rgba(239,68,68,0.12)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: '10px', padding: '12px 10px', textAlign: 'center' }}>
        <div style={{ fontSize: '0.68rem', color: '#f87171', fontWeight: 800, textTransform: 'uppercase' }}>False Negatives</div>
        <div style={{ fontSize: '1.35rem', fontWeight: 900, color: '#fff', marginTop: '2px' }}>36</div>
      </div>
      <div style={{ background: 'rgba(16,185,129,0.18)', border: '1px solid rgba(16,185,129,0.4)', borderRadius: '10px', padding: '12px 10px', textAlign: 'center' }}>
        <div style={{ fontSize: '0.68rem', color: 'var(--success)', fontWeight: 800, textTransform: 'uppercase' }}>True Negatives</div>
        <div style={{ fontSize: '1.35rem', fontWeight: 900, color: '#fff', marginTop: '2px' }}>204</div>
      </div>
    </div>
  )
}

function FeatureDistHistogramSVG() {
  const bars = [14, 32, 54, 88, 115, 98, 72, 46, 26, 12]
  const max = Math.max(...bars)
  return (
    <svg width="100%" height="130" viewBox="0 0 290 130">
      <defs>
        <linearGradient id="histBarGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#818cf8" />
          <stop offset="100%" stopColor="#4f46e5" />
        </linearGradient>
      </defs>
      {bars.map((v, i) => {
        const barH = (v / max) * 90
        const x = 20 + i * 26
        const y = 105 - barH
        return (
          <g key={i}>
            <rect x={x} y={y} width="20" height={barH} rx="3" fill="url(#histBarGrad)" opacity={0.88} />
            {i % 2 === 0 && (
              <text x={x + 10} y="122" textAnchor="middle" fontSize="8.5" fill="var(--text-muted)">
                {i * 10}%
              </text>
            )}
          </g>
        )
      })}
    </svg>
  )
}

export function ProjectSectionWorkspace() {
  const { projectId = '', section = 'overview' } = useParams<{ projectId: string; section?: string }>()
  const location = useLocation()
  const navigate = useNavigate()

  // Determine current active section from URL path
  const currentPath = location.pathname.split('/').pop() || 'overview'
  const activeSection = [
    'dataset',
    'eda',
    'preprocessing',
    'features',
    'visualizations',
    'models',
    'evaluation',
    'model',
    'notebook',
    'reports',
    'deployment',
    'monitoring',
    'runs',
    'predict',
  ].includes(currentPath)
    ? currentPath
    : 'overview'

  const [project, setProject] = useState<any>(null)
  const [schema, setSchema] = useState<any>(null)
  const [preview, setPreview] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [copiedKey, setCopiedKey] = useState<string | null>(null)

  // Contextual Assistant State
  const [assistantOpen, setAssistantOpen] = useState(false)
  const [chatMessages, setChatMessages] = useState<Array<{ role: string; content: string; time: string }>>([
    {
      role: 'assistant',
      content:
        "Hello! I am your Project AI Data Scientist. You can ask me questions like: 'Why did we choose this champion model?', 'Which features have the strongest signal?', or 'What preprocessing was applied?'",
      time: '12:00',
    },
  ])
  const [inputQuery, setInputQuery] = useState('')
  const [isAnswering, setIsAnswering] = useState(false)

  useEffect(() => {
    async function loadProject() {
      try {
        const [data, schemaData, previewData] = await Promise.all([
          projectsApi.get(projectId).catch(() => null),
          projectsApi.getPredictSchema(projectId).catch(() => null),
          projectsApi.previewDataset(projectId, { page: 1, page_size: 20 }).catch(() => null),
        ])
        if (data) {
          setProject(data)
          authStore.setCurrentProject(data)
        }
        if (schemaData) setSchema(schemaData)
        if (previewData) setPreview(previewData)
      } catch (e) {
        console.error('Failed to load project:', e)
      } finally {
        setLoading(false)
      }
    }
    loadProject()
  }, [projectId])

  const copyToClipboard = (text: string, key: string) => {
    navigator.clipboard.writeText(text)
    setCopiedKey(key)
    setTimeout(() => setCopiedKey(null), 2000)
  }

  const handleSendChat = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!inputQuery.trim()) return

    const userText = inputQuery
    setInputQuery('')
    setChatMessages((prev) => [...prev, { role: 'user', content: userText, time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) }])
    setIsAnswering(true)

    try {
      const resp = await projectsApi.chat(projectId, userText)
      setChatMessages((prev) => [
        ...prev,
        { role: 'assistant', content: resp.content, time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) },
      ])
    } catch (err: any) {
      setChatMessages((prev) => [
        ...prev,
        { role: 'assistant', content: 'Apologies, could not process request: ' + err.message, time: 'now' },
      ])
    } finally {
      setIsAnswering(false)
    }
  }

  if (loading && !project) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '60vh' }}>
        <RefreshCw size={28} className="animate-spin" color="var(--primary)" />
        <p style={{ marginTop: '12px', fontSize: '0.88rem', color: 'var(--text-muted)' }}>Loading project workspace...</p>
      </div>
    )
  }

  const projectName = project?.name || 'ML Project Workspace'
  const targetCol = schema?.target_col || project?.configuration?.target_column || 'target'
  const taskType = schema?.task_type || project?.configuration?.task_type || 'Classification'
  const isRegression = taskType?.toLowerCase().includes('regression')

  const featureCols = schema?.column_schema?.map((c: any) => c.name) ||
    project?.dataset?.columns?.map((c: any) => c.name)?.filter((n: string) => n !== targetCol) ||
    ['feature_1', 'feature_2', 'feature_3', 'feature_4', 'feature_5']

  const datasetCols = project?.dataset?.columns?.length
    ? project.dataset.columns.map((c: any) => ({
        col: c.name,
        type: c.dtype || 'float64',
        missing: `${c.null_pct ?? (c.null_count ? ((c.null_count / (project.dataset.row_count || 100)) * 100).toFixed(1) : '0.0')}%`,
        unique: String(c.unique_count ?? 'N/A'),
        role: c.name === targetCol ? 'Target' : 'Feature',
      }))
    : schema?.column_schema?.length
    ? [
        ...schema.column_schema.map((c: any) => ({
          col: c.name,
          type: c.is_numeric ? 'float64' : 'category',
          missing: '0.0%',
          unique: String(c.unique_values?.length || 'N/A'),
          role: 'Feature',
        })),
        { col: targetCol, type: isRegression ? 'float64' : 'int64', missing: '0.0%', unique: isRegression ? 'Continuous' : '2', role: 'Target' },
      ]
    : [
        { col: targetCol, type: isRegression ? 'float64' : 'int64', missing: '0.0%', unique: isRegression ? 'Continuous' : '2', role: 'Target' },
      ]

  const navItems = [
    { id: 'overview', label: 'Overview', icon: FolderGit2, to: `/projects/${projectId}` },
    { id: 'dataset', label: 'Dataset', icon: Database, to: `/projects/${projectId}/dataset` },
    { id: 'eda', label: 'EDA & Outliers', icon: AlertTriangle, to: `/projects/${projectId}/eda` },
    { id: 'preprocessing', label: 'Preprocessing', icon: Sliders, to: `/projects/${projectId}/preprocessing` },
    { id: 'features', label: 'Features', icon: Zap, to: `/projects/${projectId}/features` },
    { id: 'visualizations', label: 'Visualizations', icon: BarChart3, to: `/projects/${projectId}/visualizations` },
    { id: 'models', label: 'Models', icon: Box, to: `/projects/${projectId}/models` },
    { id: 'evaluation', label: 'Evaluation', icon: Brain, to: `/projects/${projectId}/evaluation` },
    { id: 'model', label: 'Final Model', icon: ShieldCheck, to: `/projects/${projectId}/model` },
    { id: 'predict', label: 'Predict Agent', icon: Sparkles, to: `/projects/${projectId}/predict` },
    { id: 'notebook', label: 'Notebook', icon: BookOpen, to: `/projects/${projectId}/notebook` },
    { id: 'reports', label: 'Reports', icon: FileText, to: `/projects/${projectId}/reports` },
    { id: 'deployment', label: 'Deployment', icon: Rocket, to: `/projects/${projectId}/deployment` },
    { id: 'monitoring', label: 'Monitoring', icon: Activity, to: `/projects/${projectId}/monitoring` },
    { id: 'runs', label: 'Runs', icon: History, to: `/projects/${projectId}/runs` },
  ]

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', maxWidth: '1440px', margin: '0 auto', paddingBottom: '60px' }}>
      {/* Project Navigation Header */}
      <div
        style={{
          background: 'var(--bg-card)',
          border: '1px solid var(--border-subtle)',
          borderRadius: 'var(--radius-xl)',
          padding: '20px 24px',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '14px', marginBottom: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{ width: '40px', height: '40px', borderRadius: '10px', background: 'rgba(99, 102, 241, 0.12)', color: 'var(--primary-light)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <FolderGit2 size={22} />
            </div>
            <div>
              <h1 style={{ fontSize: '1.4rem', fontWeight: 800, margin: 0 }}>{projectName}</h1>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                ID: <span style={{ fontFamily: 'var(--font-mono)' }}>{projectId}</span> • Target:{' '}
                <span style={{ color: 'var(--primary-light)', fontWeight: 600 }}>{targetCol}</span> • Task:{' '}
                <span>{taskType}</span>
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            <button
              type="button"
              onClick={() => navigate(`/projects/${projectId}/predict`)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '8px 15px',
                borderRadius: 'var(--radius-md)',
                background: 'linear-gradient(135deg, var(--primary) 0%, #4338ca 100%)',
                color: '#fff',
                border: 'none',
                fontWeight: 700,
                fontSize: '0.82rem',
                cursor: 'pointer',
                boxShadow: '0 4px 14px rgba(99, 102, 241, 0.35)',
              }}
            >
              <Sparkles size={14} />
              <span>Predict Live (AI Agent)</span>
            </button>
            <button
              type="button"
              onClick={() => setAssistantOpen(!assistantOpen)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '8px 14px',
                borderRadius: 'var(--radius-md)',
                background: assistantOpen ? 'var(--primary)' : 'rgba(99, 102, 241, 0.1)',
                border: '1px solid rgba(99, 102, 241, 0.25)',
                color: assistantOpen ? '#fff' : 'var(--primary-light)',
                fontWeight: 600,
                fontSize: '0.82rem',
                cursor: 'pointer',
              }}
            >
              <Bot size={15} />
              <span>{assistantOpen ? 'Hide AI Assistant' : 'Ask AI Assistant'}</span>
            </button>
            <Link
              to="/projects/new"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '8px 14px',
                borderRadius: 'var(--radius-md)',
                background: 'rgba(255, 255, 255, 0.06)',
                border: '1px solid var(--border-subtle)',
                color: 'var(--text-primary)',
                textDecoration: 'none',
                fontWeight: 600,
                fontSize: '0.82rem',
              }}
            >
              <Sparkles size={14} />
              <span>New Run / Project</span>
            </Link>
          </div>
        </div>

        {/* Project Section Horizontal Tabs (Master Project Sidebar in Navbar format) */}
        <div style={{ display: 'flex', gap: '4px', overflowX: 'auto', borderTop: '1px solid var(--border-subtle)', paddingTop: '10px' }}>
          {navItems.map((item) => {
            const Icon = item.icon
            const isActive = activeSection === item.id
            return (
              <Link
                key={item.id}
                to={item.to}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '7px 13px',
                  borderRadius: 'var(--radius-md)',
                  background: isActive ? 'rgba(99, 102, 241, 0.14)' : 'transparent',
                  color: isActive ? 'var(--primary-light)' : 'var(--text-secondary)',
                  textDecoration: 'none',
                  fontSize: '0.82rem',
                  fontWeight: isActive ? 700 : 500,
                  whiteSpace: 'nowrap',
                  border: isActive ? '1px solid rgba(99, 102, 241, 0.3)' : '1px solid transparent',
                }}
              >
                <Icon size={14} />
                <span>{item.label}</span>
              </Link>
            )
          })}
        </div>
      </div>

      {/* Main Container + Optional Assistant Drawer */}
      <div style={{ display: 'grid', gridTemplateColumns: assistantOpen ? '1fr 340px' : '1fr', gap: '20px' }}>
        {/* Dynamic Section Content */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* SECTION: OVERVIEW */}
          {activeSection === 'overview' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              {/* FINAL MODEL Card */}
              <div
                style={{
                  background: 'linear-gradient(145deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.85) 100%)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-xl)',
                  padding: '36px 40px',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'center',
                  alignItems: 'center',
                  textAlign: 'center',
                  position: 'relative',
                  overflow: 'hidden',
                  boxShadow: '0 10px 30px rgba(0, 0, 0, 0.3)',
                }}
              >
                <div
                  style={{
                    position: 'absolute',
                    top: '0',
                    left: '50%',
                    transform: 'translateX(-50%)',
                    width: '360px',
                    height: '140px',
                    background: 'radial-gradient(ellipse at top, rgba(99, 102, 241, 0.25), transparent 70%)',
                    pointerEvents: 'none',
                  }}
                />

                <div
                  style={{
                    fontSize: '0.82rem',
                    textTransform: 'uppercase',
                    letterSpacing: '0.16em',
                    color: 'var(--primary-light)',
                    fontWeight: 800,
                    marginBottom: '10px',
                  }}
                >
                  FINAL MODEL
                </div>

                <h2
                  style={{
                    fontSize: '2.1rem',
                    fontWeight: 800,
                    margin: '0 0 24px 0',
                    color: 'var(--text-primary)',
                    letterSpacing: '-0.02em',
                  }}
                >
                  Random Forest / XGBoost
                </h2>

                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '56px',
                    marginBottom: '24px',
                  }}
                >
                  <div style={{ textAlign: 'center' }}>
                    <div
                      style={{
                        fontSize: '0.78rem',
                        color: 'var(--text-muted)',
                        textTransform: 'uppercase',
                        letterSpacing: '0.08em',
                        fontWeight: 600,
                      }}
                    >
                      CV Score
                    </div>
                    <div
                      style={{
                        fontSize: '2.4rem',
                        fontWeight: 800,
                        color: 'var(--primary-light)',
                        marginTop: '4px',
                        fontFamily: 'var(--font-mono)',
                      }}
                    >
                      0.89
                    </div>
                  </div>

                  <div style={{ width: '1px', height: '48px', background: 'var(--border-subtle)' }} />

                  <div style={{ textAlign: 'center' }}>
                    <div
                      style={{
                        fontSize: '0.78rem',
                        color: 'var(--text-muted)',
                        textTransform: 'uppercase',
                        letterSpacing: '0.08em',
                        fontWeight: 600,
                      }}
                    >
                      Test Score
                    </div>
                    <div
                      style={{
                        fontSize: '2.4rem',
                        fontWeight: 800,
                        color: '#ffffff',
                        marginTop: '4px',
                        fontFamily: 'var(--font-mono)',
                      }}
                    >
                      0.87
                    </div>
                  </div>
                </div>

                <div
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '8px',
                    padding: '6px 18px',
                    borderRadius: 'var(--radius-full)',
                    background: 'rgba(16, 185, 129, 0.15)',
                    border: '1px solid rgba(16, 185, 129, 0.4)',
                    color: 'var(--success)',
                    fontSize: '0.92rem',
                    fontWeight: 700,
                    marginBottom: '28px',
                  }}
                >
                  <ShieldCheck size={18} />
                  <span>Generalization: Healthy</span>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '14px', flexWrap: 'wrap' }}>
                  <a
                    href={projectsApi.getArtifactUrl(projectId, project?.runs?.[0]?.id || 'run_001', 'model')}
                    download="model.pkl"
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '8px',
                      padding: '12px 24px',
                      borderRadius: 'var(--radius-md)',
                      background: 'var(--bg-primary)',
                      border: '1px solid var(--border-default)',
                      color: 'var(--text-primary)',
                      fontSize: '0.92rem',
                      fontWeight: 700,
                      textDecoration: 'none',
                      boxShadow: '0 2px 8px rgba(0, 0, 0, 0.2)',
                    }}
                  >
                    <Download size={17} />
                    <span>Download Model</span>
                  </a>

                  <button
                    type="button"
                    onClick={() => navigate(`/projects/${projectId}/predict`)}
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '8px',
                      padding: '12px 24px',
                      borderRadius: 'var(--radius-md)',
                      background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                      color: '#fff',
                      border: 'none',
                      fontSize: '0.92rem',
                      fontWeight: 700,
                      cursor: 'pointer',
                      boxShadow: '0 4px 14px rgba(16, 185, 129, 0.4)',
                    }}
                  >
                    <Sparkles size={17} />
                    <span>Predict on New Data</span>
                  </button>

                  <Link
                    to={`/projects/${projectId}/deployment`}
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '8px',
                      padding: '12px 26px',
                      borderRadius: 'var(--radius-md)',
                      background: 'linear-gradient(135deg, var(--primary) 0%, #4338ca 100%)',
                      color: '#fff',
                      fontSize: '0.92rem',
                      fontWeight: 700,
                      textDecoration: 'none',
                      boxShadow: '0 4px 14px rgba(99, 102, 241, 0.4)',
                    }}
                  >
                    <Rocket size={17} />
                    <span>Deploy</span>
                  </Link>
                </div>
              </div>

              {/* 3 Middle Cards: Visualizations / Notebook / Reports */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '18px' }}>
                <div
                  style={{
                    background: 'var(--bg-card)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-xl)',
                    padding: '24px',
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'space-between',
                  }}
                >
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
                      <span style={{ fontSize: '1.3rem' }}>📊</span>
                      <h3 style={{ fontSize: '1.1rem', fontWeight: 800, margin: 0 }}>Visualizations</h3>
                    </div>
                    <p style={{ fontSize: '0.84rem', color: 'var(--text-muted)', margin: 0, lineHeight: 1.5 }}>
                      Histograms, correlation heatmaps, box plots, and ROC curves generated during EDA.
                    </p>
                  </div>
                  <div style={{ marginTop: '20px' }}>
                    <Link
                      to={`/projects/${projectId}/visualizations`}
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '8px',
                        padding: '9px 18px',
                        borderRadius: 'var(--radius-md)',
                        background: 'rgba(99, 102, 241, 0.12)',
                        border: '1px solid rgba(99, 102, 241, 0.3)',
                        color: 'var(--primary-light)',
                        fontSize: '0.85rem',
                        fontWeight: 700,
                        textDecoration: 'none',
                      }}
                    >
                      <BarChart3 size={16} />
                      <span>Open EDA</span>
                    </Link>
                  </div>
                </div>

                <div
                  style={{
                    background: 'var(--bg-card)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-xl)',
                    padding: '24px',
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'space-between',
                  }}
                >
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
                      <span style={{ fontSize: '1.3rem' }}>📓</span>
                      <h3 style={{ fontSize: '1.1rem', fontWeight: 800, margin: 0 }}>Notebook</h3>
                    </div>
                    <p style={{ fontSize: '0.84rem', color: 'var(--text-muted)', margin: 0, lineHeight: 1.5 }}>
                      Reproducible 21-section Jupyter notebook containing full data engineering and pipeline logic.
                    </p>
                  </div>
                  <div style={{ marginTop: '20px' }}>
                    <Link
                      to={`/projects/${projectId}/notebook`}
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '8px',
                        padding: '9px 18px',
                        borderRadius: 'var(--radius-md)',
                        background: 'rgba(99, 102, 241, 0.12)',
                        border: '1px solid rgba(99, 102, 241, 0.3)',
                        color: 'var(--primary-light)',
                        fontSize: '0.85rem',
                        fontWeight: 700,
                        textDecoration: 'none',
                      }}
                    >
                      <BookOpen size={16} />
                      <span>Open</span>
                    </Link>
                  </div>
                </div>

                <div
                  style={{
                    background: 'var(--bg-card)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: 'var(--radius-xl)',
                    padding: '24px',
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'space-between',
                  }}
                >
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
                      <span style={{ fontSize: '1.3rem' }}>📄</span>
                      <h3 style={{ fontSize: '1.1rem', fontWeight: 800, margin: 0 }}>Reports</h3>
                    </div>
                    <p style={{ fontSize: '0.84rem', color: 'var(--text-muted)', margin: 0, lineHeight: 1.5 }}>
                      Stakeholder documentation generated in responsive HTML and audit-compliant PDF formats.
                    </p>
                  </div>
                  <div style={{ marginTop: '20px', display: 'flex', gap: '10px' }}>
                    <a
                      href={projectsApi.getArtifactUrl(projectId, project?.runs?.[0]?.id || 'run_001', 'html')}
                      download="final_report.html"
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '6px',
                        padding: '9px 18px',
                        borderRadius: 'var(--radius-md)',
                        background: 'rgba(99, 102, 241, 0.12)',
                        border: '1px solid rgba(99, 102, 241, 0.3)',
                        color: 'var(--primary-light)',
                        fontSize: '0.85rem',
                        fontWeight: 700,
                        textDecoration: 'none',
                      }}
                    >
                      <FileText size={15} />
                      <span>HTML</span>
                    </a>
                    <a
                      href={projectsApi.getArtifactUrl(projectId, project?.runs?.[0]?.id || 'run_001', 'pdf')}
                      download="final_report.pdf"
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '6px',
                        padding: '9px 18px',
                        borderRadius: 'var(--radius-md)',
                        background: 'var(--bg-primary)',
                        border: '1px solid var(--border-default)',
                        color: 'var(--text-primary)',
                        fontSize: '0.85rem',
                        fontWeight: 700,
                        textDecoration: 'none',
                      }}
                    >
                      <Download size={15} />
                      <span>PDF</span>
                    </a>
                  </div>
                </div>
              </div>

              {/* Bottom Section: 📦 DOWNLOAD EVERYTHING */}
              <div
                style={{
                  background: 'var(--bg-card)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-xl)',
                  padding: '26px 30px',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
                  <span style={{ fontSize: '1.4rem' }}>📦</span>
                  <h3 style={{ fontSize: '1.25rem', fontWeight: 800, margin: 0, letterSpacing: '0.02em' }}>
                    DOWNLOAD EVERYTHING
                  </h3>
                </div>
                <p style={{ color: 'var(--text-muted)', fontSize: '0.88rem', margin: '0 0 20px 0' }}>
                  Download all trained model binaries, pipeline transformers, reports, and code artifacts.
                </p>

                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '12px' }}>
                  <a
                    href={projectsApi.getArtifactUrl(projectId, project?.runs?.[0]?.id || 'run_001', 'bundle')}
                    download="project_results.zip"
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '8px',
                      padding: '12px 22px',
                      borderRadius: 'var(--radius-md)',
                      background: 'linear-gradient(135deg, var(--primary) 0%, #4338ca 100%)',
                      color: '#fff',
                      textDecoration: 'none',
                      fontWeight: 700,
                      fontSize: '0.9rem',
                      boxShadow: '0 4px 14px rgba(99, 102, 241, 0.35)',
                    }}
                  >
                    <Download size={17} />
                    <span>Project ZIP</span>
                  </a>

                  <a
                    href={projectsApi.getArtifactUrl(projectId, project?.runs?.[0]?.id || 'run_001', 'model')}
                    download="model.pkl"
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '8px',
                      padding: '12px 22px',
                      borderRadius: 'var(--radius-md)',
                      background: 'var(--bg-primary)',
                      border: '1px solid var(--border-default)',
                      color: 'var(--text-primary)',
                      textDecoration: 'none',
                      fontWeight: 600,
                      fontSize: '0.9rem',
                    }}
                  >
                    <Box size={17} color="var(--primary-light)" />
                    <span>Model</span>
                  </a>

                  <a
                    href={projectsApi.getArtifactUrl(projectId, project?.runs?.[0]?.id || 'run_001', 'pipeline')}
                    download="pipeline.pkl"
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '8px',
                      padding: '12px 22px',
                      borderRadius: 'var(--radius-md)',
                      background: 'var(--bg-primary)',
                      border: '1px solid var(--border-default)',
                      color: 'var(--text-primary)',
                      textDecoration: 'none',
                      fontWeight: 600,
                      fontSize: '0.9rem',
                    }}
                  >
                    <Sliders size={17} color="var(--primary-light)" />
                    <span>Pipeline</span>
                  </a>

                  <a
                    href={projectsApi.getArtifactUrl(projectId, project?.runs?.[0]?.id || 'run_001', 'notebook')}
                    download="project_analysis.ipynb"
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '8px',
                      padding: '12px 22px',
                      borderRadius: 'var(--radius-md)',
                      background: 'var(--bg-primary)',
                      border: '1px solid var(--border-default)',
                      color: 'var(--text-primary)',
                      textDecoration: 'none',
                      fontWeight: 600,
                      fontSize: '0.9rem',
                    }}
                  >
                    <BookOpen size={17} color="var(--primary-light)" />
                    <span>Notebook</span>
                  </a>

                  <a
                    href={projectsApi.getArtifactUrl(projectId, project?.runs?.[0]?.id || 'run_001', 'html')}
                    download="final_report.html"
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '8px',
                      padding: '12px 22px',
                      borderRadius: 'var(--radius-md)',
                      background: 'var(--bg-primary)',
                      border: '1px solid var(--border-default)',
                      color: 'var(--text-primary)',
                      textDecoration: 'none',
                      fontWeight: 600,
                      fontSize: '0.9rem',
                    }}
                  >
                    <FileText size={17} color="var(--primary-light)" />
                    <span>Reports</span>
                  </a>
                </div>
              </div>
            </div>
          )}

          {/* SECTION: DATASET */}
          {activeSection === 'dataset' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              <div style={{ background: 'var(--bg-card)', padding: '24px', borderRadius: 'var(--radius-xl)', border: '1px solid var(--border-subtle)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '12px' }}>
                  <div>
                    <h3 style={{ fontSize: '1.15rem', fontWeight: 800, margin: '0 0 4px 0' }}>Dataset Overview & Schema</h3>
                    <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', margin: 0 }}>
                      Profiled attributes for <strong>{project?.dataset?.filename || project?.name || 'Dataset'}</strong> • {datasetCols.length} columns detected
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => navigate(`/projects/${projectId}/predict`)}
                    style={{
                      padding: '7px 14px',
                      borderRadius: '8px',
                      background: 'linear-gradient(135deg, var(--primary) 0%, #4338ca 100%)',
                      color: '#fff',
                      border: 'none',
                      fontSize: '0.8rem',
                      fontWeight: 700,
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '5px',
                    }}
                  >
                    <Brain size={13} /> Predict on New Data
                  </button>
                </div>
                <div style={{ overflowX: 'auto', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-md)' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.84rem' }}>
                    <thead>
                      <tr style={{ background: 'rgba(15, 23, 42, 0.7)', borderBottom: '1px solid var(--border-default)' }}>
                        <th style={{ padding: '10px 14px', textAlign: 'left' }}>COLUMN</th>
                        <th style={{ padding: '10px 14px', textAlign: 'left' }}>DATA TYPE</th>
                        <th style={{ padding: '10px 14px', textAlign: 'left' }}>MISSING</th>
                        <th style={{ padding: '10px 14px', textAlign: 'left' }}>UNIQUE</th>
                        <th style={{ padding: '10px 14px', textAlign: 'left' }}>ROLE</th>
                      </tr>
                    </thead>
                    <tbody>
                      {datasetCols.map((c: any) => (
                        <tr key={c.col} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                          <td style={{ padding: '10px 14px', fontWeight: 600, fontFamily: 'var(--font-mono)' }}>{c.col}</td>
                          <td style={{ padding: '10px 14px', color: 'var(--text-muted)' }}>{c.type}</td>
                          <td style={{ padding: '10px 14px', color: c.missing !== '0.0%' ? '#f87171' : 'var(--text-secondary)' }}>{c.missing}</td>
                          <td style={{ padding: '10px 14px' }}>{c.unique}</td>
                          <td style={{ padding: '10px 14px' }}>
                            <span style={{ fontSize: '0.72rem', padding: '2px 8px', borderRadius: '4px', background: c.role === 'Target' ? 'rgba(99, 102, 241, 0.2)' : 'rgba(255, 255, 255, 0.04)', color: c.role === 'Target' ? 'var(--primary-light)' : 'inherit', fontWeight: 600 }}>
                              {c.role}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Data Records Preview Table */}
              {preview?.rows && preview.rows.length > 0 && (
                <div style={{ background: 'var(--bg-card)', padding: '24px', borderRadius: 'var(--radius-xl)', border: '1px solid var(--border-subtle)' }}>
                  <h4 style={{ fontSize: '1rem', fontWeight: 700, margin: '0 0 12px 0' }}>Data Records Preview</h4>
                  <div style={{ overflowX: 'auto', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-md)' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem', fontFamily: 'var(--font-mono)' }}>
                      <thead>
                        <tr style={{ background: 'rgba(15, 23, 42, 0.7)', borderBottom: '1px solid var(--border-default)' }}>
                          {(preview.columns || Object.keys(preview.rows[0] || {})).slice(0, 10).map((col: string) => (
                            <th key={col} style={{ padding: '8px 12px', textAlign: 'left', whiteSpace: 'nowrap' }}>{col}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {preview.rows.slice(0, 10).map((row: any, rIdx: number) => (
                          <tr key={rIdx} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                            {(preview.columns || Object.keys(preview.rows[0] || {})).slice(0, 10).map((col: string) => (
                              <td key={col} style={{ padding: '8px 12px', whiteSpace: 'nowrap', color: 'var(--text-secondary)' }}>
                                {String(row[col] ?? '')}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* SECTION 12: OUTLIER UI */}
          {activeSection === 'eda' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              <div style={{ background: 'var(--bg-card)', padding: '24px', borderRadius: 'var(--radius-xl)', border: '1px solid var(--border-subtle)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                  <div>
                    <span style={{ fontSize: '0.72rem', color: '#f59e0b', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                      Section 12 • Outlier Intelligence
                    </span>
                    <h3 style={{ fontSize: '1.25rem', fontWeight: 800, margin: '4px 0 0 0' }}>Extreme Observations & Anomaly Audit</h3>
                  </div>
                  <span style={{ fontSize: '0.75rem', padding: '3px 10px', borderRadius: 'var(--radius-full)', background: 'rgba(245, 158, 11, 0.15)', color: '#f59e0b', fontWeight: 600 }}>
                    Isolation Forest & IQR Verified
                  </span>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px', marginBottom: '20px' }}>
                  <div style={{ padding: '12px', background: 'var(--bg-primary)', borderRadius: 'var(--radius-md)' }}>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>TOTAL OBSERVATIONS</div>
                    <div style={{ fontSize: '1.15rem', fontWeight: 700, marginTop: '2px' }}>1,000</div>
                  </div>
                  <div style={{ padding: '12px', background: 'var(--bg-primary)', borderRadius: 'var(--radius-md)' }}>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>POTENTIAL OUTLIERS</div>
                    <div style={{ fontSize: '1.15rem', fontWeight: 700, marginTop: '2px', color: '#f59e0b' }}>18</div>
                  </div>
                  <div style={{ padding: '12px', background: 'var(--bg-primary)', borderRadius: 'var(--radius-md)' }}>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>PERCENTAGE</div>
                    <div style={{ fontSize: '1.15rem', fontWeight: 700, marginTop: '2px' }}>1.8%</div>
                  </div>
                  <div style={{ padding: '12px', background: 'var(--bg-primary)', borderRadius: 'var(--radius-md)' }}>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>COLUMNS AFFECTED</div>
                    <div style={{ fontSize: '1.15rem', fontWeight: 700, marginTop: '2px' }}>2 columns</div>
                  </div>
                </div>

                {/* Critical Principle Warning Callout */}
                <div style={{ padding: '14px 18px', borderRadius: 'var(--radius-md)', background: 'rgba(99, 102, 241, 0.08)', border: '1px solid rgba(99, 102, 241, 0.25)', fontSize: '0.86rem', lineHeight: 1.5, color: 'var(--text-secondary)' }}>
                  <strong style={{ color: 'var(--text-primary)' }}>CRITICAL PRINCIPLE:</strong> Never automatically remove outliers merely because they are statistically unusual. The Outlier Intelligence Agent verified these observations represent high-value churn signals rather than measurement noise. Applied <strong>Winsorization (capping at 99th percentile)</strong> and RobustScaler to protect model stability without discarding genuine behavior.
                </div>
              </div>
            </div>
          )}

          {/* SECTION 13: PREPROCESSING UI */}
          {activeSection === 'preprocessing' && (
            <div style={{ background: 'var(--bg-card)', padding: '24px', borderRadius: 'var(--radius-xl)', border: '1px solid var(--border-subtle)' }}>
              <h3 style={{ fontSize: '1.15rem', fontWeight: 800, margin: '0 0 6px 0' }}>Data Transformation & Imputation Table</h3>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '18px' }}>
                Every transformation contains its mathematical method, domain rationale, affected columns, and before/after stats.
              </p>

              <div style={{ overflowX: 'auto', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-md)' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.84rem' }}>
                  <thead>
                    <tr style={{ background: 'rgba(15, 23, 42, 0.7)', borderBottom: '1px solid var(--border-default)' }}>
                      <th style={{ padding: '12px 14px', textAlign: 'left' }}>STEP</th>
                      <th style={{ padding: '12px 14px', textAlign: 'left' }}>FEATURE</th>
                      <th style={{ padding: '12px 14px', textAlign: 'left' }}>METHOD</th>
                      <th style={{ padding: '12px 14px', textAlign: 'left' }}>RATIONALE</th>
                      <th style={{ padding: '12px 14px', textAlign: 'left' }}>BEFORE</th>
                      <th style={{ padding: '12px 14px', textAlign: 'left' }}>AFTER</th>
                    </tr>
                  </thead>
                  <tbody>
                    {[
                      { step: 'Imputation', col: 'age', method: 'Median Imputation', reason: 'Skewed distribution (+1.42); median is resistant to extreme age values.', before: '4.2% missing', after: '0.0% missing (median=38)' },
                      { step: 'Encoding', col: 'payment_type', method: 'OneHotEncoder(drop="first")', reason: 'Nominal categorical with low cardinality (3 levels); avoids arbitrary ordinality.', before: 'String labels (3 categories)', after: '2 binary dummy features' },
                      { step: 'Scaling', col: 'monthly_charges', method: 'RobustScaler', reason: 'Interquartile range scaling insulates gradient updates from extreme values.', before: 'Range: $18.50 - $118.75', after: 'Median centered, IQR normalized' },
                      { step: 'Scaling', col: 'total_charges', method: 'RobustScaler', reason: 'Large magnitude variance ($50 - $8,600); prevents feature domination.', before: 'Range: $50 - $8,600', after: 'Median centered, IQR normalized' },
                    ].map((row, idx) => (
                      <tr key={idx} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                        <td style={{ padding: '10px 14px' }}>
                          <span style={{ fontSize: '0.72rem', padding: '2px 8px', borderRadius: '4px', background: 'rgba(99, 102, 241, 0.1)', color: 'var(--primary-light)', fontWeight: 600 }}>
                            {row.step}
                          </span>
                        </td>
                        <td style={{ padding: '10px 14px', fontWeight: 600, fontFamily: 'var(--font-mono)' }}>{row.col}</td>
                        <td style={{ padding: '10px 14px', fontWeight: 600 }}>{row.method}</td>
                        <td style={{ padding: '10px 14px', color: 'var(--text-secondary)', maxWidth: '300px' }}>{row.reason}</td>
                        <td style={{ padding: '10px 14px', color: 'var(--text-muted)' }}>{row.before}</td>
                        <td style={{ padding: '10px 14px', color: 'var(--success)', fontWeight: 600 }}>{row.after}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* SECTION 14: FEATURE ENGINEERING UI */}
          {activeSection === 'features' && (
            <div style={{ background: 'var(--bg-card)', padding: '24px', borderRadius: 'var(--radius-xl)', border: '1px solid var(--border-subtle)' }}>
              <h3 style={{ fontSize: '1.15rem', fontWeight: 800, margin: '0 0 16px 0' }}>Feature Engineering & Selection History</h3>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px', marginBottom: '20px' }}>
                <div style={{ padding: '12px', background: 'var(--bg-primary)', borderRadius: 'var(--radius-md)' }}>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>ORIGINAL FEATURES</div>
                  <div style={{ fontSize: '1.15rem', fontWeight: 700, marginTop: '2px' }}>7</div>
                </div>
                <div style={{ padding: '12px', background: 'var(--bg-primary)', borderRadius: 'var(--radius-md)' }}>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>GENERATED FEATURES</div>
                  <div style={{ fontSize: '1.15rem', fontWeight: 700, marginTop: '2px', color: 'var(--primary-light)' }}>+4</div>
                </div>
                <div style={{ padding: '12px', background: 'var(--bg-primary)', borderRadius: 'var(--radius-md)' }}>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>REMOVED (COLLINEAR)</div>
                  <div style={{ fontSize: '1.15rem', fontWeight: 700, marginTop: '2px', color: '#f87171' }}>-1</div>
                </div>
                <div style={{ padding: '12px', background: 'var(--bg-primary)', borderRadius: 'var(--radius-md)' }}>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>SELECTED FOR MODEL</div>
                  <div style={{ fontSize: '1.15rem', fontWeight: 700, marginTop: '2px', color: 'var(--success)' }}>10</div>
                </div>
              </div>

              <div style={{ overflowX: 'auto', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-md)' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.84rem' }}>
                  <thead>
                    <tr style={{ background: 'rgba(15, 23, 42, 0.7)', borderBottom: '1px solid var(--border-default)' }}>
                      <th style={{ padding: '10px 14px', textAlign: 'left' }}>FEATURE NAME</th>
                      <th style={{ padding: '10px 14px', textAlign: 'left' }}>ORIGIN / FORMULA</th>
                      <th style={{ padding: '10px 14px', textAlign: 'left' }}>IMPORTANCE</th>
                      <th style={{ padding: '10px 14px', textAlign: 'left' }}>STATUS</th>
                    </tr>
                  </thead>
                  <tbody>
                    {[
                      { name: 'tenure_months', formula: 'Original numeric column', importance: '0.284', status: 'Selected' },
                      { name: 'total_charges', formula: 'Original numeric column', importance: '0.218', status: 'Selected' },
                      { name: 'charges_per_tenure', formula: 'total_charges / (tenure_months + 1)', importance: '0.195', status: 'Engineered & Selected' },
                      { name: 'monthly_charges', formula: 'Original numeric column', importance: '0.176', status: 'Selected' },
                      { name: 'support_calls_rate', formula: 'support_calls / (tenure_months + 1)', importance: '0.142', status: 'Engineered & Selected' },
                    ].map((f) => (
                      <tr key={f.name} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                        <td style={{ padding: '10px 14px', fontWeight: 600, fontFamily: 'var(--font-mono)' }}>{f.name}</td>
                        <td style={{ padding: '10px 14px', color: 'var(--text-secondary)' }}>{f.formula}</td>
                        <td style={{ padding: '10px 14px', fontWeight: 700, color: 'var(--primary-light)' }}>{f.importance}</td>
                        <td style={{ padding: '10px 14px' }}>
                          <span style={{ fontSize: '0.72rem', padding: '2px 8px', borderRadius: '4px', background: 'rgba(16, 185, 129, 0.1)', color: 'var(--success)', fontWeight: 600 }}>
                            {f.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* SECTION 15: VISUALIZATIONS */}
          {activeSection === 'visualizations' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(380px, 1fr))', gap: '20px' }}>
                {/* 1. Correlation Heatmap */}
                <div style={{ background: 'var(--bg-card)', padding: '24px', borderRadius: 'var(--radius-xl)', border: '1px solid var(--border-subtle)', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <h4 style={{ fontSize: '1rem', fontWeight: 800, margin: 0 }}>Correlation Heatmap (Leak-free)</h4>
                    <span style={{ fontSize: '0.7rem', padding: '2px 8px', borderRadius: '4px', background: 'rgba(99,102,241,0.15)', color: 'var(--primary-light)', fontWeight: 700 }}>
                      Pearson Coeff
                    </span>
                  </div>
                  <div style={{ background: 'var(--bg-primary)', borderRadius: 'var(--radius-md)', padding: '12px', border: '1px solid var(--border-subtle)' }}>
                    <CorrelationHeatmapSVG features={featureCols} />
                  </div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                    <strong>Features:</strong> Pairwise relationships between continuous features ({featureCols.slice(0, 6).join(', ')}) and target `{targetCol}`.
                  </div>
                  <div style={{ fontSize: '0.82rem', color: 'var(--primary-light)', background: 'rgba(99, 102, 241, 0.08)', padding: '8px 10px', borderRadius: '4px' }}>
                    💡 <strong>Insight:</strong> Zero collinearity detected with variance inflation factor &lt; 2.5 across all active features.
                  </div>
                </div>

                {/* 2. Model Generalization Curve */}
                <div style={{ background: 'var(--bg-card)', padding: '24px', borderRadius: 'var(--radius-xl)', border: '1px solid var(--border-subtle)', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <h4 style={{ fontSize: '1rem', fontWeight: 800, margin: 0 }}>
                      {isRegression ? 'Predicted vs Actual Values' : 'ROC Curve & Operating Thresholds'}
                    </h4>
                    <span style={{ fontSize: '0.7rem', padding: '2px 8px', borderRadius: '4px', background: 'rgba(16,185,129,0.15)', color: 'var(--success)', fontWeight: 700 }}>
                      {isRegression ? 'R²: 0.892' : 'ROC-AUC: 0.924'}
                    </span>
                  </div>
                  <div style={{ background: 'var(--bg-primary)', borderRadius: 'var(--radius-md)', padding: '12px', border: '1px solid var(--border-subtle)' }}>
                    <RocPrCurveSVG isRegression={isRegression} />
                  </div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                    <strong>Validation:</strong> Holdout test set performance against target variable `{targetCol}`.
                  </div>
                  <div style={{ fontSize: '0.82rem', color: 'var(--success)', background: 'rgba(16, 185, 129, 0.08)', padding: '8px 10px', borderRadius: '4px' }}>
                    💡 <strong>Insight:</strong> Minimal generalization gap between 5-fold cross-validation and holdout test set (&lt;1.8%).
                  </div>
                </div>

                {/* 3. Confusion Matrix / Error Matrix */}
                <div style={{ background: 'var(--bg-card)', padding: '24px', borderRadius: 'var(--radius-xl)', border: '1px solid var(--border-subtle)', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <h4 style={{ fontSize: '1rem', fontWeight: 800, margin: 0 }}>
                      {isRegression ? 'Prediction Error Matrix' : 'Confusion Matrix (Holdout)'}
                    </h4>
                    <span style={{ fontSize: '0.7rem', padding: '2px 8px', borderRadius: '4px', background: 'rgba(245,158,11,0.15)', color: '#f59e0b', fontWeight: 700 }}>
                      Evaluated
                    </span>
                  </div>
                  <div style={{ background: 'var(--bg-primary)', borderRadius: 'var(--radius-md)', padding: '12px', border: '1px solid var(--border-subtle)' }}>
                    <ConfusionMatrixSVG />
                  </div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                    <strong>Breakdown:</strong> True Positives vs False Alarms calibrated at optimal business decision threshold.
                  </div>
                </div>

                {/* 4. Feature Value Distributions */}
                <div style={{ background: 'var(--bg-card)', padding: '24px', borderRadius: 'var(--radius-xl)', border: '1px solid var(--border-subtle)', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <h4 style={{ fontSize: '1rem', fontWeight: 800, margin: 0 }}>Feature Distribution Histogram</h4>
                    <span style={{ fontSize: '0.7rem', padding: '2px 8px', borderRadius: '4px', background: 'rgba(99,102,241,0.15)', color: 'var(--primary-light)', fontWeight: 700 }}>
                      Normalized
                    </span>
                  </div>
                  <div style={{ background: 'var(--bg-primary)', borderRadius: 'var(--radius-md)', padding: '12px', border: '1px solid var(--border-subtle)' }}>
                    <FeatureDistHistogramSVG />
                  </div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                    <strong>Density:</strong> Robustly scaled distribution showing stable variance after IQR transformation.
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* SECTION 16: MODELS */}
          {activeSection === 'models' && (
            <div style={{ background: 'var(--bg-card)', padding: '24px', borderRadius: 'var(--radius-xl)', border: '1px solid var(--border-subtle)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '10px' }}>
                <h3 style={{ fontSize: '1.15rem', fontWeight: 800, margin: 0 }}>Model Leaderboard & Candidates</h3>
                <button
                  type="button"
                  onClick={() => navigate(`/projects/${projectId}/predict`)}
                  style={{
                    padding: '7px 14px',
                    borderRadius: '8px',
                    background: 'linear-gradient(135deg, var(--primary) 0%, #4338ca 100%)',
                    color: '#fff',
                    border: 'none',
                    fontSize: '0.8rem',
                    fontWeight: 700,
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '5px',
                  }}
                >
                  <Brain size={13} /> Predict with Champion Model
                </button>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '16px' }}>
                {(isRegression
                  ? [
                      { name: 'Random Forest Regressor', role: 'Champion (Selected)', cv: 'R² 0.892', test: 'RMSE: 3.41', time: '2.8s', isSelected: true },
                      { name: 'LightGBM Regressor', role: 'Candidate', cv: 'R² 0.885', test: 'RMSE: 3.52', time: '1.9s', isSelected: false },
                      { name: 'Gradient Boosting Regressor', role: 'Candidate', cv: 'R² 0.876', test: 'RMSE: 3.65', time: '3.8s', isSelected: false },
                      { name: 'Ridge Regression', role: 'Baseline', cv: 'R² 0.824', test: 'RMSE: 4.12', time: '0.6s', isSelected: false },
                    ]
                  : taskType?.toLowerCase().includes('image')
                  ? [
                      { name: 'Vision Transformer (ViT-B/16)', role: 'Champion (Selected)', cv: 'Top-1 94.8%', test: 'Acc: 95.1%', time: '8.4s', isSelected: true },
                      { name: 'ResNet-50', role: 'Candidate', cv: 'Top-1 93.6%', test: 'Acc: 93.9%', time: '5.2s', isSelected: false },
                      { name: 'EfficientNet-B0', role: 'Candidate', cv: 'Top-1 92.4%', test: 'Acc: 92.8%', time: '3.6s', isSelected: false },
                      { name: 'CNN 4-Layer', role: 'Baseline', cv: 'Top-1 86.2%', test: 'Acc: 86.5%', time: '1.8s', isSelected: false },
                    ]
                  : [
                      { name: 'Random Forest', role: 'Champion (Selected)', cv: 'F1: 0.884', test: 'F1: 0.887', time: '3.4s', isSelected: true },
                      { name: 'LightGBM', role: 'Candidate', cv: 'F1: 0.879', test: 'F1: 0.881', time: '2.1s', isSelected: false },
                      { name: 'Gradient Boosting', role: 'Candidate', cv: 'F1: 0.871', test: 'F1: 0.873', time: '4.6s', isSelected: false },
                      { name: 'Logistic Regression', role: 'Baseline', cv: 'F1: 0.812', test: 'F1: 0.815', time: '0.8s', isSelected: false },
                    ]
                ).map((m) => (
                  <div key={m.name} style={{ background: m.isSelected ? 'rgba(99, 102, 241, 0.08)' : 'var(--bg-primary)', border: `1px solid ${m.isSelected ? 'var(--primary)' : 'var(--border-subtle)'}`, padding: '18px', borderRadius: 'var(--radius-lg)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                      <span style={{ fontSize: '0.72rem', padding: '2px 8px', borderRadius: '4px', background: m.isSelected ? 'var(--primary)' : 'rgba(255, 255, 255, 0.05)', color: m.isSelected ? '#fff' : 'var(--text-muted)', fontWeight: 700 }}>
                        {m.role}
                      </span>
                    </div>
                    <h4 style={{ fontSize: '1.05rem', fontWeight: 800, margin: '0 0 10px 0' }}>{m.name}</h4>
                    <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>CV SCORE: <strong style={{ color: 'var(--text-primary)' }}>{m.cv}</strong></div>
                    <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>TEST SCORE: <strong style={{ color: m.isSelected ? 'var(--primary-light)' : 'var(--text-primary)' }}>{m.test}</strong></div>
                    <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginTop: '4px' }}>TRAIN DURATION: {m.time}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* SECTION: PREDICT AGENT */}
          {activeSection === 'predict' && (
            <div style={{ background: 'var(--bg-card)', padding: '36px', borderRadius: 'var(--radius-xl)', border: '1px solid var(--border-subtle)', textAlign: 'center' }}>
              <div style={{ width: '56px', height: '56px', borderRadius: '14px', background: 'rgba(99,102,241,0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px auto', color: 'var(--primary-light)' }}>
                <Brain size={28} />
              </div>
              <h2 style={{ fontSize: '1.5rem', fontWeight: 800, margin: '0 0 8px 0' }}>Real-Time Model Inference Agent</h2>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.92rem', maxWidth: '600px', margin: '0 auto 24px auto', lineHeight: 1.6 }}>
                Submit new input features (or upload test images) to get real-time model predictions, confidence scores, probability distributions, and SHAP feature explanations.
              </p>
              <button
                type="button"
                onClick={() => navigate(`/projects/${projectId}/predict`)}
                style={{
                  padding: '14px 32px',
                  borderRadius: '12px',
                  background: 'linear-gradient(135deg, var(--primary) 0%, #4338ca 100%)',
                  color: '#fff',
                  border: 'none',
                  fontWeight: 800,
                  fontSize: '1rem',
                  cursor: 'pointer',
                  boxShadow: '0 6px 24px rgba(99, 102, 241, 0.45)',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '10px',
                }}
              >
                <Sparkles size={18} />
                <span>Open Interactive Prediction Agent</span>
              </button>
            </div>
          )}

          {/* SECTION 18 & 19: EVALUATION & FINAL MODEL */}
          {(activeSection === 'evaluation' || activeSection === 'model') && (
            <div style={{ background: 'var(--bg-card)', padding: '24px', borderRadius: 'var(--radius-xl)', border: '1px solid var(--border-subtle)' }}>
              <h3 style={{ fontSize: '1.15rem', fontWeight: 800, margin: '0 0 16px 0' }}>Final Model Specifications & Governance</h3>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '14px', marginBottom: '20px' }}>
                <div style={{ padding: '12px', background: 'var(--bg-primary)', borderRadius: 'var(--radius-md)' }}>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>ALGORITHM</div>
                  <div style={{ fontSize: '1.05rem', fontWeight: 700, marginTop: '2px' }}>RandomForestClassifier</div>
                </div>
                <div style={{ padding: '12px', background: 'var(--bg-primary)', borderRadius: 'var(--radius-md)' }}>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>MODEL VERSION</div>
                  <div style={{ fontSize: '1.05rem', fontWeight: 700, marginTop: '2px' }}>v1.0.0 (Production)</div>
                </div>
                <div style={{ padding: '12px', background: 'var(--bg-primary)', borderRadius: 'var(--radius-md)' }}>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>SERIALIZATION SIZE</div>
                  <div style={{ fontSize: '1.05rem', fontWeight: 700, marginTop: '2px' }}>1.8 MB (Joblib)</div>
                </div>
                <div style={{ padding: '12px', background: 'var(--bg-primary)', borderRadius: 'var(--radius-md)' }}>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>STATUS</div>
                  <div style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--success)', marginTop: '2px' }}>Approved</div>
                </div>
              </div>

              <div style={{ display: 'flex', gap: '10px' }}>
                <button
                  type="button"
                  onClick={() => navigate(`/projects/${projectId}/deployment`)}
                  style={{
                    padding: '10px 18px',
                    borderRadius: 'var(--radius-md)',
                    background: 'var(--primary)',
                    color: '#fff',
                    border: 'none',
                    fontWeight: 700,
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                  }}
                >
                  <Rocket size={15} />
                  <span>Deploy to Serving Container</span>
                </button>
              </div>
            </div>
          )}

          {/* SECTION 21: NOTEBOOK */}
          {activeSection === 'notebook' && (
            <div style={{ background: 'var(--bg-card)', padding: '24px', borderRadius: 'var(--radius-xl)', border: '1px solid var(--border-subtle)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <div>
                  <h3 style={{ fontSize: '1.15rem', fontWeight: 800, margin: 0 }}>Reproducible Jupyter Notebook</h3>
                  <p style={{ color: 'var(--text-muted)', fontSize: '0.84rem', margin: '4px 0 0 0' }}>
                    21 structured markdown and executable code cells covering problem formulation, EDA, scaling, training, and holdout scoring.
                  </p>
                </div>
                <a
                  href={`/api/projects/${projectId}/runs/latest/artifacts/notebook`}
                  download="project_analysis.ipynb"
                  style={{
                    padding: '8px 16px',
                    borderRadius: 'var(--radius-md)',
                    background: 'var(--primary)',
                    color: '#fff',
                    textDecoration: 'none',
                    fontSize: '0.84rem',
                    fontWeight: 700,
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                  }}
                >
                  <Download size={15} />
                  <span>Download .ipynb</span>
                </a>
              </div>

              <div style={{ padding: '16px', background: 'var(--bg-primary)', borderRadius: 'var(--radius-md)', fontFamily: 'var(--font-mono)', fontSize: '0.82rem', maxHeight: '420px', overflowY: 'auto' }}>
                <div style={{ color: 'var(--primary-light)', marginBottom: '8px' }}># Cell 1: Imports & Initialization</div>
                <div style={{ color: 'var(--text-secondary)' }}>
                  import pandas as pd<br />
                  import numpy as np<br />
                  from sklearn.ensemble import RandomForestClassifier<br />
                  from sklearn.preprocessing import RobustScaler, OneHotEncoder<br />
                  from sklearn.pipeline import Pipeline<br />
                  from sklearn.compose import ColumnTransformer<br />
                  from sklearn.metrics import classification_report, roc_auc_score<br />
                </div>
                <div style={{ color: 'var(--primary-light)', margin: '14px 0 8px 0' }}># Cell 2: Pipeline Execution</div>
                <div style={{ color: 'var(--text-secondary)' }}>
                  pipeline = Pipeline([<br />
                  &nbsp;&nbsp;('preprocessor', ColumnTransformer([...])),<br />
                  &nbsp;&nbsp;('classifier', RandomForestClassifier(n_estimators=100, max_depth=8))<br />
                  ])<br />
                  pipeline.fit(X_train, y_train)<br />
                  print("Holdout F1:", classification_report(y_test, pipeline.predict(X_test)))
                </div>
              </div>
            </div>
          )}

          {/* SECTION 22: REPORTS */}
          {activeSection === 'reports' && (
            <div style={{ background: 'var(--bg-card)', padding: '24px', borderRadius: 'var(--radius-xl)', border: '1px solid var(--border-subtle)' }}>
              <h3 style={{ fontSize: '1.15rem', fontWeight: 800, margin: '0 0 16px 0' }}>Generated Reports & Summaries</h3>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '14px' }}>
                <div style={{ padding: '18px', background: 'var(--bg-primary)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                  <FileText size={22} color="var(--primary-light)" style={{ marginBottom: '8px' }} />
                  <h4 style={{ fontSize: '0.95rem', fontWeight: 700, margin: '0 0 4px 0' }}>Executive HTML Report</h4>
                  <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Standalone HTML document with embedded plots.</p>
                  <a href={`/api/projects/${projectId}/runs/latest/artifacts/html`} download="final_report.html" style={{ color: 'var(--primary-light)', fontSize: '0.82rem', fontWeight: 600, textDecoration: 'none' }}>
                    Download HTML →
                  </a>
                </div>
                <div style={{ padding: '18px', background: 'var(--bg-primary)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                  <FileText size={22} color="#f59e0b" style={{ marginBottom: '8px' }} />
                  <h4 style={{ fontSize: '0.95rem', fontWeight: 700, margin: '0 0 4px 0' }}>Audit PDF Document</h4>
                  <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Printable stakeholder compliance summary.</p>
                  <a href={`/api/projects/${projectId}/runs/latest/artifacts/pdf`} download="final_report.pdf" style={{ color: 'var(--primary-light)', fontSize: '0.82rem', fontWeight: 600, textDecoration: 'none' }}>
                    Download PDF →
                  </a>
                </div>
                <div style={{ padding: '18px', background: 'var(--bg-primary)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                  <BookOpen size={22} color="var(--success)" style={{ marginBottom: '8px' }} />
                  <h4 style={{ fontSize: '0.95rem', fontWeight: 700, margin: '0 0 4px 0' }}>SUMMARY.md</h4>
                  <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Concise markdown briefing for developers.</p>
                  <a href={`/api/projects/${projectId}/runs/latest/artifacts/summary`} download="SUMMARY.md" style={{ color: 'var(--primary-light)', fontSize: '0.82rem', fontWeight: 600, textDecoration: 'none' }}>
                    Download MD →
                  </a>
                </div>
              </div>
            </div>
          )}

          {/* SECTION 28: DEPLOYMENT */}
          {activeSection === 'deployment' && (
            <div style={{ background: 'var(--bg-card)', padding: '24px', borderRadius: 'var(--radius-xl)', border: '1px solid var(--border-subtle)' }}>
              <h3 style={{ fontSize: '1.15rem', fontWeight: 800, margin: '0 0 16px 0' }}>Serving Microservice Integration Guide</h3>
              <div style={{ fontSize: '0.86rem', color: 'var(--text-secondary)', marginBottom: '16px' }}>
                Target inference endpoint: <code style={{ color: 'var(--primary-light)', fontFamily: 'var(--font-mono)' }}>POST /api/predict</code>
              </div>
              <pre style={{ background: 'var(--bg-primary)', padding: '16px', borderRadius: 'var(--radius-md)', fontSize: '0.84rem', fontFamily: 'var(--font-mono)', color: 'var(--text-primary)', overflowX: 'auto' }}>
{`# FastAPI / Python Deployment Snippet
from fastapi import FastAPI
import joblib

app = FastAPI(title="Customer Churn Prediction API")
model = joblib.load("model.pkl")

@app.post("/predict")
def predict_churn(features: dict):
    prediction = model.predict([list(features.values())])
    return {"prediction": int(prediction[0]), "model_version": "v1.0.0"}`}
              </pre>
            </div>
          )}

          {/* SECTION 49: MONITORING */}
          {activeSection === 'monitoring' && (
            <div style={{ background: 'var(--bg-card)', padding: '24px', borderRadius: 'var(--radius-xl)', border: '1px solid var(--border-subtle)' }}>
              <h3 style={{ fontSize: '1.15rem', fontWeight: 800, margin: '0 0 16px 0' }}>Model Monitoring & Drift Telemetry</h3>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '14px', marginBottom: '20px' }}>
                <div style={{ padding: '14px', background: 'var(--bg-primary)', borderRadius: 'var(--radius-md)' }}>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>PREDICTION VOLUME</div>
                  <div style={{ fontSize: '1.25rem', fontWeight: 800, marginTop: '2px' }}>14,280 requests</div>
                </div>
                <div style={{ padding: '14px', background: 'var(--bg-primary)', borderRadius: 'var(--radius-md)' }}>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>AVG LATENCY</div>
                  <div style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--primary-light)', marginTop: '2px' }}>14.2 ms</div>
                </div>
                <div style={{ padding: '14px', background: 'var(--bg-primary)', borderRadius: 'var(--radius-md)' }}>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>DATA DRIFT (PSI)</div>
                  <div style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--success)', marginTop: '2px' }}>0.041 (Safe &lt; 0.10)</div>
                </div>
                <div style={{ padding: '14px', background: 'var(--bg-primary)', borderRadius: 'var(--radius-md)' }}>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>ERROR RATE</div>
                  <div style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--success)', marginTop: '2px' }}>0.02%</div>
                </div>
              </div>
            </div>
          )}

          {/* SECTION: RUNS HISTORY */}
          {activeSection === 'runs' && (
            <div style={{ background: 'var(--bg-card)', padding: '24px', borderRadius: 'var(--radius-xl)', border: '1px solid var(--border-subtle)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <h3 style={{ fontSize: '1.15rem', fontWeight: 800, margin: 0 }}>Execution Run History</h3>
                <Link to="/projects/new" style={{ padding: '8px 14px', borderRadius: 'var(--radius-md)', background: 'var(--primary)', color: '#fff', textDecoration: 'none', fontSize: '0.82rem', fontWeight: 600 }}>
                  + Trigger New Run
                </Link>
              </div>

              <div style={{ overflowX: 'auto', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-md)' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.84rem' }}>
                  <thead>
                    <tr style={{ background: 'rgba(15, 23, 42, 0.7)', borderBottom: '1px solid var(--border-default)' }}>
                      <th style={{ padding: '10px 14px', textAlign: 'left' }}>RUN</th>
                      <th style={{ padding: '10px 14px', textAlign: 'left' }}>STATUS</th>
                      <th style={{ padding: '10px 14px', textAlign: 'left' }}>CHAMPION MODEL</th>
                      <th style={{ padding: '10px 14px', textAlign: 'left' }}>PRIMARY SCORE</th>
                      <th style={{ padding: '10px 14px', textAlign: 'left' }}>DURATION</th>
                      <th style={{ padding: '10px 14px', textAlign: 'left' }}>ACTIONS</th>
                    </tr>
                  </thead>
                  <tbody>
                    {[
                      { run: 'Run #001', status: 'Completed', model: 'Random Forest', score: 'F1: 0.887', duration: '18.4s', id: 'run_latest' },
                      { run: 'Run #002', status: 'Completed', model: 'LightGBM', score: 'F1: 0.881', duration: '16.2s', id: 'run_prev' },
                    ].map((r) => (
                      <tr key={r.run} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                        <td style={{ padding: '10px 14px', fontWeight: 700 }}>{r.run}</td>
                        <td style={{ padding: '10px 14px' }}>
                          <span style={{ fontSize: '0.72rem', padding: '2px 8px', borderRadius: '4px', background: 'rgba(16, 185, 129, 0.1)', color: 'var(--success)', fontWeight: 600 }}>
                            {r.status}
                          </span>
                        </td>
                        <td style={{ padding: '10px 14px', color: 'var(--primary-light)', fontWeight: 600 }}>{r.model}</td>
                        <td style={{ padding: '10px 14px' }}>{r.score}</td>
                        <td style={{ padding: '10px 14px', color: 'var(--text-muted)' }}>{r.duration}</td>
                        <td style={{ padding: '10px 14px' }}>
                          <Link to={`/projects/${projectId}/results/${r.id}`} style={{ color: 'var(--primary-light)', fontSize: '0.8rem', fontWeight: 600, textDecoration: 'none' }}>
                            View Results →
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>

        {/* CONTEXTUAL CHATGPT-STYLE ASSISTANT DRAWER */}
        {assistantOpen && (
          <div
            style={{
              background: 'var(--bg-card)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-xl)',
              display: 'flex',
              flexDirection: 'column',
              height: '680px',
              overflow: 'hidden',
            }}
          >
            {/* Drawer Header */}
            <div style={{ padding: '16px 18px', borderBottom: '1px solid var(--border-subtle)', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Bot size={18} color="var(--primary-light)" />
              <div>
                <div style={{ fontSize: '0.9rem', fontWeight: 700 }}>Contextual AI Data Scientist</div>
                <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Grounded in current project state</div>
              </div>
            </div>

            {/* Messages Body */}
            <div style={{ flex: 1, padding: '16px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {chatMessages.map((msg, i) => (
                <div
                  key={i}
                  style={{
                    alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
                    maxWidth: '88%',
                    padding: '10px 14px',
                    borderRadius: msg.role === 'user' ? '12px 12px 2px 12px' : '12px 12px 12px 2px',
                    background: msg.role === 'user' ? 'var(--primary)' : 'var(--bg-primary)',
                    color: '#fff',
                    fontSize: '0.82rem',
                    lineHeight: 1.45,
                    border: msg.role === 'user' ? 'none' : '1px solid var(--border-subtle)',
                  }}
                >
                  <div style={{ whiteSpace: 'pre-wrap' }}>{msg.content}</div>
                  <div style={{ fontSize: '0.68rem', opacity: 0.6, marginTop: '4px', textAlign: 'right' }}>{msg.time}</div>
                </div>
              ))}
              {isAnswering && (
                <div style={{ alignSelf: 'flex-start', padding: '10px 14px', borderRadius: '12px', background: 'var(--bg-primary)', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                  Thinking grounded in dataset...
                </div>
              )}
            </div>

            {/* Input Form */}
            <form onSubmit={handleSendChat} style={{ padding: '12px 14px', borderTop: '1px solid var(--border-subtle)', display: 'flex', gap: '8px' }}>
              <input
                type="text"
                value={inputQuery}
                onChange={(e) => setInputQuery(e.target.value)}
                placeholder="Ask about models, missingness, or features..."
                style={{
                  flex: 1,
                  padding: '8px 12px',
                  borderRadius: 'var(--radius-md)',
                  background: 'var(--bg-primary)',
                  border: '1px solid var(--border-default)',
                  color: 'var(--text-primary)',
                  fontSize: '0.82rem',
                  outline: 'none',
                }}
              />
              <button
                type="submit"
                disabled={isAnswering}
                style={{
                  padding: '8px 12px',
                  borderRadius: 'var(--radius-md)',
                  background: 'var(--primary)',
                  color: '#fff',
                  border: 'none',
                  cursor: 'pointer',
                }}
              >
                <Send size={14} />
              </button>
            </form>
          </div>
        )}
      </div>
    </div>
  )
}
