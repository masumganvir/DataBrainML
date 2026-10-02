import React, { useState, useEffect } from 'react'
import { NavLink } from 'react-router-dom'
import {
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
  Network,
  Settings,
  ShieldCheck,
  ChevronLeft,
  ChevronRight,
  Sparkles,
} from 'lucide-react'
import { authStore } from '../../services/authStore'

export default function Sidebar() {
  const [isCollapsed, setIsCollapsed] = useState(() => {
    return localStorage.getItem('datalab_sidebar_collapsed') === 'true'
  })
  const [userRole, setUserRole] = useState(authStore.getState().user?.role || 'data_scientist')

  useEffect(() => {
    return authStore.subscribe(() => {
      setUserRole(authStore.getState().user?.role || 'data_scientist')
    })
  }, [])

  const toggleCollapse = () => {
    const next = !isCollapsed
    setIsCollapsed(next)
    localStorage.setItem('datalab_sidebar_collapsed', String(next))
  }

  // Keyboard shortcut Ctrl+B or Cmd+B to toggle sidebar
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'b') {
        e.preventDefault()
        toggleCollapse()
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isCollapsed])

  const navItems = [
    { label: 'Dashboard', to: '/dashboard', icon: LayoutDashboard },
    { label: 'Projects', to: '/projects', icon: FolderGit2 },
    { label: 'Datasets', to: '/app/datasets', icon: Database },
    { label: 'Runs', to: '/projects', icon: Activity },
    { label: 'Visualizations', to: '/app/pipelines', icon: GitFork },
    { label: 'Models', to: '/app/models', icon: Box },
    { label: 'Experiments', to: '/app/experiments', icon: FlaskConical },
    { label: 'Reports', to: '/app/reports', icon: FileText },
    { label: 'Deployments', to: '/app/deployments', icon: Rocket },
    { label: 'Monitoring', to: '/app/monitoring', icon: ShieldCheck },
    { label: 'Assistant', to: '/app/assistant', icon: Bot },
    { label: 'Settings', to: '/app/settings', icon: Settings },
  ]

  const isAdmin = userRole === 'admin' || userRole === 'owner'

  return (
    <aside className={`app-sidebar ${isCollapsed ? 'collapsed' : ''}`}>
      {/* New Project Quick Action */}
      <div style={{ padding: '14px 12px 6px 12px' }}>
        <NavLink
          to="/projects/new"
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px',
            padding: isCollapsed ? '10px' : '10px 14px',
            borderRadius: 'var(--radius-md)',
            background: 'linear-gradient(135deg, var(--primary) 0%, #4338ca 100%)',
            color: '#fff',
            textDecoration: 'none',
            fontSize: '0.84rem',
            fontWeight: 700,
            boxShadow: '0 4px 12px rgba(99, 102, 241, 0.3)',
          }}
          title={isCollapsed ? 'New Project' : undefined}
        >
          <Sparkles size={16} />
          {!isCollapsed && <span>New Project</span>}
        </NavLink>
      </div>

      {/* Navigation List */}
      <div style={{ flex: 1, padding: '10px 0', overflowY: 'auto' }}>
        <div
          style={{
            padding: '0 16px 8px 16px',
            fontSize: '0.7rem',
            fontWeight: 700,
            color: 'var(--text-muted)',
            letterSpacing: '0.05em',
            display: isCollapsed ? 'none' : 'block',
          }}
        >
          WORKBENCH
        </div>

        {navItems.map((item) => {
          const Icon = item.icon
          return (
            <NavLink
              key={item.label}
              to={item.to}
              className={({ isActive }) => `sidebar-nav-item ${isActive ? 'active' : ''}`}
              title={isCollapsed ? item.label : undefined}
            >
              <Icon size={18} style={{ flexShrink: 0 }} />
              {!isCollapsed && <span>{item.label}</span>}
            </NavLink>
          )
        })}

        {/* Administration Section */}
        {isAdmin && (
          <>
            <div
              style={{
                padding: '16px 16px 8px 16px',
                fontSize: '0.7rem',
                fontWeight: 700,
                color: 'var(--text-muted)',
                letterSpacing: '0.05em',
                display: isCollapsed ? 'none' : 'block',
              }}
            >
              GOVERNANCE & AUDIT
            </div>
            <NavLink
              to="/admin/audit-logs"
              className={({ isActive }) => `sidebar-nav-item ${isActive ? 'active' : ''}`}
              title={isCollapsed ? 'Admin Audit Trail' : undefined}
            >
              <ShieldCheck size={18} style={{ flexShrink: 0, color: 'var(--secondary-accent)' }} />
              {!isCollapsed && <span>Audit Trail & Admin</span>}
            </NavLink>
          </>
        )}
      </div>

      {/* Footer Controls: Settings & Collapse Toggle */}
      <div
        style={{
          borderTop: '1px solid var(--border-subtle)',
          padding: '12px 0',
          background: 'rgba(10, 15, 29, 0.4)',
        }}
      >
        <NavLink
          to="/app/settings/profile"
          className={({ isActive }) => `sidebar-nav-item ${isActive ? 'active' : ''}`}
          title={isCollapsed ? 'Settings' : undefined}
        >
          <Settings size={18} style={{ flexShrink: 0 }} />
          {!isCollapsed && <span>Settings & Security</span>}
        </NavLink>

        <button
          onClick={toggleCollapse}
          title={isCollapsed ? 'Expand sidebar (Ctrl+B)' : 'Collapse sidebar (Ctrl+B)'}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            width: 'calc(100% - 20px)',
            margin: '4px 10px',
            padding: '8px 14px',
            borderRadius: 'var(--radius-md)',
            background: 'transparent',
            border: 'none',
            color: 'var(--text-muted)',
            cursor: 'pointer',
            fontSize: '0.8rem',
            textAlign: 'left',
          }}
        >
          {isCollapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
          {!isCollapsed && <span>Collapse Sidebar</span>}
        </button>
      </div>
    </aside>
  )
}
