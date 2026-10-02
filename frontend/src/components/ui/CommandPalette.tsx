import React, { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Search,
  LayoutDashboard,
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
  ShieldCheck,
  Upload,
  Play,
  Moon,
  Sun,
  X,
} from 'lucide-react'
import { authStore } from '../../services/authStore'

interface CommandPaletteProps {
  isOpen: boolean
  onClose: () => void
}

interface CommandItem {
  id: string
  title: string
  category: 'Navigation' | 'Actions' | 'Settings'
  icon: React.ElementType
  action: () => void
  shortcut?: string
}

export default function CommandPalette({ isOpen, onClose }: CommandPaletteProps) {
  const navigate = useNavigate()
  const [query, setQuery] = useState('')
  const [selectedIndex, setSelectedIndex] = useState(0)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 50)
      setQuery('')
      setSelectedIndex(0)
    }
  }, [isOpen])

  const commands: CommandItem[] = [
    {
      id: 'nav-dash',
      title: 'Go to Dashboard',
      category: 'Navigation',
      icon: LayoutDashboard,
      action: () => { navigate('/app/dashboard'); onClose(); },
    },
    {
      id: 'nav-proj',
      title: 'View All Projects',
      category: 'Navigation',
      icon: FolderGit2,
      action: () => { navigate('/app/projects'); onClose(); },
    },
    {
      id: 'nav-data',
      title: 'Datasets & Upload Explorer',
      category: 'Navigation',
      icon: Database,
      action: () => { navigate('/app/datasets'); onClose(); },
    },
    {
      id: 'nav-exp',
      title: 'AutoML Experiment Laboratory',
      category: 'Navigation',
      icon: FlaskConical,
      action: () => { navigate('/app/experiments'); onClose(); },
    },
    {
      id: 'nav-pipe',
      title: 'Visual Pipeline Graph',
      category: 'Navigation',
      icon: GitFork,
      action: () => { navigate('/app/pipelines'); onClose(); },
    },
    {
      id: 'nav-models',
      title: 'Model Registry & Explainability',
      category: 'Navigation',
      icon: Box,
      action: () => { navigate('/app/models'); onClose(); },
    },
    {
      id: 'nav-deploy',
      title: 'Deployments & Microservices',
      category: 'Navigation',
      icon: Rocket,
      action: () => { navigate('/app/deployments'); onClose(); },
    },
    {
      id: 'nav-mon',
      title: 'Monitoring & Drift Detection',
      category: 'Navigation',
      icon: Activity,
      action: () => { navigate('/app/monitoring'); onClose(); },
    },
    {
      id: 'nav-rep',
      title: 'Executive Reports & PDF Export',
      category: 'Navigation',
      icon: FileText,
      action: () => { navigate('/app/reports'); onClose(); },
    },
    {
      id: 'nav-nb',
      title: 'Jupyter Notebooks Viewer',
      category: 'Navigation',
      icon: BookOpen,
      action: () => { navigate('/app/notebooks'); onClose(); },
    },
    {
      id: 'nav-ai',
      title: 'AI Data Scientist Assistant',
      category: 'Navigation',
      icon: Bot,
      action: () => { navigate('/app/assistant'); onClose(); },
    },
    {
      id: 'act-upload',
      title: 'Action: Upload New Dataset',
      category: 'Actions',
      icon: Upload,
      action: () => { navigate('/app/datasets'); onClose(); },
    },
    {
      id: 'act-train',
      title: 'Action: Train Candidate Models',
      category: 'Actions',
      icon: Play,
      action: () => { navigate('/app/experiments'); onClose(); },
    },
    {
      id: 'nav-sec',
      title: 'Security Center & Active Sessions',
      category: 'Settings',
      icon: Settings,
      action: () => { navigate('/app/settings/security'); onClose(); },
    },
    {
      id: 'nav-audit',
      title: 'Admin Audit Trail & Observability',
      category: 'Settings',
      icon: ShieldCheck,
      action: () => { navigate('/admin/audit-logs'); onClose(); },
    },
  ]

  const filtered = commands.filter((c) =>
    c.title.toLowerCase().includes(query.toLowerCase()) ||
    c.category.toLowerCase().includes(query.toLowerCase())
  )

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setSelectedIndex((prev) => (prev + 1) % (filtered.length || 1))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setSelectedIndex((prev) => (prev - 1 + filtered.length) % (filtered.length || 1))
    } else if (e.key === 'Enter' && filtered[selectedIndex]) {
      e.preventDefault()
      filtered[selectedIndex].action()
    } else if (e.key === 'Escape') {
      onClose()
    }
  }

  if (!isOpen) return null

  return (
    <div className="cmd-palette-backdrop" onClick={onClose}>
      <div className="cmd-palette-modal" onClick={(e) => e.stopPropagation()}>
        {/* Search Input */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            padding: '16px 20px',
            borderBottom: '1px solid var(--border-subtle)',
          }}
        >
          <Search size={18} color="var(--primary-light)" />
          <input
            ref={inputRef}
            type="text"
            placeholder="Type a command or search platform resources..."
            value={query}
            onChange={(e) => {
              setQuery(e.target.value)
              setSelectedIndex(0)
            }}
            onKeyDown={handleKeyDown}
            style={{
              flex: 1,
              background: 'transparent',
              border: 'none',
              outline: 'none',
              color: 'var(--text-primary)',
              fontSize: '1rem',
              fontFamily: 'var(--font-sans)',
            }}
          />
          <button
            onClick={onClose}
            style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
          >
            <X size={18} />
          </button>
        </div>

        {/* Results List */}
        <div style={{ maxHeight: '380px', overflowY: 'auto', padding: '8px' }}>
          {filtered.length === 0 ? (
            <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.875rem' }}>
              No matching commands found for "{query}"
            </div>
          ) : (
            filtered.map((item, idx) => {
              const Icon = item.icon
              const isSelected = idx === selectedIndex
              return (
                <div
                  key={item.id}
                  onClick={item.action}
                  onMouseEnter={() => setSelectedIndex(idx)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '10px 14px',
                    borderRadius: 'var(--radius-md)',
                    cursor: 'pointer',
                    background: isSelected ? 'rgba(99, 102, 241, 0.15)' : 'transparent',
                    border: isSelected ? '1px solid rgba(99, 102, 241, 0.3)' : '1px solid transparent',
                    color: isSelected ? 'var(--text-primary)' : 'var(--text-secondary)',
                    transition: 'all 120ms ease',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <Icon size={17} color={isSelected ? 'var(--primary-light)' : 'var(--text-muted)'} />
                    <span style={{ fontSize: '0.9rem', fontWeight: isSelected ? 600 : 400 }}>{item.title}</span>
                  </div>
                  <span
                    style={{
                      fontSize: '0.7rem',
                      padding: '2px 8px',
                      borderRadius: 'var(--radius-full)',
                      background: 'rgba(255, 255, 255, 0.06)',
                      color: 'var(--text-muted)',
                    }}
                  >
                    {item.category}
                  </span>
                </div>
              )
            })
          )}
        </div>

        {/* Footer shortcuts */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '10px 18px',
            background: 'rgba(10, 15, 29, 0.6)',
            borderTop: '1px solid var(--border-subtle)',
            fontSize: '0.75rem',
            color: 'var(--text-muted)',
          }}
        >
          <span>Use ↑↓ arrows to navigate, Enter to select</span>
          <span>ESC to dismiss</span>
        </div>
      </div>
    </div>
  )
}
