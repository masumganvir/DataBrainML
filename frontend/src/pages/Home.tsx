import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { sessionsApi } from '@/services/api'
import { Session } from '@/types'
import { Sparkles, Plus, Database, ArrowRight, BarChart3, ShieldCheck, Cpu, Clock, Trash2 } from 'lucide-react'

export default function Home() {
  const navigate = useNavigate()
  const [sessions, setSessions] = useState<Session[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isCreating, setIsCreating] = useState(false)
  const [newSessionName, setNewSessionName] = useState('')
  const [showModal, setShowModal] = useState(false)

  useEffect(() => {
    loadSessions()
  }, [])

  const loadSessions = async () => {
    try {
      setIsLoading(true)
      const data = await sessionsApi.list()
      setSessions(data)
    } catch (err) {
      console.error('Failed to load sessions:', err)
    } finally {
      setIsLoading(false)
    }
  }

  const handleCreateSession = async (e?: React.FormEvent) => {
    if (e) e.preventDefault()
    try {
      setIsCreating(true)
      const session = await sessionsApi.create(newSessionName.trim() || undefined)
      navigate(`/analysis/${session.id}`)
    } catch (err) {
      console.error('Failed to create session:', err)
    } finally {
      setIsCreating(false)
      setShowModal(false)
    }
  }

  const handleDeleteSession = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation()
    if (!confirm('Are you sure you want to delete this session?')) return
    try {
      await sessionsApi.delete(id)
      setSessions(prev => prev.filter(s => s.id !== id))
    } catch (err) {
      console.error('Failed to delete session:', err)
    }
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Top Navigation */}
      <header style={{
        height: '64px',
        borderBottom: '1px solid var(--border-subtle)',
        background: 'rgba(9, 13, 22, 0.85)',
        backdropFilter: 'blur(12px)',
        position: 'sticky',
        top: 0,
        zIndex: 50,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 32px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            width: '36px',
            height: '36px',
            borderRadius: '10px',
            background: 'var(--primary-gradient)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 0 15px rgba(99, 102, 241, 0.5)'
          }}>
            <Sparkles size={20} color="#fff" />
          </div>
          <div>
            <span style={{ fontSize: '1.2rem', fontWeight: 800, letterSpacing: '-0.03em', background: 'linear-gradient(to right, #ffffff, #c7d2fe)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
              DataWise AI
            </span>
            <span style={{ marginLeft: '8px', fontSize: '0.75rem', padding: '2px 6px', borderRadius: '4px', background: 'rgba(99, 102, 241, 0.15)', color: '#818cf8', border: '1px solid rgba(99, 102, 241, 0.3)' }}>
              v0.1.0
            </span>
          </div>
        </div>

        <button
          className="btn btn-primary"
          onClick={() => setShowModal(true)}
        >
          <Plus size={16} />
          <span>New Analysis</span>
        </button>
      </header>

      {/* Hero Section */}
      <main style={{ flex: 1, maxWidth: '1200px', width: '100%', margin: '0 auto', padding: '48px 24px' }}>
        <div style={{ textAlign: 'center', marginBottom: '48px' }}>
          <div className="badge badge-primary" style={{ marginBottom: '16px', padding: '6px 14px' }}>
            <Sparkles size={13} />
            <span>Autonomous Data Science & ML Preparation Agent</span>
          </div>
          <h1 style={{ fontSize: '2.8rem', marginBottom: '16px', fontWeight: 800 }}>
            Transform Raw Data into <br />
            <span style={{ background: 'var(--primary-gradient)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
              Production-Ready ML Pipelines
            </span>
          </h1>
          <p style={{ fontSize: '1.1rem', maxWidth: '680px', margin: '0 auto', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
            Upload any CSV, Excel, or JSON dataset. DataWise AI autonomously profiles, cleans, engineers features, generates interactive visualizations, and builds reproducible scikit-learn preprocessing pipelines with human-in-the-loop verification.
          </p>

          <div style={{ marginTop: '32px', display: 'flex', justifyContent: 'center', gap: '16px' }}>
            <button
              className="btn btn-primary btn-lg"
              onClick={() => setShowModal(true)}
            >
              <Plus size={18} />
              <span>Start Free Analysis</span>
            </button>
          </div>
        </div>

        {/* Feature Highlights Grid */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
          gap: '20px',
          marginBottom: '56px'
        }}>
          <div className="glass-card" style={{ padding: '24px' }}>
            <div style={{ width: '40px', height: '40px', borderRadius: '8px', background: 'rgba(99, 102, 241, 0.15)', color: '#818cf8', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '16px' }}>
              <BarChart3 size={22} />
            </div>
            <h3 style={{ marginBottom: '8px', fontSize: '1.1rem' }}>Smart Profiling & Viz</h3>
            <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
              Automated schema inference, outlier detection, distribution analysis, and intelligent interactive Plotly chart recommendations.
            </p>
          </div>

          <div className="glass-card" style={{ padding: '24px' }}>
            <div style={{ width: '40px', height: '40px', borderRadius: '8px', background: 'rgba(16, 185, 129, 0.15)', color: '#34d399', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '16px' }}>
              <ShieldCheck size={22} />
            </div>
            <h3 style={{ marginBottom: '8px', fontSize: '1.1rem' }}>Zero Unintended Mutations</h3>
            <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
              Non-destructive workflows with full immutable dataset versioning and human-in-the-loop verification on destructive proposals.
            </p>
          </div>

          <div className="glass-card" style={{ padding: '24px' }}>
            <div style={{ width: '40px', height: '40px', borderRadius: '8px', background: 'rgba(6, 182, 212, 0.15)', color: '#22d3ee', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '16px' }}>
              <Cpu size={22} />
            </div>
            <h3 style={{ marginBottom: '8px', fontSize: '1.1rem' }}>sklearn Pipeline Gen</h3>
            <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
              Exports clean, runnable ColumnTransformer and Pipeline Python code ready for training, deployment, and inference.
            </p>
          </div>
        </div>

        {/* Recent Sessions List */}
        <div style={{ marginTop: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Database size={20} color="var(--primary-light)" />
              <h2>Analysis Sessions</h2>
            </div>
            <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              {sessions.length} {sessions.length === 1 ? 'session' : 'sessions'} found
            </span>
          </div>

          {isLoading ? (
            <div className="glass-card" style={{ padding: '48px', textAlign: 'center' }}>
              <div className="spinner" style={{ margin: '0 auto 16px' }}></div>
              <p>Loading sessions…</p>
            </div>
          ) : sessions.length === 0 ? (
            <div className="glass-card" style={{ padding: '48px', textAlign: 'center' }}>
              <Database size={40} color="var(--text-muted)" style={{ margin: '0 auto 16px', opacity: 0.5 }} />
              <h3 style={{ marginBottom: '8px' }}>No Sessions Yet</h3>
              <p style={{ marginBottom: '24px', maxWidth: '400px', margin: '0 auto 24px' }}>
                Create your first analysis session to upload datasets, interact with the agent, and generate ML pipelines.
              </p>
              <button className="btn btn-primary" onClick={() => setShowModal(true)}>
                <Plus size={16} />
                <span>Create New Session</span>
              </button>
            </div>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: '16px' }}>
              {sessions.map(session => (
                <div
                  key={session.id}
                  className="glass-card glass-card-hover"
                  style={{ padding: '20px', cursor: 'pointer', display: 'flex', flexDirection: 'column', justifyContent: 'space-between', gap: '16px' }}
                  onClick={() => navigate(`/analysis/${session.id}`)}
                >
                  <div>
                    <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '8px' }}>
                      <h3 style={{ fontSize: '1.05rem', fontWeight: 600 }}>{session.name}</h3>
                      <button
                        className="btn btn-sm btn-outline"
                        style={{ padding: '4px', borderColor: 'transparent', color: 'var(--text-muted)' }}
                        title="Delete Session"
                        onClick={(e) => handleDeleteSession(e, session.id)}
                      >
                        <Trash2 size={15} />
                      </button>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                      <span className="badge badge-primary">{session.current_stage}</span>
                      <span className="badge badge-neutral">{session.status}</span>
                    </div>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderTop: '1px solid var(--border-subtle)', paddingTop: '12px', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <Clock size={13} />
                      {new Date(session.created_at).toLocaleDateString()}
                    </span>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '4px', color: 'var(--primary-light)' }}>
                      Open <ArrowRight size={13} />
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>

      {/* Create Session Modal */}
      {showModal && (
        <div style={{
          position: 'fixed',
          inset: 0,
          background: 'rgba(0, 0, 0, 0.7)',
          backdropFilter: 'blur(6px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 100,
          padding: '16px'
        }}>
          <div className="glass-card" style={{ maxWidth: '440px', width: '100%', padding: '28px' }}>
            <h3 style={{ marginBottom: '8px' }}>Create New Session</h3>
            <p style={{ fontSize: '0.875rem', marginBottom: '20px' }}>
              Give your data science project a name to organize your exploration and artifacts.
            </p>

            <form onSubmit={handleCreateSession}>
              <div style={{ marginBottom: '20px' }}>
                <label style={{ display: 'block', marginBottom: '6px', fontSize: '0.85rem', fontWeight: 600 }}>
                  Session Name
                </label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="e.g. Credit Card Fraud Detection, House Price Forecast..."
                  value={newSessionName}
                  onChange={(e) => setNewSessionName(e.target.value)}
                  autoFocus
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setShowModal(false)}
                  disabled={isCreating}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={isCreating}
                >
                  {isCreating ? 'Creating…' : 'Create Session'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
