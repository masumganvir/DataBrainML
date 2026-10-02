import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { FolderGit2, Plus, ArrowRight, Database, Box, Calendar, Tag, Shield } from 'lucide-react'
import { authStore, DEMO_PROJECTS } from '../../services/authStore'
import { Project } from '../../types'

export function ProjectsList() {
  const navigate = useNavigate()
  const [projects, setProjects] = useState<Project[]>(DEMO_PROJECTS)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [newProjectName, setNewProjectName] = useState('')
  const [newProjectDesc, setNewProjectDesc] = useState('')
  const [newProjectTag, setNewProjectTag] = useState('Classification')

  const handleCreateProject = (e: React.FormEvent) => {
    e.preventDefault()
    if (!newProjectName.trim()) return

    const newProj: Project = {
      id: `proj_${Date.now()}`,
      name: newProjectName.trim(),
      description: newProjectDesc.trim() || 'Custom AutoML & Data Science Project.',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      dataset_count: 0,
      experiment_count: 0,
      model_count: 0,
      active_deployment: false,
      status: 'active',
      tags: [newProjectTag, 'Private'],
    }

    const updated = [newProj, ...projects]
    setProjects(updated)
    authStore.setCurrentProject(newProj)
    setIsModalOpen(false)
    setNewProjectName('')
    setNewProjectDesc('')
  }

  const handleSelect = (proj: Project) => {
    authStore.setCurrentProject(proj)
    navigate(`/app/projects/${proj.id}`)
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h1 style={{ fontSize: '1.6rem', fontWeight: 800, margin: 0 }}>Projects Workspace</h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', margin: '4px 0 0 0' }}>
            Multi-tenant isolated data science environments. Every project strictly encapsulates datasets, models, and secrets.
          </p>
        </div>

        <button
          onClick={() => setIsModalOpen(true)}
          className="btn btn-primary"
          style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
        >
          <Plus size={16} /> New Project
        </button>
      </div>

      {/* Projects Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: '20px' }}>
        {projects.map((proj) => (
          <div
            key={proj.id}
            style={{
              background: 'var(--bg-card)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-xl)',
              padding: '24px',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              transition: 'all 150ms ease',
            }}
          >
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <div
                    style={{
                      width: '36px',
                      height: '36px',
                      borderRadius: '8px',
                      background: 'rgba(99, 102, 241, 0.1)',
                      color: 'var(--primary-light)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}
                  >
                    <FolderGit2 size={18} />
                  </div>
                  <div>
                    <h3 style={{ fontSize: '1.05rem', fontWeight: 700, margin: 0 }}>{proj.name}</h3>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>ID: {proj.id}</div>
                  </div>
                </div>

                <span
                  style={{
                    fontSize: '0.65rem',
                    padding: '2px 8px',
                    borderRadius: 'var(--radius-full)',
                    background: proj.active_deployment ? 'rgba(16, 185, 129, 0.12)' : 'rgba(148, 163, 184, 0.12)',
                    color: proj.active_deployment ? 'var(--success)' : 'var(--text-muted)',
                    border: `1px solid ${proj.active_deployment ? 'rgba(16, 185, 129, 0.3)' : 'var(--border-subtle)'}`,
                    fontWeight: 600,
                  }}
                >
                  {proj.active_deployment ? 'DEPLOYED' : 'IN DEVELOPMENT'}
                </span>
              </div>

              <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.5, marginBottom: '16px' }}>
                {proj.description}
              </p>

              {/* Tags */}
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginBottom: '16px' }}>
                {proj.tags.map((tag) => (
                  <span
                    key={tag}
                    style={{
                      fontSize: '0.7rem',
                      padding: '2px 8px',
                      borderRadius: 'var(--radius-sm)',
                      background: 'rgba(255, 255, 255, 0.05)',
                      color: 'var(--text-muted)',
                    }}
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>

            {/* Metrics Footer */}
            <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '14px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '14px' }}>
                <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <Database size={13} /> {proj.dataset_count} Datasets
                </span>
                <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <Box size={13} /> {proj.model_count} Models
                </span>
              </div>

              <button
                onClick={() => handleSelect(proj)}
                className="btn btn-secondary"
                style={{ width: '100%', display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '6px' }}
              >
                <span>Open Project Workspace</span>
                <ArrowRight size={14} />
              </button>
            </div>
          </div>
        ))}
      </div>

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
                  Description
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
                <button type="submit" className="btn btn-primary">
                  Create Workspace
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
