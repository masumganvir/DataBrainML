import React, { useState, useEffect } from 'react'
import { Outlet, useLocation, Link } from 'react-router-dom'
import TopBar from './TopBar'
import Sidebar from './Sidebar'
import CommandPalette from '../ui/CommandPalette'
import ErrorBoundary from '../ui/ErrorBoundary'
import { authStore } from '../../services/authStore'
import { projectsApi } from '../../services/api'
import { ChevronRight, Home } from 'lucide-react'

export function AppShell() {
  const location = useLocation()
  const [isCommandPaletteOpen, setIsCommandPaletteOpen] = useState(false)
  const [currentProject, setCurrentProject] = useState(authStore.getState().currentProject)

  useEffect(() => {
    return authStore.subscribe(() => {
      setCurrentProject(authStore.getState().currentProject)
    })
  }, [])

  // Synchronize current project with active route
  useEffect(() => {
    const match = location.pathname.match(/\/projects\/([^\/]+)/)
    if (match && match[1] && match[1] !== 'new') {
      const routeProjId = match[1]
      if (currentProject?.id !== routeProjId) {
        projectsApi.get(routeProjId)
          .then((p) => {
            if (p && p.name) authStore.setCurrentProject(p)
          })
          .catch(() => {})
      }
    }
  }, [location.pathname, currentProject?.id])

  // Global Ctrl+K / Cmd+K shortcut listener
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault()
        setIsCommandPaletteOpen((prev) => !prev)
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [])

  // Build clean breadcrumbs from path
  const pathParts = location.pathname.split('/').filter(Boolean)
  const breadcrumbItems = pathParts.map((part, index) => {
    const url = `/${pathParts.slice(0, index + 1).join('/')}`
    const label = part.charAt(0).toUpperCase() + part.slice(1).replace(/-/g, ' ')
    return { url, label }
  })

  return (
    <div className="app-container">
      {/* Collapsible Left Sidebar */}
      <Sidebar />

      {/* Main Viewport */}
      <div className="main-viewport">
        {/* Top Header Bar */}
        <TopBar onOpenCommandPalette={() => setIsCommandPaletteOpen(true)} />

        {/* Breadcrumbs Bar */}
        <div
          style={{
            padding: '8px 24px',
            background: 'rgba(15, 23, 42, 0.3)',
            borderBottom: '1px solid var(--border-subtle)',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: '0.8rem',
            color: 'var(--text-muted)',
          }}
        >
          <Link to="/app/dashboard" style={{ color: 'inherit', textDecoration: 'none', display: 'flex', alignItems: 'center' }}>
            <Home size={13} />
          </Link>
          {breadcrumbItems.map((item, idx) => (
            <React.Fragment key={item.url}>
              <ChevronRight size={12} />
              {idx === breadcrumbItems.length - 1 ? (
                <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{item.label}</span>
              ) : (
                <Link to={item.url} style={{ color: 'inherit', textDecoration: 'none' }}>
                  {item.label}
                </Link>
              )}
            </React.Fragment>
          ))}
          {currentProject && (
            <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Project:</span>
              <span
                style={{
                  fontSize: '0.75rem',
                  padding: '2px 8px',
                  borderRadius: 'var(--radius-full)',
                  background: 'rgba(99, 102, 241, 0.1)',
                  color: 'var(--primary-light)',
                  border: '1px solid rgba(99, 102, 241, 0.25)',
                  fontWeight: 600,
                }}
              >
                {currentProject.name}
              </span>
            </div>
          )}
        </div>

        {/* Scrollable Main Content with Error Boundary */}
        <main className="main-content-scroll">
          <ErrorBoundary>
            <Outlet />
          </ErrorBoundary>
        </main>
      </div>

      {/* Global Command Palette */}
      <CommandPalette
        isOpen={isCommandPaletteOpen}
        onClose={() => setIsCommandPaletteOpen(false)}
      />
    </div>
  )
}

export default AppShell
