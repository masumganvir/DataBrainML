import React, { useState, useRef, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Upload,
  Sparkles,
  ChevronDown,
  ChevronUp,
  Settings2,
  FileSpreadsheet,
  AlertCircle,
  CheckCircle2,
  Sliders,
  Cpu,
  Database,
  ArrowRight,
  Layers,
  Search,
  RefreshCw,
  Zap,
  Brain,
  BarChart3,
  Shield,
  FlaskConical,
  X,
  Play,
  ChevronRight,
} from 'lucide-react'
import { projectsApi } from '../../services/api'
import { authStore } from '../../services/authStore'

/* ────────────────────────────────────────────────────────────────
   Inline global keyframes — injected once into document head
──────────────────────────────────────────────────────────────── */
const STYLE_ID = 'new-project-animations'
if (typeof document !== 'undefined' && !document.getElementById(STYLE_ID)) {
  const style = document.createElement('style')
  style.id = STYLE_ID
  style.textContent = `
    @keyframes floatBall {
      0%,100% { transform: translate(0, 0) scale(1); }
      33% { transform: translate(40px, -60px) scale(1.08); }
      66% { transform: translate(-30px, 40px) scale(0.95); }
    }
    @keyframes orbitRing {
      from { transform: rotate(0deg); }
      to { transform: rotate(360deg); }
    }
    @keyframes pulseGlow {
      0%,100% { box-shadow: 0 0 0 0 rgba(99,102,241,0.4); }
      50% { box-shadow: 0 0 0 16px rgba(99,102,241,0); }
    }
    @keyframes shimmer {
      0% { background-position: -200% center; }
      100% { background-position: 200% center; }
    }
    @keyframes slideUp {
      from { opacity: 0; transform: translateY(24px); }
      to { opacity: 1; transform: translateY(0); }
    }
    @keyframes fadeIn {
      from { opacity: 0; }
      to { opacity: 1; }
    }
    @keyframes progressPulse {
      0%,100% { opacity: 1; }
      50% { opacity: 0.6; }
    }
    @keyframes checkPop {
      0% { transform: scale(0); opacity: 0; }
      60% { transform: scale(1.2); }
      100% { transform: scale(1); opacity: 1; }
    }
    @keyframes spinSlow {
      from { transform: rotate(0deg); }
      to { transform: rotate(360deg); }
    }
    .np-slide-up { animation: slideUp 0.5s cubic-bezier(0.16,1,0.3,1) both; }
    .np-fade-in { animation: fadeIn 0.4s ease both; }
    .np-check-pop { animation: checkPop 0.45s cubic-bezier(0.34,1.56,0.64,1) both; }
    .np-spin-slow { animation: spinSlow 3s linear infinite; }
    .np-card:hover { transform: translateY(-2px); box-shadow: 0 12px 40px rgba(0,0,0,0.35) !important; }
    .np-card { transition: transform 0.25s ease, box-shadow 0.25s ease; }
    .np-btn-glow:not(:disabled):hover {
      transform: translateY(-2px) scale(1.01);
      box-shadow: 0 14px 36px rgba(99,102,241,0.55) !important;
    }
    .np-btn-glow { transition: all 0.2s cubic-bezier(0.16,1,0.3,1); }
    .np-input:focus { border-color: rgba(99,102,241,0.7) !important; box-shadow: 0 0 0 3px rgba(99,102,241,0.15); }
    .np-input { transition: border-color 0.15s, box-shadow 0.15s; }
    .np-tag:hover { background: rgba(99,102,241,0.25) !important; transform: scale(1.05); }
    .np-tag { transition: all 0.15s ease; cursor: pointer; }
    .np-drop:hover { border-color: var(--primary) !important; background: rgba(99,102,241,0.06) !important; }
    .np-drop { transition: all 0.2s ease; }
    .np-feature-pill:hover { background: rgba(99,102,241,0.14) !important; color: #fff !important; }
    .np-feature-pill { transition: all 0.15s ease; }
  `
  document.head.appendChild(style)
}

/* ────────────────────────────────────────────────────────────────
   Floating ambient particles background
──────────────────────────────────────────────────────────────── */
function AmbientParticles() {
  const balls = [
    { w: 320, h: 320, top: '-60px', left: '-80px', color: 'rgba(99,102,241,0.12)', delay: '0s', dur: '14s' },
    { w: 220, h: 220, top: '40%', right: '-60px', color: 'rgba(16,185,129,0.08)', delay: '-5s', dur: '18s' },
    { w: 260, h: 260, bottom: '-40px', left: '40%', color: 'rgba(139,92,246,0.1)', delay: '-9s', dur: '22s' },
    { w: 160, h: 160, top: '20%', left: '60%', color: 'rgba(99,102,241,0.07)', delay: '-3s', dur: '16s' },
  ]
  return (
    <div style={{ position: 'fixed', inset: 0, pointerEvents: 'none', overflow: 'hidden', zIndex: 0 }}>
      {balls.map((b, i) => (
        <div
          key={i}
          style={{
            position: 'absolute',
            width: b.w,
            height: b.h,
            top: b.top,
            left: b.left,
            right: (b as any).right,
            bottom: (b as any).bottom,
            borderRadius: '50%',
            background: `radial-gradient(circle, ${b.color} 0%, transparent 70%)`,
            animationName: 'floatBall',
            animationDuration: b.dur,
            animationDelay: b.delay,
            animationTimingFunction: 'ease-in-out',
            animationIterationCount: 'infinite',
            filter: 'blur(2px)',
          }}
        />
      ))}
    </div>
  )
}

/* ────────────────────────────────────────────────────────────────
   Main Component
──────────────────────────────────────────────────────────────── */
export function NewProject() {
  const navigate = useNavigate()

  // Project Configuration
  const [projectName, setProjectName] = useState('')
  const [prompt, setPrompt] = useState('')
  const [isAdvancedOpen, setIsAdvancedOpen] = useState(false)

  // Advanced Options
  const [targetColumn, setTargetColumn] = useState('Auto')
  const [taskType, setTaskType] = useState('Auto Detect')
  const [optimizationMetric, setOptimizationMetric] = useState('Auto')
  const [computeBudget, setComputeBudget] = useState('Balanced')
  const [cvFolds, setCvFolds] = useState(5)
  const [deepLearning, setDeepLearning] = useState('Auto')

  // Dataset State
  const [file, setFile] = useState<File | null>(null)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'uploading' | 'profiling' | 'ready' | 'error'>('idle')
  const [errorMessage, setErrorMessage] = useState('')
  const [datasetMeta, setDatasetMeta] = useState<any>(null)
  const [previewData, setPreviewData] = useState<{ columns: string[]; rows: any[]; total_rows: number } | null>(null)
  const [previewSearch, setPreviewSearch] = useState('')
  const [isDragging, setIsDragging] = useState(false)
  const [isStarting, setIsStarting] = useState(false)
  const [createdProjectId, setCreatedProjectId] = useState<string>('')

  // AI Project Planner & Human Approval Modals
  const [isProposalModalOpen, setIsProposalModalOpen] = useState(false)
  const [aiProposal, setAiProposal] = useState<any>(null)
  const [isEditingProposal, setIsEditingProposal] = useState(false)
  const [duplicateWarning, setDuplicateWarning] = useState<any>(null)
  const [isPlanning, setIsPlanning] = useState(false)

  const fileInputRef = useRef<HTMLInputElement>(null)

  // ── Create project immediately using explicit name (avoids React closure state race) ──
  const ensureProjectCreated = async (customName?: string): Promise<string> => {
    if (createdProjectId) return createdProjectId
    const activeName = (customName || projectName || 'New ML Project').trim()
    const activePrompt = prompt.trim() || `Analyze this dataset and build a high-performance predictive model.`

    const proj = await projectsApi.create({
      name: activeName,
      description: `Autonomous ML analysis for ${activeName}`,
      prompt: activePrompt,
      configuration: {
        target_column: targetColumn,
        task_type: taskType,
        optimization_metric: optimizationMetric,
        compute_budget: computeBudget,
        cv_folds: cvFolds,
        deep_learning: deepLearning,
      },
    })
    setCreatedProjectId(proj.id)
    authStore.setCurrentProject(proj)
    return proj.id
  }

  // Process Dataset File
  const handleFileUpload = async (selectedFile: File, forceUpload: boolean = false) => {
    setFile(selectedFile)
    setUploadStatus('uploading')
    setErrorMessage('')
    setDuplicateWarning(null)

    // Derive project name from file
    const cleanName = selectedFile.name.replace(/\.[^/.]+$/, '').replace(/[_-]/g, ' ')
    const titleCase = cleanName
      .split(' ')
      .filter(Boolean)
      .map((w) => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase())
      .join(' ')

    const activeProjectName = (projectName.trim() || titleCase || 'New ML Project').trim()
    if (!projectName.trim() && titleCase) {
      setProjectName(titleCase)
    }

    // Check if image file
    const isImageFile = selectedFile.type.startsWith('image/') || /\.(png|jpe?g|webp|gif)$/i.test(selectedFile.name)
    if (isImageFile) {
      setTaskType('Image Classification')
      setTargetColumn('class_label')
      setPrompt(`Classify uploaded images into visual target categories using deep vision models.`)
    }

    try {
      setUploadStatus('profiling')
      const projId = await ensureProjectCreated(activeProjectName)

      const result = await projectsApi.uploadDataset(projId, selectedFile, (pct) => {
        setUploadProgress(pct)
      })

      if (result.duplicate && !forceUpload) {
        setDuplicateWarning(result)
        setUploadStatus('idle')
        return
      }

      if (result.dataset || result.row_count) {
        const meta = result.dataset || result
        setDatasetMeta(meta)
        setPreviewData(result.preview || null)
        setUploadStatus('ready')

        const recTarget = meta.recommended_target || targetColumn
        if (recTarget && recTarget !== 'Auto') {
          setTargetColumn(recTarget)
        }
        if (meta.recommended_task && meta.recommended_task !== 'Auto Detect') {
          const fmt = meta.recommended_task.charAt(0).toUpperCase() + meta.recommended_task.slice(1)
          setTaskType(fmt)
        }

        if (!isImageFile) {
          setPrompt(
            `Analyze this dataset to predict '${recTarget || 'target'}' using an autonomous ML pipeline. Maximize generalization performance and explain feature contributions.`
          )
        }

        // Proactively generate AI Project Plan proposal
        setIsPlanning(true)
        try {
          const planRes = await projectsApi.proposePlan(projId, {
            prompt: prompt.trim() || `Analyze this dataset to predict '${recTarget || 'target'}'`,
            custom_name: activeProjectName,
          })
          if (planRes?.proposal) {
            setAiProposal(planRes.proposal)
            setIsProposalModalOpen(true)
          }
        } catch (planErr) {
          console.warn('Could not generate plan proposal:', planErr)
        } finally {
          setIsPlanning(false)
        }
      } else {
        setUploadStatus('ready')
      }
    } catch (err: any) {
      setUploadStatus('error')
      setErrorMessage(err.message || 'Failed to upload and profile dataset')
    }
  }

  // Load sample dataset
  const handleLoadSample = async (sampleName: string) => {
    setUploadStatus('uploading')
    setErrorMessage('')
    try {
      let dummyCsv = ''
      let derivedTitle = 'Sample Dataset Analysis'
      let derivedPrompt = 'Train high-performance predictive model on benchmark data.'
      let derivedTarget = 'target'
      let derivedTask = 'Classification'

      if (sampleName === 'telecom_churn') {
        derivedTitle = 'Telecom Customer Churn'
        derivedPrompt = 'Analyze subscriber behavior to predict churn and prioritize high-risk accounts.'
        derivedTarget = 'churn'
        derivedTask = 'Classification'
        dummyCsv =
          'customer_id,age,tenure_months,monthly_charges,total_charges,payment_type,support_calls,churn\n' +
          Array.from({ length: 120 }, (_, i) => {
            const churn = Math.random() > 0.72 ? 1 : 0
            const charges = (Math.random() * 80 + 20).toFixed(2)
            const tenure = Math.floor(Math.random() * 60) + 1
            const total = (parseFloat(charges) * tenure).toFixed(2)
            const payment = ['Credit Card', 'Bank Transfer', 'Electronic Check'][i % 3]
            return `CUST_${1000 + i},${Math.floor(Math.random() * 50) + 20},${tenure},${charges},${total},${payment},${Math.floor(Math.random() * 5)},${churn}`
          }).join('\n')
      } else if (sampleName === 'financial_fraud') {
        derivedTitle = 'Financial Fraud Detection'
        derivedPrompt = 'Detect fraudulent transactions in high-volume payment streams with low false positive rate.'
        derivedTarget = 'is_fraud'
        derivedTask = 'Classification'
        dummyCsv =
          'transaction_id,amount,transaction_hour,distance_from_home,used_pin_number,online_order,high_risk_merchant,is_fraud\n' +
          Array.from({ length: 120 }, (_, i) => {
            const fraud = Math.random() > 0.88 ? 1 : 0
            const amount = fraud ? (Math.random() * 900 + 100).toFixed(2) : (Math.random() * 90 + 5).toFixed(2)
            const hour = Math.floor(Math.random() * 24)
            const dist = (Math.random() * 80).toFixed(1)
            const pin = Math.random() > 0.5 ? 1 : 0
            const online = Math.random() > 0.4 ? 1 : 0
            const highRisk = fraud ? (Math.random() > 0.3 ? 1 : 0) : (Math.random() > 0.9 ? 1 : 0)
            return `TX_${5000 + i},${amount},${hour},${dist},${pin},${online},${highRisk},${fraud}`
          }).join('\n')
      } else if (sampleName === 'student_performance') {
        derivedTitle = 'Student Exam Performance'
        derivedPrompt = 'Predict final student exam score based on study hours, attendance, and previous academic records.'
        derivedTarget = 'exam_score'
        derivedTask = 'Regression'
        dummyCsv =
          'student_id,hours_studied,attendance_pct,parental_education,tutoring_sessions,previous_exam_score,exam_score\n' +
          Array.from({ length: 120 }, (_, i) => {
            const hours = (Math.random() * 35 + 5).toFixed(1)
            const att = Math.floor(Math.random() * 30 + 70)
            const parent = ['High School', 'Bachelor', 'Master', 'Doctorate'][i % 4]
            const tutor = Math.floor(Math.random() * 6)
            const prev = Math.floor(Math.random() * 40 + 55)
            const exam = Math.min(100, Math.max(30, Math.round(prev * 0.4 + parseFloat(hours) * 1.2 + att * 0.3 + tutor * 2 + (Math.random() * 8 - 4))))
            return `STU_${2000 + i},${hours},${att},${parent},${tutor},${prev},${exam}`
          }).join('\n')
      } else if (sampleName === 'house_prices') {
        derivedTitle = 'Real Estate House Prices'
        derivedPrompt = 'Forecast residential property prices based on square footage, bedrooms, year built, and neighborhood tier.'
        derivedTarget = 'price_k'
        derivedTask = 'Regression'
        dummyCsv =
          'house_id,square_feet,bedrooms,bathrooms,neighborhood_tier,year_built,garage_cars,price_k\n' +
          Array.from({ length: 120 }, (_, i) => {
            const sqft = Math.floor(Math.random() * 2500 + 800)
            const bed = Math.floor(Math.random() * 4 + 1)
            const bath = Math.floor(Math.random() * 3 + 1)
            const tier = ['Tier 1', 'Tier 2', 'Tier 3'][i % 3]
            const year = Math.floor(Math.random() * 40 + 1980)
            const garage = Math.floor(Math.random() * 3)
            const price = Math.round(sqft * 0.18 + bed * 15 + (year - 1980) * 2 + garage * 10 + (i % 3 === 0 ? 80 : 20))
            return `PROP_${3000 + i},${sqft},${bed},${bath},${tier},${year},${garage},${price}`
          }).join('\n')
      } else if (sampleName === 'image_classification') {
        derivedTitle = 'Visual Object & Defect Classifier'
        derivedPrompt = 'Train deep convolutional / Vision Transformer models to classify visual classes with high top-1 accuracy.'
        derivedTarget = 'class_label'
        derivedTask = 'Image Classification'
        dummyCsv =
          'image_id,width,height,channels,sharpness_score,ambient_light,class_label\n' +
          Array.from({ length: 120 }, (_, i) => {
            const classes = ['Defect Free', 'Surface Scratch', 'Micro Crack', 'Color Mismatch']
            const label = classes[i % classes.length]
            const sharpness = (Math.random() * 40 + 60).toFixed(1)
            const light = (Math.random() * 50 + 50).toFixed(1)
            return `IMG_${4000 + i},224,224,3,${sharpness},${light},${label}`
          }).join('\n')
      }

      setProjectName(derivedTitle)
      setPrompt(derivedPrompt)
      setTargetColumn(derivedTarget)
      setTaskType(derivedTask)

      const sampleFile = new File([dummyCsv], `${sampleName}.csv`, { type: 'text/csv' })
      await handleFileUpload(sampleFile)
    } catch (err: any) {
      setErrorMessage(err.message)
      setUploadStatus('error')
    }
  }

  // Drag & Drop
  const handleDragOver = (e: React.DragEvent) => { e.preventDefault(); setIsDragging(true) }
  const handleDragLeave = () => setIsDragging(false)
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault(); setIsDragging(false)
    if (e.dataTransfer.files?.[0]) handleFileUpload(e.dataTransfer.files[0])
  }

  // Primary CTA
  const handleStartAnalysis = async () => {
    setIsStarting(true)
    setErrorMessage('')
    try {
      let projId = createdProjectId

      // If project wasn't pre-created (no upload), create it now
      if (!projId) {
        const proj = await projectsApi.create({
          name: projectName,
          description: `Autonomous ML analysis for ${projectName}`,
          prompt,
          configuration: {
            target_column: targetColumn,
            task_type: taskType,
            optimization_metric: optimizationMetric,
            compute_budget: computeBudget,
            cv_folds: cvFolds,
            deep_learning: deepLearning,
            dataset_name: datasetMeta?.filename || file?.name || 'dataset.csv',
            dataset_rows: datasetMeta?.row_count || 1000,
            dataset_cols: datasetMeta?.column_count || 14,
          },
        })
        projId = proj.id
        authStore.setCurrentProject(proj)
      } else {
        // Update project with latest config
        await projectsApi.update(projId, {
          name: projectName,
          configuration: {
            target_column: targetColumn,
            task_type: taskType,
            optimization_metric: optimizationMetric,
            compute_budget: computeBudget,
            cv_folds: cvFolds,
            deep_learning: deepLearning,
            dataset_name: datasetMeta?.filename || file?.name || 'dataset.csv',
            dataset_rows: datasetMeta?.row_count || 1000,
            dataset_cols: datasetMeta?.column_count || 14,
          },
        }).catch(() => {}) // non-fatal
      }

      // Start asynchronous LangGraph run
      const runResult = await projectsApi.startRun(projId, {
        prompt,
        configuration: {
          target_column: targetColumn,
          task_type: taskType,
          optimization_metric: optimizationMetric,
          compute_budget: computeBudget,
          cv_folds: cvFolds,
          deep_learning: deepLearning,
        },
      })

      navigate(`/projects/${projId}/run/${runResult.run_id}`)
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to start AI analysis run')
      setIsStarting(false)
    }
  }

  // AI Project Planner actions
  const handleApproveProposal = async () => {
    if (!createdProjectId || !aiProposal) return
    try {
      await projectsApi.approvePlan(createdProjectId, { proposal: aiProposal })
      if (aiProposal.project_name) setProjectName(aiProposal.project_name)
      if (aiProposal.target_candidate) setTargetColumn(aiProposal.target_candidate)
      if (aiProposal.task_type) {
        const fmt = aiProposal.task_type.charAt(0).toUpperCase() + aiProposal.task_type.slice(1)
        setTaskType(fmt)
      }
      setIsProposalModalOpen(false)
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to approve AI proposal')
    }
  }

  const handleRegenerateProposal = async () => {
    if (!createdProjectId) return
    setIsPlanning(true)
    try {
      const res = await projectsApi.regeneratePlan(createdProjectId, {
        prompt: prompt.trim() || undefined,
        custom_name: projectName.trim() || undefined,
      })
      if (res?.proposal) {
        setAiProposal(res.proposal)
      }
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to regenerate plan')
    } finally {
      setIsPlanning(false)
    }
  }

  const handleForceUploadDuplicate = async () => {
    if (file) {
      const currentFile = file
      setDuplicateWarning(null)
      await handleFileUpload(currentFile, true)
    }
  }

  const filteredRows = previewData?.rows.filter((row: any) => {
    if (!previewSearch) return true
    return Object.values(row).some((v) => String(v).toLowerCase().includes(previewSearch.toLowerCase()))
  })

  const agentPipeline = [
    { icon: Database, label: 'Data Profiler', color: '#6366f1' },
    { icon: Shield, label: 'Quality Auditor', color: '#10b981' },
    { icon: BarChart3, label: 'EDA Agent', color: '#f59e0b' },
    { icon: Sliders, label: 'Preprocessor', color: '#8b5cf6' },
    { icon: Zap, label: 'Feature Eng.', color: '#ec4899' },
    { icon: Brain, label: 'Model Trainer', color: '#06b6d4' },
    { icon: FlaskConical, label: 'Evaluator', color: '#84cc16' },
    { icon: Sparkles, label: 'Orchestrator', color: '#f97316' },
  ]

  return (
    <div style={{ position: 'relative', minHeight: '100vh' }}>
      <AmbientParticles />

      <div
        className="np-slide-up"
        style={{
          maxWidth: '1360px',
          margin: '0 auto',
          display: 'flex',
          flexDirection: 'column',
          gap: '28px',
          paddingBottom: '80px',
          position: 'relative',
          zIndex: 1,
        }}
      >
        {/* ── HERO HEADER ── */}
        <div
          style={{
            background: 'linear-gradient(135deg, rgba(99,102,241,0.08) 0%, rgba(139,92,246,0.06) 50%, rgba(16,185,129,0.04) 100%)',
            border: '1px solid rgba(99,102,241,0.2)',
            borderRadius: '24px',
            padding: '36px 40px',
            position: 'relative',
            overflow: 'hidden',
          }}
        >
          {/* Decorative orbit ring */}
          <div
            style={{
              position: 'absolute',
              top: '-80px',
              right: '-80px',
              width: '280px',
              height: '280px',
              borderRadius: '50%',
              border: '1px solid rgba(99,102,241,0.15)',
              animationName: 'orbitRing',
              animationDuration: '20s',
              animationTimingFunction: 'linear',
              animationIterationCount: 'infinite',
            }}
          />
          <div
            style={{
              position: 'absolute',
              top: '-40px',
              right: '-40px',
              width: '200px',
              height: '200px',
              borderRadius: '50%',
              border: '1px dashed rgba(139,92,246,0.12)',
              animationName: 'orbitRing',
              animationDuration: '14s',
              animationTimingFunction: 'linear',
              animationIterationCount: 'infinite',
              animationDirection: 'reverse',
            }}
          />

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '24px' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px' }}>
                <div
                  style={{
                    background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
                    borderRadius: '10px',
                    width: '38px',
                    height: '38px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    boxShadow: '0 4px 14px rgba(99,102,241,0.4)',
                    animationName: 'pulseGlow',
                    animationDuration: '3s',
                    animationTimingFunction: 'ease-in-out',
                    animationIterationCount: 'infinite',
                  }}
                >
                  <Sparkles size={20} color="#fff" />
                </div>
                <span
                  style={{
                    fontSize: '0.72rem',
                    textTransform: 'uppercase',
                    letterSpacing: '0.12em',
                    fontWeight: 800,
                    color: 'var(--primary-light)',
                    background: 'rgba(99,102,241,0.12)',
                    padding: '3px 10px',
                    borderRadius: '6px',
                    border: '1px solid rgba(99,102,241,0.25)',
                  }}
                >
                  Autonomous DataLab
                </span>
                <ChevronRight size={14} color="var(--text-muted)" />
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>/workspace/new</span>
              </div>

              <h1
                style={{
                  fontSize: '2.4rem',
                  fontWeight: 900,
                  margin: '0 0 10px 0',
                  letterSpacing: '-0.03em',
                  background: 'linear-gradient(135deg, #fff 0%, rgba(255,255,255,0.75) 100%)',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  backgroundClip: 'text',
                }}
              >
                Create New ML Project
              </h1>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', lineHeight: 1.6, margin: 0, maxWidth: '680px' }}>
                Upload your dataset and describe what you want to predict. The <strong style={{ color: 'var(--primary-light)' }}>17-stage LangGraph orchestrator</strong> handles profiling, cleaning, feature engineering, model selection, training, and report generation — autonomously.
              </p>
            </div>

            {/* Agent Pipeline Visualization */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', alignItems: 'flex-end' }}>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.1em', fontWeight: 700 }}>
                Agents Ready
              </div>
              <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', maxWidth: '340px', justifyContent: 'flex-end' }}>
                {agentPipeline.map((agent, i) => {
                  const Icon = agent.icon
                  return (
                    <div
                      key={i}
                      className="np-feature-pill"
                      title={agent.label}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '5px',
                        padding: '5px 10px',
                        borderRadius: '100px',
                        background: `${agent.color}14`,
                        border: `1px solid ${agent.color}30`,
                        color: agent.color,
                        fontSize: '0.7rem',
                        fontWeight: 600,
                      }}
                    >
                      <Icon size={11} />
                      <span>{agent.label}</span>
                    </div>
                  )
                })}
              </div>
            </div>
          </div>
        </div>

        {/* ── ERROR BANNER ── */}
        {errorMessage && (
          <div
            className="np-fade-in"
            style={{
              padding: '14px 20px',
              borderRadius: '14px',
              background: 'linear-gradient(135deg, rgba(239,68,68,0.12), rgba(239,68,68,0.06))',
              border: '1px solid rgba(239,68,68,0.35)',
              color: '#fca5a5',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: '12px',
              fontSize: '0.9rem',
              boxShadow: '0 4px 20px rgba(239,68,68,0.12)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <AlertCircle size={18} color="#f87171" />
              <span>{errorMessage}</span>
            </div>
            <button
              onClick={() => setErrorMessage('')}
              style={{ background: 'none', border: 'none', color: '#f87171', cursor: 'pointer', padding: '2px' }}
            >
              <X size={16} />
            </button>
          </div>
        )}

        {/* ── MAIN 2-COLUMN LAYOUT ── */}
        <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1.75fr) minmax(0, 1.25fr)', gap: '24px' }}>
          {/* ╔════ LEFT COLUMN ════╗ */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {/* A. Project Name */}
            <div
              className="np-card"
              style={{
                background: 'rgba(15,23,42,0.7)',
                backdropFilter: 'blur(20px)',
                border: '1px solid rgba(99,102,241,0.15)',
                borderRadius: '20px',
                padding: '24px 28px',
                boxShadow: '0 4px 24px rgba(0,0,0,0.2)',
              }}
            >
              <label
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  fontSize: '0.72rem',
                  fontWeight: 800,
                  color: 'var(--primary-light)',
                  textTransform: 'uppercase',
                  letterSpacing: '0.1em',
                  marginBottom: '12px',
                }}
              >
                <div style={{ width: '20px', height: '20px', borderRadius: '6px', background: 'rgba(99,102,241,0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.65rem', fontWeight: 900 }}>A</div>
                Project Name
              </label>
              <input
                className="np-input"
                type="text"
                value={projectName}
                onChange={(e) => setProjectName(e.target.value)}
                placeholder="e.g. Credit Card Fraud Detection, House Price Prediction, Sales Forecasting"
                style={{
                  width: '100%',
                  padding: '13px 18px',
                  borderRadius: '12px',
                  background: 'rgba(15,23,42,0.6)',
                  border: '1px solid rgba(255,255,255,0.08)',
                  color: 'var(--text-primary)',
                  fontSize: '1.05rem',
                  fontWeight: 700,
                  outline: 'none',
                  boxSizing: 'border-box',
                }}
              />
            </div>

            {/* B. Dataset Upload */}
            <div
              className="np-card"
              style={{
                background: 'rgba(15,23,42,0.7)',
                backdropFilter: 'blur(20px)',
                border: '1px solid rgba(99,102,241,0.15)',
                borderRadius: '20px',
                padding: '24px 28px',
                boxShadow: '0 4px 24px rgba(0,0,0,0.2)',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <label
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    fontSize: '0.72rem',
                    fontWeight: 800,
                    color: 'var(--primary-light)',
                    textTransform: 'uppercase',
                    letterSpacing: '0.1em',
                  }}
                >
                  <div style={{ width: '20px', height: '20px', borderRadius: '6px', background: 'rgba(99,102,241,0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.65rem', fontWeight: 900 }}>B</div>
                  Dataset Upload
                </label>
                <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                  <button
                    type="button"
                    onClick={() => handleLoadSample('telecom_churn')}
                    disabled={uploadStatus === 'uploading' || uploadStatus === 'profiling'}
                    style={{
                      fontSize: '0.72rem',
                      padding: '5px 11px',
                      borderRadius: '100px',
                      background: 'linear-gradient(135deg, rgba(99,102,241,0.15), rgba(99,102,241,0.08))',
                      border: '1px solid rgba(99,102,241,0.3)',
                      color: 'var(--primary-light)',
                      cursor: 'pointer',
                      fontWeight: 700,
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px',
                    }}
                  >
                    <Zap size={11} /> Churn
                  </button>
                  <button
                    type="button"
                    onClick={() => handleLoadSample('financial_fraud')}
                    disabled={uploadStatus === 'uploading' || uploadStatus === 'profiling'}
                    style={{
                      fontSize: '0.72rem',
                      padding: '5px 11px',
                      borderRadius: '100px',
                      background: 'linear-gradient(135deg, rgba(16,185,129,0.15), rgba(16,185,129,0.08))',
                      border: '1px solid rgba(16,185,129,0.3)',
                      color: '#34d399',
                      cursor: 'pointer',
                      fontWeight: 700,
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px',
                    }}
                  >
                    <Shield size={11} /> Fraud
                  </button>
                  <button
                    type="button"
                    onClick={() => handleLoadSample('student_performance')}
                    disabled={uploadStatus === 'uploading' || uploadStatus === 'profiling'}
                    style={{
                      fontSize: '0.72rem',
                      padding: '5px 11px',
                      borderRadius: '100px',
                      background: 'linear-gradient(135deg, rgba(245,158,11,0.15), rgba(245,158,11,0.08))',
                      border: '1px solid rgba(245,158,11,0.3)',
                      color: '#fbbf24',
                      cursor: 'pointer',
                      fontWeight: 700,
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px',
                    }}
                  >
                    <FlaskConical size={11} /> Student Exams
                  </button>
                  <button
                    type="button"
                    onClick={() => handleLoadSample('house_prices')}
                    disabled={uploadStatus === 'uploading' || uploadStatus === 'profiling'}
                    style={{
                      fontSize: '0.72rem',
                      padding: '5px 11px',
                      borderRadius: '100px',
                      background: 'linear-gradient(135deg, rgba(139,92,246,0.15), rgba(139,92,246,0.08))',
                      border: '1px solid rgba(139,92,246,0.3)',
                      color: '#c084fc',
                      cursor: 'pointer',
                      fontWeight: 700,
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px',
                    }}
                  >
                    <BarChart3 size={11} /> House Prices
                  </button>
                  <button
                    type="button"
                    onClick={() => handleLoadSample('image_classification')}
                    disabled={uploadStatus === 'uploading' || uploadStatus === 'profiling'}
                    style={{
                      fontSize: '0.72rem',
                      padding: '5px 11px',
                      borderRadius: '100px',
                      background: 'linear-gradient(135deg, rgba(236,72,153,0.15), rgba(236,72,153,0.08))',
                      border: '1px solid rgba(236,72,153,0.3)',
                      color: '#f472b6',
                      cursor: 'pointer',
                      fontWeight: 700,
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px',
                    }}
                  >
                    <Sparkles size={11} /> Image Vision
                  </button>
                </div>
              </div>

              {/* Drag & Drop Zone */}
              <div
                className="np-drop"
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                style={{
                  border: `2px dashed ${isDragging ? '#6366f1' : 'rgba(255,255,255,0.1)'}`,
                  borderRadius: '16px',
                  padding: '40px 20px',
                  textAlign: 'center',
                  background: isDragging
                    ? 'rgba(99,102,241,0.08)'
                    : 'linear-gradient(135deg, rgba(15,23,42,0.5), rgba(30,41,59,0.3))',
                  cursor: 'pointer',
                  position: 'relative',
                  overflow: 'hidden',
                }}
              >
                {/* subtle grid lines */}
                <div
                  style={{
                    position: 'absolute',
                    inset: 0,
                    backgroundImage: 'radial-gradient(rgba(99,102,241,0.06) 1px, transparent 1px)',
                    backgroundSize: '24px 24px',
                    pointerEvents: 'none',
                  }}
                />

                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".csv,.xlsx,.xls,.json,.parquet,.pq,.png,.jpg,.jpeg,.webp,.zip"
                  style={{ display: 'none' }}
                  onChange={(e) => { if (e.target.files?.[0]) handleFileUpload(e.target.files[0]) }}
                />

                <div
                  style={{
                    width: '64px',
                    height: '64px',
                    borderRadius: '50%',
                    background: 'linear-gradient(135deg, rgba(99,102,241,0.2), rgba(139,92,246,0.15))',
                    border: '1px solid rgba(99,102,241,0.3)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    margin: '0 auto 16px auto',
                    boxShadow: '0 8px 24px rgba(99,102,241,0.2)',
                  }}
                >
                  <Upload size={28} color="#818cf8" />
                </div>

                <h3 style={{ fontSize: '1.05rem', fontWeight: 800, margin: '0 0 6px 0', color: '#e2e8f0' }}>
                  DROP YOUR DATASET OR IMAGES HERE
                </h3>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', margin: '0 0 18px 0' }}>
                  CSV • XLSX • JSON • PARQUET • IMAGES (PNG/JPG/ZIP)
                </p>
                <button
                  type="button"
                  style={{
                    background: 'rgba(99,102,241,0.12)',
                    border: '1px solid rgba(99,102,241,0.3)',
                    color: 'var(--primary-light)',
                    padding: '9px 22px',
                    borderRadius: '10px',
                    fontSize: '0.84rem',
                    fontWeight: 700,
                    cursor: 'pointer',
                  }}
                >
                  Browse Files
                </button>
              </div>

              {/* Upload Status Card */}
              {uploadStatus !== 'idle' && (
                <div
                  className="np-slide-up"
                  style={{
                    marginTop: '14px',
                    padding: '16px 18px',
                    borderRadius: '14px',
                    background: uploadStatus === 'error'
                      ? 'rgba(239,68,68,0.08)'
                      : uploadStatus === 'ready'
                      ? 'rgba(16,185,129,0.08)'
                      : 'rgba(99,102,241,0.08)',
                    border: `1px solid ${
                      uploadStatus === 'error'
                        ? 'rgba(239,68,68,0.25)'
                        : uploadStatus === 'ready'
                        ? 'rgba(16,185,129,0.25)'
                        : 'rgba(99,102,241,0.2)'
                    }`,
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      <div
                        style={{
                          width: '36px',
                          height: '36px',
                          borderRadius: '9px',
                          background: 'rgba(99,102,241,0.15)',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                        }}
                      >
                        <FileSpreadsheet size={18} color="#818cf8" />
                      </div>
                      <div>
                        <div style={{ fontSize: '0.88rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                          {file?.name || datasetMeta?.filename || 'Loading...'}
                        </div>
                        <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                          {file ? `${(file.size / 1024).toFixed(1)} KB` : '—'} •{' '}
                          {datasetMeta
                            ? `${datasetMeta.row_count?.toLocaleString()} rows, ${datasetMeta.column_count} cols`
                            : 'Profiling...'}
                        </div>
                      </div>
                    </div>

                    {uploadStatus === 'profiling' && (
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.8rem', color: 'var(--primary-light)' }}>
                        <RefreshCw size={14} className="animate-spin" />
                        <span>Profiling</span>
                      </div>
                    )}
                    {uploadStatus === 'ready' && (
                      <div className="np-check-pop" style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.82rem', color: '#34d399', fontWeight: 700 }}>
                        <CheckCircle2 size={18} />
                        <span>Ready</span>
                      </div>
                    )}
                    {uploadStatus === 'error' && (
                      <span style={{ fontSize: '0.8rem', color: '#f87171', fontWeight: 600 }}>Failed</span>
                    )}
                  </div>

                  {uploadProgress > 0 && uploadProgress < 100 && (
                    <div style={{ marginTop: '12px' }}>
                      <div style={{ width: '100%', height: '6px', background: 'rgba(255,255,255,0.06)', borderRadius: '3px', overflow: 'hidden' }}>
                        <div
                          style={{
                            width: `${uploadProgress}%`,
                            height: '100%',
                            background: 'linear-gradient(90deg, #6366f1, #8b5cf6)',
                            borderRadius: '3px',
                            transition: 'width 0.3s ease',
                            animationName: 'progressPulse',
                            animationDuration: '1s',
                            animationIterationCount: 'infinite',
                          }}
                        />
                      </div>
                      <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '4px', textAlign: 'right' }}>
                        {uploadProgress}%
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* C. Objective Prompt */}
            <div
              className="np-card"
              style={{
                background: 'rgba(15,23,42,0.7)',
                backdropFilter: 'blur(20px)',
                border: '1px solid rgba(99,102,241,0.15)',
                borderRadius: '20px',
                padding: '24px 28px',
                boxShadow: '0 4px 24px rgba(0,0,0,0.2)',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                <label
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    fontSize: '0.72rem',
                    fontWeight: 800,
                    color: 'var(--primary-light)',
                    textTransform: 'uppercase',
                    letterSpacing: '0.1em',
                  }}
                >
                  <div style={{ width: '20px', height: '20px', borderRadius: '6px', background: 'rgba(99,102,241,0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.65rem', fontWeight: 900 }}>C</div>
                  Describe What You Want To Build
                </label>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', background: 'rgba(255,255,255,0.04)', padding: '3px 8px', borderRadius: '6px', border: '1px solid rgba(255,255,255,0.06)' }}>
                  ChatGPT-style intent prompt
                </span>
              </div>

              <textarea
                className="np-input"
                rows={5}
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="e.g. Build an autonomous model with high generalization, optimize F1/RMSE, and explain key feature contributions."
                style={{
                  width: '100%',
                  padding: '14px 18px',
                  borderRadius: '12px',
                  background: 'rgba(15,23,42,0.6)',
                  border: '1px solid rgba(255,255,255,0.08)',
                  color: 'var(--text-primary)',
                  fontSize: '0.92rem',
                  lineHeight: 1.65,
                  outline: 'none',
                  resize: 'vertical',
                  boxSizing: 'border-box',
                  fontFamily: 'inherit',
                }}
              />
              <div style={{ fontSize: '0.76rem', color: 'var(--text-muted)', marginTop: '8px', display: 'flex', alignItems: 'flex-start', gap: '6px' }}>
                <span style={{ fontSize: '0.9rem' }}>💡</span>
                <span>Describe prediction objectives, constraints, preferred metrics, or business context. The orchestrator tailors feature engineering and loss penalties accordingly.</span>
              </div>
            </div>
          </div>

          {/* ╔════ RIGHT COLUMN ════╗ */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {/* Advanced Configuration Panel */}
            <div
              className="np-card"
              style={{
                background: 'rgba(15,23,42,0.7)',
                backdropFilter: 'blur(20px)',
                border: '1px solid rgba(99,102,241,0.15)',
                borderRadius: '20px',
                overflow: 'hidden',
                boxShadow: '0 4px 24px rgba(0,0,0,0.2)',
              }}
            >
              <button
                type="button"
                onClick={() => setIsAdvancedOpen(!isAdvancedOpen)}
                style={{
                  width: '100%',
                  padding: '20px 24px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  background: 'transparent',
                  border: 'none',
                  color: 'var(--text-primary)',
                  cursor: 'pointer',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <div
                    style={{
                      width: '34px',
                      height: '34px',
                      borderRadius: '9px',
                      background: 'linear-gradient(135deg, rgba(99,102,241,0.2), rgba(139,92,246,0.15))',
                      border: '1px solid rgba(99,102,241,0.25)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}
                  >
                    <Settings2 size={16} color="#818cf8" />
                  </div>
                  <div style={{ textAlign: 'left' }}>
                    <div style={{ fontWeight: 800, fontSize: '0.92rem' }}>Advanced Configuration</div>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '1px' }}>Optional • AUTO by default</div>
                  </div>
                </div>
                <div
                  style={{
                    width: '28px',
                    height: '28px',
                    borderRadius: '8px',
                    background: 'rgba(255,255,255,0.05)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    transition: 'transform 0.2s ease',
                    transform: isAdvancedOpen ? 'rotate(180deg)' : 'rotate(0)',
                  }}
                >
                  <ChevronDown size={16} />
                </div>
              </button>

              {isAdvancedOpen && (
                <div
                  className="np-slide-up"
                  style={{ padding: '0 24px 24px 24px', display: 'flex', flexDirection: 'column', gap: '14px' }}
                >
                  <div style={{ height: '1px', background: 'rgba(255,255,255,0.06)' }} />

                  {/* Target Column */}
                  <div>
                    <label style={{ display: 'block', fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: '6px', fontWeight: 700 }}>TARGET COLUMN</label>
                    <select
                      value={targetColumn}
                      onChange={(e) => setTargetColumn(e.target.value)}
                      style={{
                        width: '100%',
                        padding: '10px 14px',
                        borderRadius: '10px',
                        background: 'rgba(15,23,42,0.6)',
                        border: '1px solid rgba(255,255,255,0.08)',
                        color: 'var(--text-primary)',
                        fontSize: '0.85rem',
                        outline: 'none',
                      }}
                    >
                      <option value="Auto">⚡ Auto Detect Target</option>
                      {datasetMeta?.columns?.map((col: any) => (
                        <option key={col.name} value={col.name}>{col.name} ({col.dtype})</option>
                      ))}
                    </select>
                  </div>

                  {/* Task Type + Metric */}
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                    <div>
                      <label style={{ display: 'block', fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: '6px', fontWeight: 700 }}>TASK TYPE</label>
                      <select
                        value={taskType}
                        onChange={(e) => setTaskType(e.target.value)}
                        style={{ width: '100%', padding: '10px 14px', borderRadius: '10px', background: 'rgba(15,23,42,0.6)', border: '1px solid rgba(255,255,255,0.08)', color: 'var(--text-primary)', fontSize: '0.84rem', outline: 'none' }}
                      >
                        <option>Auto Detect</option>
                        <option>Classification</option>
                        <option>Regression</option>
                        <option>Clustering</option>
                        <option>Time Series</option>
                        <option>Anomaly Detection</option>
                      </select>
                    </div>
                    <div>
                      <label style={{ display: 'block', fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: '6px', fontWeight: 700 }}>METRIC</label>
                      <select
                        value={optimizationMetric}
                        onChange={(e) => setOptimizationMetric(e.target.value)}
                        style={{ width: '100%', padding: '10px 14px', borderRadius: '10px', background: 'rgba(15,23,42,0.6)', border: '1px solid rgba(255,255,255,0.08)', color: 'var(--text-primary)', fontSize: '0.84rem', outline: 'none' }}
                      >
                        <option value="Auto">Auto</option>
                        <option value="F1">F1-Score</option>
                        <option value="ROC-AUC">ROC-AUC</option>
                        <option value="Recall">Recall</option>
                        <option value="Precision">Precision</option>
                        <option value="RMSE">RMSE</option>
                        <option value="R²">R² Score</option>
                      </select>
                    </div>
                  </div>

                  {/* Compute Budget + CV Folds */}
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                    <div>
                      <label style={{ display: 'block', fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: '6px', fontWeight: 700 }}>COMPUTE BUDGET</label>
                      <select
                        value={computeBudget}
                        onChange={(e) => setComputeBudget(e.target.value)}
                        style={{ width: '100%', padding: '10px 14px', borderRadius: '10px', background: 'rgba(15,23,42,0.6)', border: '1px solid rgba(255,255,255,0.08)', color: 'var(--text-primary)', fontSize: '0.84rem', outline: 'none' }}
                      >
                        <option>Low (Fast ~15s)</option>
                        <option value="Balanced">Balanced (~45s)</option>
                        <option>High (Deep ~120s)</option>
                      </select>
                    </div>
                    <div>
                      <label style={{ display: 'block', fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: '6px', fontWeight: 700 }}>CV FOLDS</label>
                      <input
                        type="number"
                        min={2} max={10}
                        value={cvFolds}
                        onChange={(e) => setCvFolds(Number(e.target.value))}
                        style={{ width: '100%', padding: '10px 14px', borderRadius: '10px', background: 'rgba(15,23,42,0.6)', border: '1px solid rgba(255,255,255,0.08)', color: 'var(--text-primary)', fontSize: '0.84rem', outline: 'none', boxSizing: 'border-box' }}
                      />
                    </div>
                  </div>

                  {/* Deep Learning */}
                  <div>
                    <label style={{ display: 'block', fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: '6px', fontWeight: 700 }}>DEEP LEARNING</label>
                    <select
                      value={deepLearning}
                      onChange={(e) => setDeepLearning(e.target.value)}
                      style={{ width: '100%', padding: '10px 14px', borderRadius: '10px', background: 'rgba(15,23,42,0.6)', border: '1px solid rgba(255,255,255,0.08)', color: 'var(--text-primary)', fontSize: '0.84rem', outline: 'none' }}
                    >
                      <option>Auto</option>
                      <option>Enabled (MLP/TabNet)</option>
                      <option>Disabled</option>
                    </select>
                  </div>
                </div>
              )}
            </div>

            {/* Dataset Profiling Card */}
            {datasetMeta && (
              <div
                className="np-card np-slide-up"
                style={{
                  background: 'rgba(15,23,42,0.7)',
                  backdropFilter: 'blur(20px)',
                  border: '1px solid rgba(16,185,129,0.2)',
                  borderRadius: '20px',
                  padding: '22px 24px',
                  boxShadow: '0 4px 24px rgba(0,0,0,0.2)',
                }}
              >
                <h3 style={{ fontSize: '0.88rem', fontWeight: 800, margin: '0 0 16px 0', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Database size={15} color="#34d399" />
                  <span style={{ color: '#34d399' }}>Dataset Health & Schema</span>
                </h3>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '14px' }}>
                  {[
                    { label: 'ROWS', value: datasetMeta.row_count?.toLocaleString() || '—' },
                    { label: 'COLUMNS', value: datasetMeta.column_count || '—' },
                    { label: 'MEMORY', value: `${((datasetMeta.memory_usage_bytes || 0) / 1024).toFixed(1)} KB` },
                    { label: 'DUPLICATES', value: `${datasetMeta.duplicate_rows_count || 0}`, color: datasetMeta.has_duplicates ? '#f87171' : '#34d399' },
                  ].map((m) => (
                    <div
                      key={m.label}
                      style={{
                        padding: '12px 14px',
                        background: 'rgba(15,23,42,0.5)',
                        borderRadius: '12px',
                        border: '1px solid rgba(255,255,255,0.06)',
                      }}
                    >
                      <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', fontWeight: 700, textTransform: 'uppercase' }}>{m.label}</div>
                      <div style={{ fontSize: '1.2rem', fontWeight: 800, color: m.color || 'var(--text-primary)', marginTop: '3px' }}>{m.value}</div>
                    </div>
                  ))}
                </div>

                {datasetMeta.target_candidates?.length > 0 && (
                  <div style={{ borderTop: '1px solid rgba(255,255,255,0.06)', paddingTop: '12px' }}>
                    <div style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--text-muted)', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
                      Target Candidates Detected
                    </div>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                      {datasetMeta.target_candidates.map((tc: any) => (
                        <span
                          key={tc.column}
                          className="np-tag"
                          onClick={() => setTargetColumn(tc.column)}
                          style={{
                            fontSize: '0.72rem',
                            padding: '4px 10px',
                            borderRadius: '100px',
                            background: targetColumn === tc.column ? 'rgba(99,102,241,0.35)' : 'rgba(99,102,241,0.1)',
                            border: `1px solid ${targetColumn === tc.column ? 'rgba(99,102,241,0.6)' : 'rgba(99,102,241,0.2)'}`,
                            color: targetColumn === tc.column ? '#c7d2fe' : 'var(--primary-light)',
                            fontWeight: 700,
                          }}
                        >
                          {tc.column} ({Math.round((tc.confidence || 0.9) * 100)}%)
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* ─── PRIMARY CTA BUTTON ─── */}
            <button
              type="button"
              className="np-btn-glow"
              onClick={handleStartAnalysis}
              disabled={isStarting}
              style={{
                width: '100%',
                padding: '18px 28px',
                borderRadius: '16px',
                background: isStarting
                  ? 'linear-gradient(135deg, rgba(99,102,241,0.6), rgba(67,56,202,0.6))'
                  : 'linear-gradient(135deg, #6366f1 0%, #4338ca 50%, #7c3aed 100%)',
                color: '#fff',
                border: 'none',
                fontSize: '1.08rem',
                fontWeight: 900,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '12px',
                cursor: isStarting ? 'not-allowed' : 'pointer',
                boxShadow: '0 8px 30px rgba(99,102,241,0.45)',
                letterSpacing: '0.01em',
                position: 'relative',
                overflow: 'hidden',
              }}
            >
              {/* shimmer overlay */}
              {!isStarting && (
                <div
                  style={{
                    position: 'absolute',
                    inset: 0,
                    background: 'linear-gradient(105deg, transparent 40%, rgba(255,255,255,0.12) 50%, transparent 60%)',
                    backgroundSize: '200% 100%',
                    animationName: 'shimmer',
                    animationDuration: '2.5s',
                    animationTimingFunction: 'ease',
                    animationIterationCount: 'infinite',
                    pointerEvents: 'none',
                  }}
                />
              )}

              {isStarting ? (
                <>
                  <RefreshCw size={22} className="animate-spin" />
                  <span>Launching Multi-Agent Graph...</span>
                </>
              ) : (
                <>
                  <Play size={20} />
                  <span>Start AI Analysis</span>
                  <ArrowRight size={20} />
                </>
              )}
            </button>

            {/* Pipeline Steps Info */}
            <div
              style={{
                padding: '16px 20px',
                borderRadius: '14px',
                background: 'rgba(15,23,42,0.4)',
                border: '1px solid rgba(255,255,255,0.06)',
              }}
            >
              <div style={{ fontSize: '0.7rem', fontWeight: 800, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '12px' }}>
                17-Stage Pipeline
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '7px' }}>
                {[
                  'Data Profiling & Quality Audit',
                  'Outlier Analysis (IQR + Isolation Forest)',
                  'Preprocessing & Feature Engineering',
                  'Target Detection & Task Classification',
                  'Baseline → Candidate → HPO Model Training',
                  'Bayesian Hyperparameter Optimization',
                  'Evaluation & Generalization Check',
                  'Notebook + HTML/PDF Report Generation',
                ].map((step, i) => (
                  <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                    <div
                      style={{
                        width: '5px',
                        height: '5px',
                        borderRadius: '50%',
                        background: `hsl(${220 + i * 20}, 80%, 65%)`,
                        flexShrink: 0,
                      }}
                    />
                    <span>{step}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* ── DATASET PREVIEW TABLE ── */}
        {previewData && (
          <div
            className="np-card np-slide-up"
            style={{
              background: 'rgba(15,23,42,0.7)',
              backdropFilter: 'blur(20px)',
              border: '1px solid rgba(99,102,241,0.15)',
              borderRadius: '20px',
              padding: '24px 28px',
              boxShadow: '0 4px 24px rgba(0,0,0,0.2)',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '14px', marginBottom: '18px' }}>
              <div>
                <h3 style={{ fontSize: '1.05rem', fontWeight: 800, margin: '0 0 4px 0' }}>
                  📊 Interactive Dataset Preview
                </h3>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', margin: 0 }}>
                  Showing first {previewData.rows.length} rows of {previewData.total_rows?.toLocaleString() || '—'} total observations
                </p>
              </div>

              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  background: 'rgba(15,23,42,0.5)',
                  padding: '8px 14px',
                  borderRadius: '10px',
                  border: '1px solid rgba(255,255,255,0.08)',
                }}
              >
                <Search size={14} color="var(--text-muted)" />
                <input
                  type="text"
                  placeholder="Filter rows..."
                  value={previewSearch}
                  onChange={(e) => setPreviewSearch(e.target.value)}
                  style={{
                    background: 'transparent',
                    border: 'none',
                    color: 'var(--text-primary)',
                    fontSize: '0.82rem',
                    outline: 'none',
                    width: '140px',
                  }}
                />
              </div>
            </div>

            <div style={{ overflowX: 'auto', borderRadius: '14px', border: '1px solid rgba(255,255,255,0.06)' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.82rem' }}>
                <thead>
                  <tr style={{ background: 'rgba(15,23,42,0.8)', borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
                    <th style={{ padding: '11px 16px', textAlign: 'left', color: 'var(--text-muted)', fontWeight: 600, width: '40px' }}>#</th>
                    {previewData.columns.map((col) => (
                      <th
                        key={col}
                        style={{
                          padding: '11px 16px',
                          textAlign: 'left',
                          fontWeight: 700,
                          color: targetColumn === col ? '#818cf8' : 'var(--text-secondary)',
                          whiteSpace: 'nowrap',
                        }}
                      >
                        {col}
                        {targetColumn === col && (
                          <span style={{ marginLeft: '6px', fontSize: '0.64rem', padding: '2px 6px', borderRadius: '4px', background: 'rgba(99,102,241,0.25)', color: '#c7d2fe' }}>
                            Target
                          </span>
                        )}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {filteredRows?.slice(0, 30).map((row: any, rIdx: number) => (
                    <tr
                      key={rIdx}
                      style={{
                        borderBottom: '1px solid rgba(255,255,255,0.04)',
                        background: rIdx % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.012)',
                        transition: 'background 0.1s',
                      }}
                    >
                      <td style={{ padding: '9px 16px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', fontSize: '0.75rem' }}>{rIdx + 1}</td>
                      {previewData.columns.map((col) => (
                        <td key={col} style={{ padding: '9px 16px', maxWidth: '180px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {row[col] === null || row[col] === undefined
                            ? <em style={{ opacity: 0.4, fontSize: '0.75rem' }}>null</em>
                            : String(row[col])}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* ── AI PROJECT PLANNER PROPOSAL MODAL (HUMAN-IN-THE-LOOP) ── */}
        {isProposalModalOpen && aiProposal && (
          <div
            style={{
              position: 'fixed',
              inset: 0,
              zIndex: 9999,
              backgroundColor: 'rgba(5, 7, 15, 0.82)',
              backdropFilter: 'blur(10px)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '24px',
            }}
          >
            <div
              className="np-card np-slide-up"
              style={{
                width: '100%',
                maxWidth: '740px',
                maxHeight: '90vh',
                overflowY: 'auto',
                background: 'linear-gradient(135deg, rgba(23, 27, 44, 0.98) 0%, rgba(15, 18, 30, 0.98) 100%)',
                border: '1px solid rgba(99, 102, 241, 0.35)',
                borderRadius: '20px',
                boxShadow: '0 25px 60px rgba(0, 0, 0, 0.6), 0 0 40px rgba(99, 102, 241, 0.15)',
                padding: '32px',
                position: 'relative',
              }}
            >
              {/* Header */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '20px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <div
                    style={{
                      width: '44px',
                      height: '44px',
                      borderRadius: '12px',
                      background: 'linear-gradient(135deg, #6366f1 0%, #a855f7 100%)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      boxShadow: '0 8px 20px rgba(99,102,241,0.4)',
                    }}
                  >
                    <Sparkles size={22} color="#fff" />
                  </div>
                  <div>
                    <h2 style={{ fontSize: '1.35rem', fontWeight: 800, margin: 0, color: '#f8fafc' }}>
                      AI Project Proposal
                    </h2>
                    <p style={{ margin: 0, fontSize: '0.85rem', color: '#94a3b8' }}>
                      Human Approval Required &bull; Review AI-recommended strategy before autonomous execution
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => setIsProposalModalOpen(false)}
                  style={{
                    background: 'rgba(255,255,255,0.06)',
                    border: 'none',
                    borderRadius: '8px',
                    width: '32px',
                    height: '32px',
                    color: '#94a3b8',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <X size={18} />
                </button>
              </div>

              {/* Proposal Content */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
                {/* Project Name Field */}
                <div style={{ background: 'rgba(99,102,241,0.06)', border: '1px solid rgba(99,102,241,0.18)', borderRadius: '12px', padding: '16px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                    <label style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.08em', color: '#818cf8', fontWeight: 700 }}>
                      Proposed Project Name
                    </label>
                    <span style={{ fontSize: '0.72rem', color: '#94a3b8' }}>Editable by user</span>
                  </div>
                  {isEditingProposal ? (
                    <input
                      type="text"
                      value={aiProposal.project_name || ''}
                      onChange={(e) => setAiProposal({ ...aiProposal, project_name: e.target.value })}
                      style={{
                        width: '100%',
                        padding: '10px 14px',
                        background: 'rgba(15, 23, 42, 0.8)',
                        border: '1px solid #6366f1',
                        borderRadius: '8px',
                        color: '#f8fafc',
                        fontSize: '1rem',
                        fontWeight: 600,
                      }}
                    />
                  ) : (
                    <div style={{ fontSize: '1.15rem', fontWeight: 700, color: '#f8fafc' }}>
                      {aiProposal.project_name || 'Autonomous ML Project'}
                    </div>
                  )}
                </div>

                {/* Objective & Business Problem */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
                  <div style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: '12px', padding: '14px' }}>
                    <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: '#94a3b8', fontWeight: 700, marginBottom: '6px' }}>
                      Objective
                    </div>
                    {isEditingProposal ? (
                      <textarea
                        rows={3}
                        value={aiProposal.objective || ''}
                        onChange={(e) => setAiProposal({ ...aiProposal, objective: e.target.value })}
                        style={{ width: '100%', padding: '8px', background: 'rgba(15,23,42,0.8)', border: '1px solid #6366f1', borderRadius: '6px', color: '#fff', fontSize: '0.82rem' }}
                      />
                    ) : (
                      <p style={{ margin: 0, fontSize: '0.85rem', color: '#cbd5e1', lineHeight: 1.45 }}>
                        {aiProposal.objective || 'Predict key outcomes with maximum accuracy and explainability.'}
                      </p>
                    )}
                  </div>
                  <div style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: '12px', padding: '14px' }}>
                    <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: '#94a3b8', fontWeight: 700, marginBottom: '6px' }}>
                      Business Problem
                    </div>
                    {isEditingProposal ? (
                      <textarea
                        rows={3}
                        value={aiProposal.business_problem || ''}
                        onChange={(e) => setAiProposal({ ...aiProposal, business_problem: e.target.value })}
                        style={{ width: '100%', padding: '8px', background: 'rgba(15,23,42,0.8)', border: '1px solid #6366f1', borderRadius: '6px', color: '#fff', fontSize: '0.82rem' }}
                      />
                    ) : (
                      <p style={{ margin: 0, fontSize: '0.85rem', color: '#cbd5e1', lineHeight: 1.45 }}>
                        {aiProposal.business_problem || 'Optimize downstream business decision making.'}
                      </p>
                    )}
                  </div>
                </div>

                {/* Technical Specs: Target, Task, Metrics */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px' }}>
                  <div style={{ background: 'rgba(99,102,241,0.08)', borderRadius: '10px', padding: '12px', border: '1px solid rgba(99,102,241,0.2)' }}>
                    <div style={{ fontSize: '0.7rem', color: '#818cf8', fontWeight: 700, textTransform: 'uppercase' }}>Target Column</div>
                    <div style={{ fontSize: '1rem', fontWeight: 700, color: '#f8fafc', marginTop: '4px' }}>
                      {aiProposal.target_candidate || 'Auto'}
                    </div>
                  </div>
                  <div style={{ background: 'rgba(16,185,129,0.08)', borderRadius: '10px', padding: '12px', border: '1px solid rgba(16,185,129,0.2)' }}>
                    <div style={{ fontSize: '0.7rem', color: '#34d399', fontWeight: 700, textTransform: 'uppercase' }}>ML Task</div>
                    <div style={{ fontSize: '1rem', fontWeight: 700, color: '#f8fafc', marginTop: '4px', textTransform: 'capitalize' }}>
                      {aiProposal.task_type || 'Classification'}
                    </div>
                  </div>
                  <div style={{ background: 'rgba(245,158,11,0.08)', borderRadius: '10px', padding: '12px', border: '1px solid rgba(245,158,11,0.2)' }}>
                    <div style={{ fontSize: '0.7rem', color: '#fbbf24', fontWeight: 700, textTransform: 'uppercase' }}>Primary Metric</div>
                    <div style={{ fontSize: '1rem', fontWeight: 700, color: '#f8fafc', marginTop: '4px' }}>
                      {aiProposal.primary_metric || 'F1 / ROC-AUC'}
                    </div>
                  </div>
                </div>

                {/* Pipeline Strategy */}
                {aiProposal.recommended_pipeline && aiProposal.recommended_pipeline.length > 0 && (
                  <div style={{ background: 'rgba(255,255,255,0.02)', borderRadius: '12px', padding: '14px', border: '1px solid rgba(255,255,255,0.06)' }}>
                    <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: '#94a3b8', fontWeight: 700, marginBottom: '8px' }}>
                      Recommended Execution Pipeline
                    </div>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                      {aiProposal.recommended_pipeline.map((step: string, idx: number) => (
                        <span
                          key={idx}
                          style={{
                            padding: '4px 10px',
                            borderRadius: '6px',
                            background: 'rgba(99,102,241,0.15)',
                            color: '#c7d2fe',
                            fontSize: '0.75rem',
                            fontWeight: 600,
                            border: '1px solid rgba(99,102,241,0.3)',
                          }}
                        >
                          {idx + 1}. {step}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Deployment Context */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.8rem', color: '#94a3b8' }}>
                  <Cpu size={15} color="#818cf8" />
                  <span>Deployment Context: <strong style={{ color: '#e2e8f0' }}>{aiProposal.deployment_context || 'REST API microservice / Docker container'}</strong></span>
                </div>
              </div>

              {/* Action Buttons */}
              <div
                style={{
                  marginTop: '28px',
                  paddingTop: '20px',
                  borderTop: '1px solid rgba(255,255,255,0.08)',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}
              >
                <div style={{ display: 'flex', gap: '10px' }}>
                  <button
                    onClick={() => setIsEditingProposal(!isEditingProposal)}
                    style={{
                      padding: '10px 18px',
                      borderRadius: '10px',
                      background: isEditingProposal ? 'rgba(99,102,241,0.3)' : 'rgba(255,255,255,0.05)',
                      border: '1px solid rgba(255,255,255,0.1)',
                      color: '#f8fafc',
                      fontSize: '0.85rem',
                      fontWeight: 600,
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                    }}
                  >
                    <Sliders size={15} />
                    {isEditingProposal ? 'Done Editing' : 'Edit Plan'}
                  </button>
                  <button
                    onClick={handleRegenerateProposal}
                    disabled={isPlanning}
                    style={{
                      padding: '10px 18px',
                      borderRadius: '10px',
                      background: 'rgba(255,255,255,0.05)',
                      border: '1px solid rgba(255,255,255,0.1)',
                      color: '#f8fafc',
                      fontSize: '0.85rem',
                      fontWeight: 600,
                      cursor: isPlanning ? 'not-allowed' : 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                    }}
                  >
                    <RefreshCw size={15} className={isPlanning ? 'np-spin-slow' : ''} />
                    {isPlanning ? 'Regenerating...' : 'Regenerate'}
                  </button>
                </div>

                <div style={{ display: 'flex', gap: '10px' }}>
                  <button
                    onClick={() => setIsProposalModalOpen(false)}
                    style={{
                      padding: '10px 18px',
                      borderRadius: '10px',
                      background: 'transparent',
                      border: '1px solid rgba(255,255,255,0.1)',
                      color: '#94a3b8',
                      fontSize: '0.85rem',
                      fontWeight: 600,
                      cursor: 'pointer',
                    }}
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleApproveProposal}
                    className="np-btn-glow"
                    style={{
                      padding: '11px 24px',
                      borderRadius: '10px',
                      background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                      border: 'none',
                      color: '#ffffff',
                      fontSize: '0.9rem',
                      fontWeight: 700,
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      boxShadow: '0 8px 25px rgba(16, 185, 129, 0.4)',
                    }}
                  >
                    <CheckCircle2 size={17} />
                    Approve & Continue
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ── DUPLICATE DATASET WARNING MODAL ── */}
        {duplicateWarning && (
          <div
            style={{
              position: 'fixed',
              inset: 0,
              zIndex: 9999,
              backgroundColor: 'rgba(5, 7, 15, 0.85)',
              backdropFilter: 'blur(10px)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '24px',
            }}
          >
            <div
              className="np-card np-slide-up"
              style={{
                width: '100%',
                maxWidth: '560px',
                background: 'linear-gradient(135deg, rgba(30, 24, 18, 0.98) 0%, rgba(20, 16, 14, 0.98) 100%)',
                border: '1px solid rgba(245, 158, 11, 0.4)',
                borderRadius: '20px',
                padding: '30px',
                boxShadow: '0 25px 60px rgba(0, 0, 0, 0.7), 0 0 35px rgba(245, 158, 11, 0.2)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '14px', marginBottom: '16px' }}>
                <div
                  style={{
                    width: '46px',
                    height: '46px',
                    borderRadius: '12px',
                    background: 'rgba(245, 158, 11, 0.2)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: '#fbbf24',
                  }}
                >
                  <AlertCircle size={26} />
                </div>
                <div>
                  <h3 style={{ margin: 0, fontSize: '1.2rem', fontWeight: 800, color: '#fef3c7' }}>
                    Duplicate Dataset Detected
                  </h3>
                  <p style={{ margin: 0, fontSize: '0.8rem', color: '#d97706' }}>
                    SHA-256 match found in project storage
                  </p>
                </div>
              </div>

              <p style={{ fontSize: '0.88rem', color: '#cbd5e1', lineHeight: 1.5, marginBottom: '22px' }}>
                This dataset already exists in this project (SHA-256:{' '}
                <code style={{ fontSize: '0.75rem', background: 'rgba(0,0,0,0.4)', padding: '2px 6px', borderRadius: '4px', color: '#fbbf24' }}>
                  {duplicateWarning.file_hash ? duplicateWarning.file_hash.substring(0, 16) + '...' : 'matched'}
                </code>
                ). What would you like to do?
              </p>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                <button
                  onClick={() => {
                    setDuplicateWarning(null)
                    if (createdProjectId) navigate(`/projects/${createdProjectId}`)
                  }}
                  style={{
                    padding: '12px 18px',
                    borderRadius: '10px',
                    background: 'rgba(99, 102, 241, 0.2)',
                    border: '1px solid rgba(99, 102, 241, 0.4)',
                    color: '#c7d2fe',
                    fontWeight: 700,
                    fontSize: '0.88rem',
                    cursor: 'pointer',
                    textAlign: 'left',
                  }}
                >
                  &rarr; Use Existing Dataset &amp; Analysis
                </button>
                <button
                  onClick={handleForceUploadDuplicate}
                  style={{
                    padding: '12px 18px',
                    borderRadius: '10px',
                    background: 'rgba(245, 158, 11, 0.2)',
                    border: '1px solid rgba(245, 158, 11, 0.4)',
                    color: '#fef3c7',
                    fontWeight: 700,
                    fontSize: '0.88rem',
                    cursor: 'pointer',
                    textAlign: 'left',
                  }}
                >
                  &rarr; Create New Dataset Version (Force Re-upload)
                </button>
                <button
                  onClick={() => {
                    setDuplicateWarning(null)
                    setFile(null)
                  }}
                  style={{
                    padding: '10px 18px',
                    borderRadius: '10px',
                    background: 'transparent',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    color: '#94a3b8',
                    fontSize: '0.85rem',
                    fontWeight: 600,
                    cursor: 'pointer',
                  }}
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
