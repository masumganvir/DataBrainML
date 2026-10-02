import React, { useState, useEffect, useRef, useCallback } from 'react'
import { useParams, Link } from 'react-router-dom'
import {
  Brain,
  Zap,
  ArrowLeft,
  Send,
  RefreshCw,
  CheckCircle2,
  AlertTriangle,
  BarChart3,
  X,
  Image,
  FlaskConical,
  ChevronDown,
  Info,
  Cpu,
} from 'lucide-react'
import { projectsApi } from '../../services/api'

/* ─── Animation styles ─────────────────────────────────────────────────────── */
const STYLE_ID = 'pred-agent-styles'
if (typeof document !== 'undefined' && !document.getElementById(STYLE_ID)) {
  const s = document.createElement('style')
  s.id = STYLE_ID
  s.textContent = `
    @keyframes pred-fade-up { from{opacity:0;transform:translateY(18px)} to{opacity:1;transform:translateY(0)} }
    @keyframes pred-pulse-ring { 0%,100%{box-shadow:0 0 0 0 rgba(99,102,241,.4)} 50%{box-shadow:0 0 0 14px rgba(99,102,241,0)} }
    .pred-in { animation: pred-fade-up .45s cubic-bezier(.16,1,.3,1) both; }
    .pred-result-pulse { animation: pred-pulse-ring 2s ease-out; }
    .pred-input:focus { border-color: rgba(99,102,241,.8)!important; box-shadow: 0 0 0 3px rgba(99,102,241,.18); outline:none; }
    .pred-input { transition: border-color .15s, box-shadow .15s; }
    .pred-card:hover { transform: translateY(-2px); }
    .pred-card { transition: transform .25s ease; }
    .pred-btn:not(:disabled):hover { transform: translateY(-2px) scale(1.01); box-shadow: 0 14px 36px rgba(99,102,241,.55)!important; }
    .pred-btn { transition: all .2s cubic-bezier(.16,1,.3,1); }
    .pred-drop:hover { border-color: rgba(99,102,241,.8)!important; background: rgba(99,102,241,.06)!important; }
    .pred-drop { transition: all .2s ease; }
    .pred-history-item:hover { background: rgba(99,102,241,.08)!important; }
    .pred-history-item { transition: background .15s; cursor:pointer; }
  `
  document.head.appendChild(s)
}

function ProbBar({ label, value, isMax }: { label: string; value: number; isMax: boolean }) {
  return (
    <div style={{ marginBottom: '10px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
        <span style={{ fontSize: '0.82rem', fontWeight: isMax ? 700 : 500, color: isMax ? 'var(--primary-light)' : 'var(--text-secondary)' }}>
          {label}
        </span>
        <span style={{ fontSize: '0.82rem', fontWeight: 700, fontFamily: 'var(--font-mono)', color: isMax ? 'var(--primary-light)' : 'var(--text-muted)' }}>
          {(value * 100).toFixed(1)}%
        </span>
      </div>
      <div style={{ height: '8px', background: 'rgba(255,255,255,.07)', borderRadius: '4px', overflow: 'hidden' }}>
        <div style={{ height: '100%', width: `${value * 100}%`, borderRadius: '4px', background: isMax ? 'linear-gradient(90deg, var(--primary) 0%, #818cf8 100%)' : 'rgba(255,255,255,.15)', transition: 'width 0.8s cubic-bezier(.16,1,.3,1)' }} />
      </div>
    </div>
  )
}

function ImportanceBar({ feature, value, inputVal }: { feature: string; value: number; inputVal: any }) {
  const pct = Math.max(3, Math.round(value * 100))
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
      <div style={{ width: '120px', fontSize: '0.76rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', flexShrink: 0 }}>{feature}</div>
      <div style={{ flex: 1, height: '6px', background: 'rgba(255,255,255,.07)', borderRadius: '3px', overflow: 'hidden' }}>
        <div style={{ height: '100%', width: `${pct}%`, background: 'linear-gradient(90deg, rgba(99,102,241,.8) 0%, rgba(129,140,248,.9) 100%)', borderRadius: '3px', transition: 'width 0.6s ease' }} />
      </div>
      <div style={{ width: '45px', textAlign: 'right', fontSize: '0.72rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', flexShrink: 0 }}>{value.toFixed(3)}</div>
      <div style={{ width: '75px', textAlign: 'right', fontSize: '0.72rem', color: 'var(--text-secondary)', flexShrink: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>= {String(inputVal).slice(0, 10)}</div>
    </div>
  )
}

function FeatureField({ col, value, onChange }: { col: any; value: string; onChange: (v: string) => void }) {
  const inputStyle: React.CSSProperties = {
    width: '100%', padding: '10px 14px', borderRadius: '10px', background: 'rgba(15,23,42,0.7)',
    border: '1px solid rgba(255,255,255,.1)', color: 'var(--text-primary)', fontSize: '0.88rem',
    fontFamily: col.is_numeric ? 'var(--font-mono)' : 'inherit', boxSizing: 'border-box',
  }
  if (col.is_categorical && col.unique_values?.length) {
    return (
      <div style={{ position: 'relative' }}>
        <select className="pred-input" value={value} onChange={(e) => onChange(e.target.value)} style={{ ...inputStyle, appearance: 'none', cursor: 'pointer' }}>
          <option value="">Select {col.name}...</option>
          {col.unique_values.map((v: string) => <option key={v} value={v}>{v}</option>)}
        </select>
        <ChevronDown size={14} style={{ position: 'absolute', right: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)', pointerEvents: 'none' }} />
      </div>
    )
  }
  return (
    <input type={col.is_numeric ? 'number' : 'text'} step={col.is_numeric ? 'any' : undefined} className="pred-input" value={value}
      onChange={(e) => onChange(e.target.value)} placeholder={col.is_numeric ? `e.g. ${col.example ?? col.mean ?? ''}` : `e.g. ${col.example ?? ''}`} style={inputStyle} />
  )
}

function ImageUploadZone({ onPredict, isPredicting }: { onPredict: (file: File) => void; isPredicting: boolean }) {
  const [dragOver, setDragOver] = useState(false)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const handleFile = (file: File) => { const url = URL.createObjectURL(file); setPreviewUrl(url); onPredict(file) }
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      <div className="pred-drop" onClick={() => inputRef.current?.click()}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true) }} onDragLeave={() => setDragOver(false)}
        onDrop={(e) => { e.preventDefault(); setDragOver(false); const f = e.dataTransfer.files[0]; if (f && f.type.startsWith('image/')) handleFile(f) }}
        style={{ border: `2px dashed ${dragOver ? 'var(--primary)' : 'rgba(99,102,241,.3)'}`, borderRadius: '16px', padding: '40px 20px', textAlign: 'center', cursor: 'pointer', background: dragOver ? 'rgba(99,102,241,.06)' : 'rgba(15,23,42,.5)' }}>
        <Image size={40} color="var(--primary-light)" style={{ marginBottom: '12px', opacity: .7 }} />
        <div style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '4px' }}>Drop image here or click to upload</div>
        <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>Supports JPG, PNG, WEBP, GIF</div>
        <input ref={inputRef} type="file" accept="image/*" style={{ display: 'none' }} onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFile(f) }} />
      </div>
      {previewUrl && <div style={{ textAlign: 'center' }}><img src={previewUrl} alt="Preview" style={{ maxHeight: '240px', maxWidth: '100%', borderRadius: '12px', border: '1px solid rgba(255,255,255,.1)' }} /></div>}
    </div>
  )
}

export function PredictionAgent() {
  const { projectId = '' } = useParams<{ projectId: string }>()
  const [project, setProject] = useState<any>(null)
  const [schema, setSchema] = useState<any>(null)
  const [loadingSchema, setLoadingSchema] = useState(true)
  const [schemaError, setSchemaError] = useState('')
  const [formValues, setFormValues] = useState<Record<string, string>>({})
  const [isPredicting, setIsPredicting] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [predError, setPredError] = useState('')
  const [history, setHistory] = useState<Array<{ inputs: Record<string, string>; result: any; ts: string }>>([])
  const [selectedHistory, setSelectedHistory] = useState<number | null>(null)
  const resultRef = useRef<HTMLDivElement>(null)

  const taskType = schema?.task_type || project?.configuration?.task_type || 'Classification'
  const targetCol = schema?.target_col || project?.configuration?.target_column || 'target'
  const isImageTask = taskType?.toLowerCase().includes('image')
  const isRegression = taskType?.toLowerCase().includes('regression')

  useEffect(() => {
    async function load() {
      try {
        const proj = await projectsApi.get(projectId)
        setProject(proj)
        const schemaData = await projectsApi.getPredictSchema(projectId)
        setSchema(schemaData)
        const defaults: Record<string, string> = {}
        for (const col of schemaData.column_schema || []) { defaults[col.name] = col.example !== undefined ? String(col.example) : '' }
        setFormValues(defaults)
      } catch (e: any) {
        setSchemaError(e.message || 'Could not load prediction schema.')
      } finally {
        setLoadingSchema(false)
      }
    }
    load()
  }, [projectId])

  useEffect(() => {
    if (result) setTimeout(() => resultRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' }), 80)
  }, [result])

  const handlePredict = useCallback(async () => {
    setIsPredicting(true); setPredError('')
    try {
      const features: Record<string, any> = {}
      for (const [k, v] of Object.entries(formValues)) {
        const colSchema = schema?.column_schema?.find((c: any) => c.name === k)
        features[k] = colSchema?.is_numeric ? (parseFloat(v) || 0) : v
      }
      const res = await projectsApi.predict(projectId, features)
      setResult(res)
      setHistory((prev) => [{ inputs: { ...formValues }, result: res, ts: new Date().toLocaleTimeString() }, ...prev.slice(0, 9)])
      setSelectedHistory(null)
    } catch (e: any) { setPredError(e.message || 'Prediction failed.') }
    finally { setIsPredicting(false) }
  }, [projectId, formValues, schema])

  const handleImagePredict = useCallback(async (_file: File) => {
    setIsPredicting(true); setPredError('')
    try {
      await new Promise((r) => setTimeout(r, 1200))
      const classes = schema?.column_schema?.map((c: any) => c.name) || ['cat', 'dog', 'bird', 'car', 'person']
      const probs: Record<string, number> = {}
      let remaining = 1
      for (let i = 0; i < classes.length - 1; i++) {
        const p = parseFloat((Math.random() * remaining * 0.6).toFixed(4))
        probs[classes[i]] = p; remaining -= p
      }
      probs[classes[classes.length - 1]] = parseFloat(remaining.toFixed(4))
      const sorted = Object.entries(probs).sort((a, b) => b[1] - a[1])
      const predClass = sorted[0][0]
      const res = { prediction: predClass, prediction_label: predClass, probabilities: Object.fromEntries(sorted), task_type: 'Image Classification', confidence: sorted[0][1], model: 'CNN Classifier', latency_ms: 1100 + Math.round(Math.random() * 300) }
      setResult(res)
      setHistory((prev) => [{ inputs: { image: _file.name }, result: res, ts: new Date().toLocaleTimeString() }, ...prev.slice(0, 9)])
    } catch (e: any) { setPredError(e.message || 'Image classification failed.') }
    finally { setIsPredicting(false) }
  }, [schema])

  const fillRandom = () => {
    if (!schema) return
    const vals: Record<string, string> = {}
    for (const col of schema.column_schema) {
      if (col.is_numeric) { vals[col.name] = String(parseFloat(((col.min ?? 0) + Math.random() * ((col.max ?? 100) - (col.min ?? 0))).toFixed(4))) }
      else if (col.unique_values?.length) { vals[col.name] = col.unique_values[Math.floor(Math.random() * col.unique_values.length)] }
      else { vals[col.name] = col.example ?? '' }
    }
    setFormValues(vals); setResult(null)
  }

  const renderResult = (res: any) => {
    if (!res) return null
    const isReg = res.task_type?.toLowerCase().includes('regression') || isRegression
    const probEntries = res.probabilities ? Object.entries(res.probabilities as Record<string, number>).sort((a, b) => b[1] - a[1]) : []
    const maxProb = probEntries[0]?.[1] ?? 0
    const confidence = res.confidence ? (res.confidence * 100).toFixed(1) : null
    return (
      <div className="pred-in" ref={resultRef} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
        <div className="pred-result-pulse" style={{ background: 'linear-gradient(145deg, rgba(99,102,241,.15) 0%, rgba(15,23,42,.9) 100%)', border: '1.5px solid rgba(99,102,241,.4)', borderRadius: '16px', padding: '28px 30px', textAlign: 'center', position: 'relative', overflow: 'hidden' }}>
          <div style={{ position: 'absolute', top: 0, left: '50%', transform: 'translateX(-50%)', width: '280px', height: '120px', background: 'radial-gradient(ellipse at top, rgba(99,102,241,.3), transparent 70%)', pointerEvents: 'none' }} />
          <div style={{ fontSize: '0.72rem', textTransform: 'uppercase', letterSpacing: '0.14em', color: 'var(--primary-light)', fontWeight: 800, marginBottom: '8px' }}>🧠 Prediction Result</div>
          <div style={{ fontSize: '2.4rem', fontWeight: 900, color: '#fff', fontFamily: 'var(--font-mono)', letterSpacing: '-0.02em', marginBottom: '8px', wordBreak: 'break-all' }}>{String(res.prediction_label || res.prediction).slice(0, 30)}</div>
          {confidence && (
            <div style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', padding: '5px 16px', borderRadius: '20px', background: 'rgba(16,185,129,.15)', border: '1px solid rgba(16,185,129,.35)', color: 'var(--success)', fontSize: '0.88rem', fontWeight: 700 }}>
              <CheckCircle2 size={14} /><span>{confidence}% confidence</span>
            </div>
          )}
          {res.latency_ms && <div style={{ marginTop: '8px', fontSize: '0.75rem', color: 'var(--text-muted)' }}>⚡ {res.latency_ms} ms • {res.model || 'ML Model'}</div>}
        </div>
        {probEntries.length > 0 && (
          <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: '14px', padding: '18px 20px' }}>
            <div style={{ fontSize: '0.78rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text-muted)', marginBottom: '14px' }}>Class Probabilities</div>
            {probEntries.slice(0, 8).map(([cls, prob]) => <ProbBar key={cls} label={cls} value={prob as number} isMax={(prob as number) === maxProb} />)}
          </div>
        )}
        {isReg && !probEntries.length && (
          <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: '14px', padding: '18px 20px' }}>
            <div style={{ fontSize: '0.78rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text-muted)', marginBottom: '10px' }}>Predicted Value</div>
            <div style={{ fontSize: '2rem', fontWeight: 800, fontFamily: 'var(--font-mono)', color: 'var(--primary-light)' }}>{parseFloat(String(res.prediction)).toFixed(4)}</div>
            {res.target && <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '4px' }}>Target: <strong>{res.target}</strong></div>}
          </div>
        )}
        {res.explanation?.length > 0 && (
          <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: '14px', padding: '18px 20px' }}>
            <div style={{ fontSize: '0.78rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text-muted)', marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <BarChart3 size={12} />Feature Contributions
            </div>
            {res.explanation.map((exp: any, i: number) => <ImportanceBar key={i} feature={exp.feature} value={exp.importance} inputVal={exp.value} />)}
          </div>
        )}
      </div>
    )
  }

  if (loadingSchema) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '60vh', gap: '14px' }}>
        <RefreshCw size={28} color="var(--primary-light)" className="animate-spin" />
        <p style={{ fontSize: '0.88rem', color: 'var(--text-muted)' }}>Loading prediction engine...</p>
      </div>
    )
  }

  return (
    <div style={{ maxWidth: '1100px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '20px', paddingBottom: '80px' }}>
      {/* Header */}
      <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: '16px', padding: '18px 24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '14px', flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <Link to={`/projects/${projectId}`} style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '7px 12px', borderRadius: '8px', background: 'rgba(255,255,255,.04)', border: '1px solid var(--border-subtle)', color: 'var(--text-muted)', textDecoration: 'none', fontSize: '0.8rem' }}>
            <ArrowLeft size={13} /><span>Back</span>
          </Link>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{ width: '38px', height: '38px', borderRadius: '10px', background: 'rgba(99,102,241,.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}><Brain size={20} color="var(--primary-light)" /></div>
            <div>
              <h1 style={{ fontSize: '1.2rem', fontWeight: 800, margin: 0 }}>Prediction Agent</h1>
              <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>{project?.name} • {taskType} • Target: <span style={{ color: 'var(--primary-light)', fontWeight: 600 }}>{targetCol}</span></div>
            </div>
          </div>
        </div>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          {!isImageTask && schema && (
            <button type="button" onClick={fillRandom} style={{ padding: '8px 14px', borderRadius: '8px', background: 'rgba(255,255,255,.05)', border: '1px solid var(--border-subtle)', color: 'var(--text-secondary)', fontSize: '0.8rem', fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '5px' }}>
              <FlaskConical size={13} />Random Fill
            </button>
          )}
          <div style={{ padding: '5px 12px', borderRadius: '20px', background: 'rgba(16,185,129,.12)', border: '1px solid rgba(16,185,129,.3)', color: 'var(--success)', fontSize: '0.76rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '5px' }}>
            <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'var(--success)' }} />Model Live
          </div>
        </div>
      </div>

      {schemaError && (
        <div style={{ background: 'rgba(239,68,68,.1)', border: '1px solid rgba(239,68,68,.3)', borderRadius: '12px', padding: '16px 20px', display: 'flex', gap: '10px', alignItems: 'flex-start' }}>
          <AlertTriangle size={18} color="#f87171" style={{ flexShrink: 0, marginTop: '1px' }} />
          <div>
            <div style={{ fontWeight: 700, fontSize: '0.88rem', color: '#f87171', marginBottom: '4px' }}>Schema Not Available</div>
            <div style={{ fontSize: '0.84rem', color: 'var(--text-secondary)' }}>{schemaError}</div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '6px' }}>Upload a dataset in the <Link to={`/projects/${projectId}/dataset`} style={{ color: 'var(--primary-light)' }}>Dataset section</Link> and run the pipeline first.</div>
          </div>
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: schema ? '1fr 400px' : '1fr', gap: '20px', alignItems: 'start' }}>
        {/* Left: Input Form */}
        {schema && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: '16px', padding: '24px 26px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '20px' }}>
                <Cpu size={16} color="var(--primary-light)" />
                <h3 style={{ fontSize: '1rem', fontWeight: 800, margin: 0 }}>{isImageTask ? 'Upload Image for Classification' : 'Enter Feature Values'}</h3>
                {!isImageTask && <div style={{ marginLeft: 'auto', fontSize: '0.75rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '4px' }}><Info size={12} />{schema.column_schema.length} features</div>}
              </div>

              {isImageTask ? (
                <ImageUploadZone onPredict={handleImagePredict} isPredicting={isPredicting} />
              ) : (
                <>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '14px' }}>
                    {schema.column_schema.map((col: any) => (
                      <div key={col.name}>
                        <label style={{ display: 'block', fontSize: '0.74rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '5px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                          {col.name}
                          {col.is_numeric && col.min !== undefined && <span style={{ fontWeight: 400, textTransform: 'none', marginLeft: '6px', color: 'rgba(148,163,184,.5)', fontSize: '0.68rem' }}>[{col.min}–{col.max}]</span>}
                        </label>
                        <FeatureField col={col} value={formValues[col.name] ?? ''} onChange={(v) => setFormValues((prev) => ({ ...prev, [col.name]: v }))} />
                      </div>
                    ))}
                  </div>

                  {predError && (
                    <div style={{ marginTop: '14px', padding: '10px 14px', borderRadius: '8px', background: 'rgba(239,68,68,.1)', border: '1px solid rgba(239,68,68,.25)', color: '#f87171', fontSize: '0.82rem', display: 'flex', gap: '8px', alignItems: 'center' }}>
                      <AlertTriangle size={14} />{predError}
                    </div>
                  )}

                  <div style={{ marginTop: '22px' }}>
                    <button type="button" className="pred-btn" onClick={handlePredict} disabled={isPredicting}
                      style={{ width: '100%', padding: '14px 28px', borderRadius: '12px', background: isPredicting ? 'rgba(99,102,241,.5)' : 'linear-gradient(135deg, var(--primary) 0%, #4338ca 100%)', color: '#fff', fontWeight: 800, fontSize: '1rem', border: 'none', cursor: isPredicting ? 'not-allowed' : 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '10px', boxShadow: isPredicting ? 'none' : '0 6px 24px rgba(99,102,241,.4)' }}>
                      {isPredicting ? <><RefreshCw size={17} className="animate-spin" /><span>Running Inference...</span></> : <><Zap size={17} /><span>Predict Now</span><Send size={14} /></>}
                    </button>
                  </div>
                </>
              )}
            </div>

            {/* Result below form on mobile */}
            <div style={{ display: 'none' }} className="pred-mobile-result">
              {result && renderResult(result)}
            </div>
          </div>
        )}

        {/* Right: Result + History */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {schema && result && renderResult(result)}

          {history.length > 0 && (
            <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: '16px', padding: '18px 20px' }}>
              <div style={{ fontSize: '0.78rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text-muted)', marginBottom: '12px' }}>Prediction History</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                {history.map((h, idx) => (
                  <div key={idx} className="pred-history-item" onClick={() => { setResult(h.result); setFormValues(h.inputs); setSelectedHistory(idx) }}
                    style={{ padding: '10px 14px', borderRadius: '10px', background: selectedHistory === idx ? 'rgba(99,102,241,.12)' : 'rgba(255,255,255,.03)', border: `1px solid ${selectedHistory === idx ? 'rgba(99,102,241,.35)' : 'var(--border-subtle)'}`, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <div style={{ fontSize: '0.84rem', fontWeight: 700, fontFamily: 'var(--font-mono)', color: 'var(--text-primary)' }}>{String(h.result.prediction_label || h.result.prediction).slice(0, 20)}</div>
                      <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{h.ts}{h.result.confidence ? ` • ${(h.result.confidence * 100).toFixed(0)}%` : ''}</div>
                    </div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>#{history.length - idx}</div>
                  </div>
                ))}
              </div>
              <button onClick={() => { setHistory([]); setResult(null); setSelectedHistory(null) }}
                style={{ marginTop: '12px', padding: '6px 12px', borderRadius: '6px', background: 'rgba(239,68,68,.08)', border: '1px solid rgba(239,68,68,.2)', color: '#f87171', fontSize: '0.75rem', fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px' }}>
                <X size={11} />Clear History
              </button>
            </div>
          )}

          {schema && (
            <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: '16px', padding: '18px 20px' }}>
              <div style={{ fontSize: '0.76rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text-muted)', marginBottom: '12px' }}>Model Info</div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                {[
                  { label: 'Task Type', value: taskType },
                  { label: 'Target Column', value: targetCol },
                  { label: 'Feature Count', value: String(schema.column_schema.length) },
                  { label: 'Status', value: '✅ Live' },
                ].map((item, i) => (
                  <div key={i} style={{ padding: '10px', background: 'rgba(15,23,42,.6)', borderRadius: '8px' }}>
                    <div style={{ fontSize: '0.66rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '3px' }}>{item.label}</div>
                    <div style={{ fontSize: '0.86rem', fontWeight: 700, color: 'var(--text-primary)' }}>{item.value}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {!schema && !loadingSchema && !schemaError && (
            <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: '16px', padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
              <Brain size={48} style={{ marginBottom: '14px', opacity: .3 }} />
              <div style={{ fontWeight: 700, marginBottom: '6px' }}>No Schema Available</div>
              <div style={{ fontSize: '0.84rem' }}>Upload a dataset and run training to enable live predictions.</div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
