import React, { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { FolderGit2, Plus, ArrowRight, Database, Box, Calendar, Tag, Shield, Search, Copy, RefreshCw, Upload } from 'lucide-react'

import { authStore } from '../../services/authStore'
import { projectsApi } from '../../services/api'
import { Project } from '../../types'

export function ProjectsList() {
  const navigate = useNavigate()
  const [projects, setProjects] = useState<any[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [newProjectName, setNewProjectName] = useState('')
  const [newProjectDesc, setNewProjectDesc] = useState('')
  const [newProjectTag, setNewProjectTag] = useState('Classification')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const loadProjects = async () => {
    setIsLoading(true)
    try {
      const list = await projectsApi.list()
      setProjects(list || [])
    } catch (err) {
      console.error('Failed to load projects:', err)
      setProjects([])
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadProjects()
  }, [])

  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newProjectName.trim()) return
    setIsSubmitting(true)

    try {
      const created = await projectsApi.create({
        name: newProjectName.trim(),
        description: newProjectDesc.trim() || `Data science workspace for ${newProjectName.trim()}`,
        objective: newProjectDesc.trim() || undefined,
        configuration: {
          task_type: newProjectTag,
        },
      })
      authStore.setCurrentProject(created)
      setIsModalOpen(false)
      setNewProjectName('')
      setNewProjectDesc('')
      navigate(`/projects/${created.id}`)
    } catch (err) {
      console.error('Failed to create project:', err)
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleCloneProject = async (e: React.MouseEvent, projId: string) => {
    e.stopPropagation()
    try {
      const cloned = await projectsApi.clone(projId)
      await loadProjects()
      authStore.setCurrentProject(cloned)
    } catch (err) {
      console.error('Failed to clone project:', err)
    }
  }

  const handleSelect = (proj: any) => {
    authStore.setCurrentProject(proj)
    navigate(`/projects/${proj.id}`)
  }

  const filteredProjects = projects.filter((p) => {
    if (!searchQuery) return true
    const q = searchQuery.toLowerCase()
    return (
      p.name?.toLowerCase().includes(q) ||
      p.description?.toLowerCase().includes(q) ||
      p.objective?.toLowerCase().includes(q) ||
      p.configuration?.dataset_name?.toLowerCase().includes(q)
    )
  })

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h1 style={{ fontSize: '1.6rem', fontWeight: 800, margin: 0 }}>Projects Workspace</h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', margin: '4px 0 0 0' }}>
            Multi-tenant isolated data science environments. Every project strictly encapsulates datasets, models, and artifacts.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <div style={{ position: 'relative', minWidth: '240px' }}>
            <Search size={15} style={{ position: 'absolute', left: '12px', top: '10px', color: 'var(--text-muted)' }} />
            <input
              type="text"
              placeholder="Search projects..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                width: '100%',
                padding: '8px 12px 8px 34px',
                borderRadius: '8px',
                background: 'rgba(15, 23, 42, 0.6)',
                border: '1px solid var(--border-subtle)',
                color: '#f8fafc',
                fontSize: '0.85rem',
              }}
            />
          </div>
          <button
            onClick={() => setIsModalOpen(true)}
            className="btn btn-primary"
            style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
          >
            <Plus size={16} /> New Project
          </button>
        </div>
      </div>

      {/* Projects Grid or Empty State */}
      {isLoading ? (
        <div style={{ padding: '60px', textAlign: 'center', color: 'var(--text-muted)' }}>
          <RefreshCw size={24} className="spin" style={{ marginBottom: '12px' }} />
          <div>Loading projects...</div>
        </div>
      ) : filteredProjects.length === 0 ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {/* Hero Empty State */}
          <div
            style={{
              background: 'linear-gradient(135deg, rgba(99,102,241,0.08) 0%, rgba(168,85,247,0.06) 100%)',
              border: '1px dashed rgba(99,102,241,0.3)',
              borderRadius: 'var(--radius-xl)',
              padding: '48px 24px',
              textAlign: 'center',
            }}
          >
            <div
              style={{
                width: '72px', height: '72px', borderRadius: '20px',
                background: 'linear-gradient(135deg, rgba(99,102,241,0.2) 0%, rgba(168,85,247,0.15) 100%)',
                color: '#818cf8',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                margin: '0 auto 20px',
                boxShadow: '0 8px 24px rgba(99,102,241,0.2)',
              }}
            >
              <FolderGit2 size={34} />
            </div>
            <h3 style={{ fontSize: '1.4rem', fontWeight: 800, margin: '0 0 10px 0', letterSpacing: '-0.02em' }}>
              {searchQuery ? 'No matching projects found' : 'Launch Your First AI Workspace'}
            </h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', maxWidth: '480px', margin: '0 auto 28px', lineHeight: 1.6 }}>
              {searchQuery
                ? `No projects matched "${searchQuery}". Try a different keyword.`
                : 'Create an isolated project container with automatic EDA, AutoML, and model governance — powered by 47+ specialized agents.'}
            </p>
            <div style={{ display: 'flex', gap: '12px', justifyContent: 'center', flexWrap: 'wrap' }}>
              <Link to="/projects/new" className="btn btn-primary" style={{ textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '12px 24px', fontSize: '0.9rem' }}>
                <Plus size={16} /> Create New Project
              </Link>
              <button onClick={() => setIsModalOpen(true)} className="btn btn-secondary" style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '12px 20px', fontSize: '0.9rem' }}>
                <Upload size={16} /> Quick Start with Dataset
              </button>
            </div>
          </div>

          {/* Sample Project Templates */}
          {!searchQuery && (
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <h3 style={{ fontSize: '1rem', fontWeight: 700, margin: 0, color: 'var(--text-secondary)' }}>
                  🚀 Start from a Template
                </h3>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Click to create from template</span>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: '20px' }}>
                {[
                  {
                    name: 'Customer Churn Prediction',
                    tag: 'CLASSIFICATION',
                    desc: 'Binary classification with ensemble ML — LightGBM, XGBoost, PyTorch neural networks, and TreeSHAP explainability.',
                    metric: 'F1: 0.925 · ROC-AUC: 0.962',
                    latency: '4.2ms',
                    stage: 'Production',
                    gradient: 'linear-gradient(135deg, rgba(99,102,241,0.12) 0%, rgba(168,85,247,0.08) 100%)',
                    borderColor: 'rgba(99,102,241,0.25)',
                    iconColor: '#818cf8',
                    agents: 7,
                  },
                  {
                    name: 'Credit Card Fraud Detector',
                    tag: 'ANOMALY DETECTION',
                    desc: 'Isolation Forest + PyTorch autoencoder with real-time streaming inference. PSI drift monitoring included.',
                    metric: 'PR-AUC: 0.981 · Recall: 0.94',
                    latency: '2.8ms',
                    stage: 'Production',
                    gradient: 'linear-gradient(135deg, rgba(16,185,129,0.1) 0%, rgba(6,182,212,0.07) 100%)',
                    borderColor: 'rgba(16,185,129,0.22)',
                    iconColor: '#34d399',
                    agents: 9,
                  },
                  {
                    name: 'LTV Revenue Regressor',
                    tag: 'REGRESSION',
                    desc: 'CatBoost LTV model with Optuna Bayesian HPO, temporal train/test isolation, and group k-fold validation.',
                    metric: 'RMSE: 142.5 · R²: 0.884',
                    latency: '5.1ms',
                    stage: 'Staging',
                    gradient: 'linear-gradient(135deg, rgba(245,158,11,0.1) 0%, rgba(251,146,60,0.07) 100%)',
                    borderColor: 'rgba(245,158,11,0.22)',
                    iconColor: '#fbbf24',
                    agents: 6,
                  },
                ].map((template) => (
                  <div
                    key={template.name}
                    onClick={() => setIsModalOpen(true)}
                    className="project-card"
                    style={{
                      background: template.gradient,
                      borderColor: template.borderColor,
                    }}
                  >
                    <div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '14px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                          <div
                            style={{
                              width: '40px', height: '40px', borderRadius: '10px',
                              background: 'rgba(255,255,255,0.06)',
                              color: template.iconColor,
                              display: 'flex', alignItems: 'center', justifyContent: 'center',
                              border: `1px solid ${template.borderColor}`,
                            }}
                          >
                            <FolderGit2 size={20} />
                          </div>
                          <div>
                            <h3 style={{ fontSize: '1rem', fontWeight: 700, margin: 0 }}>{template.name}</h3>
                            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                              {template.agents} specialized agents
                            </div>
                          </div>
                        </div>
                        <span
                          style={{
                            fontSize: '0.62rem', padding: '3px 8px',
                            borderRadius: 'var(--radius-full)',
                            background: template.stage === 'Production' ? 'rgba(16,185,129,0.15)' : 'rgba(245,158,11,0.15)',
                            color: template.stage === 'Production' ? 'var(--success)' : 'var(--warning)',
                            border: `1px solid ${template.stage === 'Production' ? 'rgba(16,185,129,0.3)' : 'rgba(245,158,11,0.3)'}`,
                            fontWeight: 700, textTransform: 'uppercase' as const,
                          }}
                        >
                          {template.stage}
                        </span>
                      </div>

                      <p style={{ fontSize: '0.83rem', color: 'var(--text-secondary)', lineHeight: 1.55, marginBottom: '14px' }}>
                        {template.desc}
                      </p>

                      <div style={{ display: 'flex', gap: '8px', marginBottom: '12px', flexWrap: 'wrap' as const }}>
                        <span style={{
                          fontSize: '0.68rem', padding: '2px 8px', borderRadius: 'var(--radius-full)',
                          background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)',
                          color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)',
                        }}>
                          {template.metric}
                        </span>
                        <span style={{
                          fontSize: '0.68rem', padding: '2px 8px', borderRadius: 'var(--radius-full)',
                          background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)',
                          color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)',
                        }}>
                          p99 {template.latency}
                        </span>
                        <span style={{
                          fontSize: '0.68rem', padding: '2px 8px', borderRadius: 'var(--radius-full)',
                          background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)',
                          color: 'var(--text-secondary)',
                        }}>
                          {template.tag}
                        </span>
                      </div>
                    </div>

                    <div style={{ borderTop: '1px solid rgba(255,255,255,0.08)', paddingTop: '14px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontSize: '0.75rem', color: template.iconColor, fontWeight: 600 }}>
                          Use this template →
                        </span>
                        <div style={{ display: 'flex', gap: '6px' }}>
                          <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Template</span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: '20px' }}>
          {filteredProjects.map((proj) => (
            <div
              key={proj.id}
              onClick={() => handleSelect(proj)}
              className="project-card"
            >
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <div
                      style={{
                        width: '40px', height: '40px', borderRadius: '10px',
                        background: 'rgba(99, 102, 241, 0.12)',
                        color: 'var(--primary-light)',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        border: '1px solid rgba(99,102,241,0.2)',
                      }}
                    >
                      <FolderGit2 size={20} />
                    </div>
                    <div>
                      <h3 style={{ fontSize: '1.05rem', fontWeight: 700, margin: 0, maxWidth: '180px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {proj.name}
                      </h3>
                      <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                        Slug: {proj.slug || proj.id}
                      </div>
                    </div>
                  </div>

                  <span
                    style={{
                      fontSize: '0.65rem', padding: '3px 8px',
                      borderRadius: 'var(--radius-full)',
                      background: proj.status === 'completed' ? 'rgba(16,185,129,0.12)' : 'rgba(99,102,241,0.12)',
                      color: proj.status === 'completed' ? 'var(--success)' : 'var(--primary-light)',
                      border: '1px solid rgba(99,102,241,0.25)',
                      fontWeight: 700, textTransform: 'uppercase' as const,
                    }}
                  >
                    {proj.status || 'Active'}
                  </span>
                </div>

                <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.5, marginBottom: '14px', minHeight: '38px', overflow: 'hidden', textOverflow: 'ellipsis', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical' as const }}>
                  {proj.description || proj.objective || 'Autonomous machine learning project workspace.'}
                </p>

                {/* Configuration Specs */}
                {proj.configuration?.dataset_name && (
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '12px', background: 'rgba(255,255,255,0.03)', padding: '6px 10px', borderRadius: '6px', border: '1px solid var(--border-subtle)' }}>
                    Dataset: <strong style={{ color: '#cbd5e1' }}>{proj.configuration.dataset_name}</strong>
                  </div>
                )}
              </div>

              {/* Footer */}
              <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '14px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <button
                    onClick={(e) => handleCloneProject(e, proj.id)}
                    title="Clone Project Configuration"
                    style={{
                      background: 'transparent', border: '1px solid var(--border-subtle)',
                      borderRadius: '6px', padding: '6px 10px',
                      color: 'var(--text-muted)', fontSize: '0.75rem',
                      cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px',
                    }}
                  >
                    <Copy size={12} /> Clone
                  </button>

                  <button
                    onClick={() => handleSelect(proj)}
                    className="btn btn-primary"
                    style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.8rem', padding: '6px 14px' }}
                  >
                    <span>Open Workspace</span>
                    <ArrowRight size={13} />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}


      {/* Create Project Modal */}
      {isModalOpen && (
        <div className="cmd-palette-backdrop" onClick={() => setIsModalOpen(false)}>
          <div className="cmd-palette-modal" style={{ padding: '24px' }} onClick={(e) => e.stopPropagation()}>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: '8px' }}>Create New Project</h2>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '20px' }}>
              Create an isolated project container for datasets, pipeline graphs, and model registry artifacts.
            </p>

            <form onSubmit={handleCreateProject} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '6px' }}>
                  Project Name *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Credit Card Fraud Detector"
                  value={newProjectName}
                  onChange={(e) => setNewProjectName(e.target.value)}
                  className="form-input"
                />
              </div>

              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '6px' }}>
                  Description / Objective
                </label>
                <textarea
                  rows={3}
                  placeholder="Business objective, target KPI, and dataset domain..."
                  value={newProjectDesc}
                  onChange={(e) => setNewProjectDesc(e.target.value)}
                  className="form-textarea"
                />
              </div>

              <div>
                <label style={{ fontSize: '0.8rem', fontWeight: 600, display: 'block', marginBottom: '6px' }}>
                  Primary Objective
                </label>
                <select
                  value={newProjectTag}
                  onChange={(e) => setNewProjectTag(e.target.value)}
                  className="form-select"
                >
                  <option value="Classification">Supervised Classification</option>
                  <option value="Regression">Supervised Regression</option>
                  <option value="Deep Learning">PyTorch Deep Learning / Neural Network</option>
                  <option value="Time Series">Time Series Forecasting</option>
                  <option value="Anomaly Detection">Fraud / Anomaly Detection</option>
                </select>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginTop: '12px' }}>
                <button type="button" onClick={() => setIsModalOpen(false)} className="btn btn-secondary">
                  Cancel
                </button>
                <button type="submit" disabled={isSubmitting} className="btn btn-primary">
                  {isSubmitting ? 'Creating...' : 'Create Workspace'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default ProjectsList
