import React, { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  Search,
  Bell,
  Sun,
  Moon,
  Shield,
  Layers,
  ChevronDown,
  LogOut,
  User as UserIcon,
  Wifi,
  WifiOff,
  Sparkles,
  Command,
} from 'lucide-react'
import { branding } from '../../config/branding'
import { authStore, DEMO_PROJECTS } from '../../services/authStore'
import { Project } from '../../types'

interface TopBarProps {
  onOpenCommandPalette: () => void
}

export default function TopBar({ onOpenCommandPalette }: TopBarProps) {
  const navigate = useNavigate()
  const [storeState, setStoreState] = useState(authStore.getState())
  const [isProjectDropdownOpen, setIsProjectDropdownOpen] = useState(false)
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false)
  const [isNotificationsOpen, setIsNotificationsOpen] = useState(false)

  useEffect(() => {
    return authStore.subscribe(() => setStoreState({ ...authStore.getState() }))
  }, [])

  const { currentProject, theme, isOnline, user, notificationsCount } = storeState

  const handleSelectProject = (project: Project) => {
    authStore.setCurrentProject(project)
    setIsProjectDropdownOpen(false)
  }

  const toggleTheme = () => {
    authStore.setTheme(theme === 'dark' ? 'light' : 'dark')
  }

  const handleLogout = () => {
    authStore.logout()
    navigate('/login')
  }

  return (
    <header className="app-topbar">
      {/* Left: Branding & Project Selector */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
        <Link
          to="/app/dashboard"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            textDecoration: 'none',
            color: 'inherit',
          }}
        >
          <div
            style={{
              width: '32px',
              height: '32px',
              borderRadius: '8px',
              background: 'linear-gradient(135deg, #06b6d4 0%, #6366f1 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 0 15px rgba(6, 182, 212, 0.4)',
            }}
          >
            <Sparkles size={18} color="#ffffff" />
          </div>
          <div>
            <span style={{ fontWeight: 800, fontSize: '1.05rem', letterSpacing: '-0.02em' }}>
              {branding.productName}
            </span>
            <span
              style={{
                marginLeft: '8px',
                fontSize: '0.65rem',
                padding: '2px 6px',
                borderRadius: '4px',
                background: 'rgba(99, 102, 241, 0.15)',
                color: 'var(--primary-light)',
                border: '1px solid rgba(99, 102, 241, 0.3)',
                fontWeight: 600,
              }}
            >
              DESKTOP
            </span>
          </div>
        </Link>

        {/* Project Context Switcher */}
        <div style={{ position: 'relative' }}>
          <button
            onClick={() => setIsProjectDropdownOpen(!isProjectDropdownOpen)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '6px 12px',
              background: 'rgba(15, 23, 42, 0.6)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-md)',
              color: 'var(--text-primary)',
              fontSize: '0.85rem',
              cursor: 'pointer',
            }}
          >
            <Layers size={15} color="var(--primary-light)" />
            <span style={{ maxWidth: '160px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {currentProject?.name || 'Select Project'}
            </span>
            <ChevronDown size={14} color="var(--text-muted)" />
          </button>

          {isProjectDropdownOpen && (
            <div
              style={{
                position: 'absolute',
                top: '100%',
                left: 0,
                marginTop: '6px',
                width: '240px',
                background: 'var(--bg-secondary)',
                border: '1px solid var(--border-medium)',
                borderRadius: 'var(--radius-md)',
                boxShadow: 'var(--shadow-lg)',
                padding: '6px',
                zIndex: 50,
              }}
            >
              <div style={{ padding: '6px 10px', fontSize: '0.7rem', color: 'var(--text-muted)', fontWeight: 600 }}>
                ACTIVE PROJECTS
              </div>
              {DEMO_PROJECTS.map((p) => (
                <div
                  key={p.id}
                  onClick={() => handleSelectProject(p)}
                  style={{
                    padding: '8px 10px',
                    borderRadius: 'var(--radius-sm)',
                    fontSize: '0.85rem',
                    cursor: 'pointer',
                    background: p.id === currentProject?.id ? 'rgba(99, 102, 241, 0.15)' : 'transparent',
                    color: p.id === currentProject?.id ? 'var(--primary-light)' : 'var(--text-secondary)',
                    fontWeight: p.id === currentProject?.id ? 600 : 400,
                  }}
                >
                  {p.name}
                </div>
              ))}
              <div style={{ borderTop: '1px solid var(--border-subtle)', margin: '6px 0' }} />
              <Link
                to="/app/projects"
                onClick={() => setIsProjectDropdownOpen(false)}
                style={{
                  display: 'block',
                  padding: '6px 10px',
                  fontSize: '0.8rem',
                  color: 'var(--primary-light)',
                  textDecoration: 'none',
                }}
              >
                + Manage All Projects
              </Link>
            </div>
          )}
        </div>
      </div>

      {/* Middle: Command Palette Quick Search */}
      <div style={{ flex: 1, maxWidth: '420px', margin: '0 20px' }}>
        <button
          onClick={onOpenCommandPalette}
          style={{
            width: '100%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '7px 14px',
            background: 'rgba(15, 23, 42, 0.5)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-full)',
            color: 'var(--text-muted)',
            fontSize: '0.85rem',
            cursor: 'pointer',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Search size={15} />
            <span>Search models, datasets, jobs...</span>
          </div>
          <span
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '2px',
              fontSize: '0.7rem',
              padding: '2px 6px',
              borderRadius: '4px',
              background: 'rgba(255, 255, 255, 0.08)',
              border: '1px solid var(--border-subtle)',
            }}
          >
            <Command size={11} /> K
          </span>
        </button>
      </div>

      {/* Right Controls: Connectivity, Alerts, Theme, Profile */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
        {/* Connection status */}
        <div
          title={isOnline ? 'Connected to backend clusters' : 'Offline Mode — Local Cache Active'}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            fontSize: '0.75rem',
            color: isOnline ? 'var(--success)' : 'var(--warning)',
            padding: '4px 8px',
            borderRadius: 'var(--radius-full)',
            background: isOnline ? 'rgba(16, 185, 129, 0.1)' : 'rgba(245, 158, 11, 0.1)',
            border: `1px solid ${isOnline ? 'rgba(16, 185, 129, 0.25)' : 'rgba(245, 158, 11, 0.25)'}`,
          }}
        >
          {isOnline ? <Wifi size={13} /> : <WifiOff size={13} />}
          <span>{isOnline ? 'ONLINE' : 'OFFLINE'}</span>
        </div>

        {/* Notifications Popover */}
        <div style={{ position: 'relative' }}>
          <button
            onClick={() => setIsNotificationsOpen(!isNotificationsOpen)}
            style={{
              background: 'transparent',
              border: 'none',
              color: 'var(--text-secondary)',
              cursor: 'pointer',
              padding: '6px',
              position: 'relative',
              display: 'flex',
              alignItems: 'center',
            }}
            title="Notifications"
          >
            <Bell size={18} />
            {notificationsCount > 0 && (
              <span
                style={{
                  position: 'absolute',
                  top: '2px',
                  right: '2px',
                  width: '8px',
                  height: '8px',
                  borderRadius: '50%',
                  background: 'var(--danger)',
                  boxShadow: '0 0 6px var(--danger)',
                }}
              />
            )}
          </button>

          {isNotificationsOpen && (
            <div
              style={{
                position: 'absolute',
                top: '100%',
                right: 0,
                marginTop: '10px',
                width: '320px',
                background: 'var(--bg-secondary)',
                border: '1px solid var(--border-medium)',
                borderRadius: 'var(--radius-lg)',
                boxShadow: 'var(--shadow-lg)',
                padding: '12px',
                zIndex: 60,
              }}
            >
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: '10px',
                  borderBottom: '1px solid var(--border-subtle)',
                  paddingBottom: '8px',
                }}
              >
                <span style={{ fontWeight: 600, fontSize: '0.85rem' }}>System Alerts</span>
                <button
                  onClick={() => authStore.clearNotifications()}
                  style={{ background: 'none', border: 'none', color: 'var(--primary-light)', fontSize: '0.75rem', cursor: 'pointer' }}
                >
                  Clear all
                </button>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <div style={{ padding: '8px', borderRadius: 'var(--radius-md)', background: 'rgba(245, 158, 11, 0.08)', border: '1px solid rgba(245, 158, 11, 0.2)' }}>
                  <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--warning)' }}>⚠️ Feature Drift Alert</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '2px' }}>
                    Feature `transaction_amount` exceeded PSI threshold (0.28).
                  </div>
                </div>
                <div style={{ padding: '8px', borderRadius: 'var(--radius-md)', background: 'rgba(16, 185, 129, 0.08)', border: '1px solid rgba(16, 185, 129, 0.2)' }}>
                  <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--success)' }}>✅ Model Trained & Registered</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '2px' }}>
                    LightGBM v2.1.0 passed 8-point production readiness audit.
                  </div>
                </div>
              </div>
              <Link
                to="/app/monitoring/alerts"
                onClick={() => setIsNotificationsOpen(false)}
                style={{ display: 'block', textAlign: 'center', marginTop: '10px', fontSize: '0.75rem', color: 'var(--primary-light)', textDecoration: 'none' }}
              >
                View all notifications in Alert Center →
              </Link>
            </div>
          )}
        </div>

        {/* Theme Switcher */}
        <button
          onClick={toggleTheme}
          style={{
            background: 'transparent',
            border: 'none',
            color: 'var(--text-secondary)',
            cursor: 'pointer',
            padding: '6px',
            display: 'flex',
            alignItems: 'center',
          }}
          title={theme === 'dark' ? 'Switch to Light Theme' : 'Switch to Dark Theme'}
        >
          {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
        </button>

        {/* User Profile Menu */}
        <div style={{ position: 'relative' }}>
          <button
            onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              background: 'transparent',
              border: 'none',
              color: 'var(--text-primary)',
              cursor: 'pointer',
              padding: '4px',
            }}
          >
            <div
              style={{
                width: '32px',
                height: '32px',
                borderRadius: '50%',
                background: 'linear-gradient(135deg, #6366f1 0%, #ec4899 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontWeight: 700,
                fontSize: '0.85rem',
                color: '#fff',
              }}
            >
              {user?.name?.charAt(0) || 'U'}
            </div>
            <div className="hidden md:block text-left">
              <div style={{ fontSize: '0.8rem', fontWeight: 600 }}>{user?.name || 'User'}</div>
              <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>{user?.role?.toUpperCase()}</div>
            </div>
          </button>

          {isUserMenuOpen && (
            <div
              style={{
                position: 'absolute',
                top: '100%',
                right: 0,
                marginTop: '10px',
                width: '220px',
                background: 'var(--bg-secondary)',
                border: '1px solid var(--border-medium)',
                borderRadius: 'var(--radius-lg)',
                boxShadow: 'var(--shadow-lg)',
                padding: '8px',
                zIndex: 60,
              }}
            >
              <div style={{ padding: '8px 10px', borderBottom: '1px solid var(--border-subtle)', marginBottom: '4px' }}>
                <div style={{ fontSize: '0.85rem', fontWeight: 600 }}>{user?.name}</div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{user?.email}</div>
                <div style={{ fontSize: '0.7rem', color: 'var(--primary-light)', marginTop: '4px' }}>
                  {user?.organization_name}
                </div>
              </div>
              <Link
                to="/app/settings/profile"
                onClick={() => setIsUserMenuOpen(false)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '8px 10px',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '0.85rem',
                  color: 'var(--text-secondary)',
                  textDecoration: 'none',
                }}
              >
                <UserIcon size={14} /> Profile & MFA
              </Link>
              <Link
                to="/app/settings/security"
                onClick={() => setIsUserMenuOpen(false)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '8px 10px',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '0.85rem',
                  color: 'var(--text-secondary)',
                  textDecoration: 'none',
                }}
              >
                <Shield size={14} /> Security Center
              </Link>
              <div style={{ borderTop: '1px solid var(--border-subtle)', margin: '4px 0' }} />
              <button
                onClick={handleLogout}
                style={{
                  width: '100%',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '8px 10px',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '0.85rem',
                  color: 'var(--danger)',
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  textAlign: 'left',
                }}
              >
                <LogOut size={14} /> Sign out
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}
