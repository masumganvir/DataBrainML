import React, { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import {
  FolderGit2,
  Database,
  FlaskConical,
  GitFork,
  Box,
  Rocket,
  Activity,
  FileText,
  BookOpen,
  Bot,
  Settings,
  Tag,
  Shield,
  ArrowRight,
  Layers,
} from 'lucide-react'
import { authStore, DEMO_PROJECTS } from '../../services/authStore'
import { Project } from '../../types'

export function ProjectDetail() {
  const { projectId } = useParams<{ projectId: string }>()
  const [activeTab, setActiveTab] = useState<'overview' | 'datasets' | 'experiments' | 'models' | 'deployments' | 'monitoring' | 'reports'>('overview')
  const [project, setProject] = useState<Project | null>(null)

  useEffect(() => {
    const found = DEMO_PROJECTS.find((p) => p.id === projectId) || authStore.getState().currentProject || DEMO_PROJECTS[0]
    setProject(found)
    authStore.setCurrentProject(found)
  }, [projectId])

  if (!project) return null

  const tabs = [
    { id: 'overview', label: 'Overview', icon: FolderGit2 },
    { id: 'datasets', label: 'Datasets', icon: Database, to: '/app/datasets' },
    { id: 'experiments', label: 'Experiments', icon: FlaskConical, to: '/app/experiments' },
    { id: 'pipeline', label: 'Pipeline Graph', icon: GitFork, to: '/app/pipelines' },
    { id: 'models', label: 'Models', icon: Box, to: '/app/models' },
    { id: 'deployments', label: 'Deployments', icon: Rocket, to: '/app/deployments' },
    { id: 'monitoring', label: 'Monitoring', icon: Activity, to: '/app/monitoring' },
    { id: 'reports', label: 'Reports', icon: FileText, to: '/app/reports' },
    { id: 'notebooks', label: 'Notebooks', icon: BookOpen, to: '/app/notebooks' },
    { id: 'assistant', label: 'AI Assistant', icon: Bot, to: '/app/assistant' },
  ]

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Project Header */}
      <div
        style={{
          background: 'var(--bg-card)',
          border: '1px solid var(--border-subtle)',
          borderRadius: 'var(--radius-xl)',
          padding: '24px 28px',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div
                style={{
                  width: '40px',
                  height: '40px',
                  borderRadius: '10px',
                  background: 'rgba(99, 102, 241, 0.12)',
                  color: 'var(--primary-light)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <FolderGit2 size={22} />
              </div>
              <div>
                <h1 style={{ fontSize: '1.5rem', fontWeight: 800, margin: 0 }}>{project.name}</h1>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                  Project ID: <span style={{ fontFamily: 'var(--font-mono)' }}>{project.id}</span> • Tenant Isolated
                </div>
              </div>
            </div>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginTop: '12px', maxWidth: '720px' }}>
              {project.description}
            </p>
          </div>

          <div style={{ display: 'flex', gap: '8px' }}>
            <span
              style={{
                fontSize: '0.75rem',
                padding: '4px 12px',
                borderRadius: 'var(--radius-full)',
                background: project.active_deployment ? 'rgba(16, 185, 129, 0.12)' : 'rgba(148, 163, 184, 0.12)',
                color: project.active_deployment ? 'var(--success)' : 'var(--text-muted)',
                border: `1px solid ${project.active_deployment ? 'rgba(16, 185, 129, 0.3)' : 'var(--border-subtle)'}`,
                fontWeight: 600,
              }}
            >
              {project.active_deployment ? 'PRODUCTION ACTIVE' : 'STAGE: TRAINING'}
            </span>
          </div>
        </div>

        {/* Horizontal Navigation Tabs */}
        <div
          style={{
            display: 'flex',
            gap: '8px',
            marginTop: '24px',
            borderTop: '1px solid var(--border-subtle)',
            paddingTop: '16px',
            overflowX: 'auto',
          }}
        >
          {tabs.map((tab) => {
            const Icon = tab.icon
            const isTabActive = activeTab === tab.id
            if (tab.to) {
              return (
                <Link
                  key={tab.id}
                  to={tab.to}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    padding: '8px 14px',
                    borderRadius: 'var(--radius-md)',
                    textDecoration: 'none',
                    fontSize: '0.85rem',
                    fontWeight: 500,
                    color: 'var(--text-secondary)',
                    background: 'transparent',
                    whiteSpace: 'nowrap',
                  }}
                >
                  <Icon size={16} />
                  <span>{tab.label}</span>
                </Link>
              )
            }
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '8px 14px',
                  borderRadius: 'var(--radius-md)',
                  border: 'none',
                  fontSize: '0.85rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  background: isTabActive ? 'var(--primary)' : 'transparent',
                  color: isTabActive ? '#ffffff' : 'var(--text-secondary)',
                  whiteSpace: 'nowrap',
                }}
              >
                <Icon size={16} />
                <span>{tab.label}</span>
              </button>
            )
          })}
        </div>
      </div>

      {/* Tab Content: Overview */}
      {activeTab === 'overview' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px' }}>
          <div
            style={{
              background: 'var(--bg-card)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-xl)',
              padding: '24px',
            }}
          >
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '16px' }}>Current Champion Model</h3>
            <div style={{ padding: '16px', borderRadius: 'var(--radius-md)', background: 'rgba(15, 23, 42, 0.4)', border: '1px solid var(--border-subtle)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontWeight: 700, fontSize: '1rem', color: 'var(--primary-light)' }}>
                  {project.current_champion_model || 'No model promoted yet'}
                </span>
                <span className="badge badge-success">CHAMPION</span>
              </div>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '8px' }}>
                Passed 8-point production readiness audit, leak-free stratified cross-validation, and KS covariate shift test.
              </p>
              <div style={{ display: 'flex', gap: '12px', marginTop: '14px' }}>
                <Link to="/app/models" className="btn btn-secondary" style={{ fontSize: '0.8rem', padding: '6px 12px' }}>
                  Inspect Model Card
                </Link>
                <Link to="/app/deployments" className="btn btn-primary" style={{ fontSize: '0.8rem', padding: '6px 12px' }}>
                  Deploy API
                </Link>
              </div>
            </div>
          </div>

          <div
            style={{
              background: 'var(--bg-card)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-xl)',
              padding: '24px',
            }}
          >
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '16px' }}>Project Artifacts Summary</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Ingested Datasets:</span>
                <span style={{ fontWeight: 600 }}>{project.dataset_count} Versions</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Trained Candidates:</span>
                <span style={{ fontWeight: 600 }}>{project.model_count} Models</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Evaluated Experiments:</span>
                <span style={{ fontWeight: 600 }}>{project.experiment_count} Runs</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Data Leakage Risk:</span>
                <span style={{ color: 'var(--success)', fontWeight: 600 }}>0 Critical Warnings</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default ProjectDetail
