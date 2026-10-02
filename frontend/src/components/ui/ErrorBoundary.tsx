import React, { Component, ErrorInfo, ReactNode } from 'react'
import { AlertTriangle, RefreshCw, Home, ShieldAlert } from 'lucide-react'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
  errorCode: string
  safeMessage: string
}

export default class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    errorCode: '',
    safeMessage: '',
  }

  public static getDerivedStateFromError(error: Error): State {
    // Generate sanitized unpredictable reference ID
    const randomHex = Math.random().toString(16).substring(2, 8).toUpperCase()
    return {
      hasError: true,
      errorCode: `ERR-${randomHex}`,
      safeMessage: 'An unexpected application condition occurred while processing this operation.',
    }
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log detailed diagnostics strictly to local client console or secure server audit sink
    console.error('[DataLab Security Error Boundary] Caught exception:', {
      error: error.message,
      componentStack: errorInfo.componentStack,
    })
  }

  private handleReset = () => {
    this.setState({ hasError: false, errorCode: '', safeMessage: '' })
    window.location.reload()
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div
          style={{
            minHeight: '80vh',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '24px',
            textAlign: 'center',
          }}
        >
          <div
            style={{
              width: '64px',
              height: '64px',
              borderRadius: '16px',
              background: 'rgba(239, 68, 68, 0.1)',
              border: '1px solid rgba(239, 68, 68, 0.25)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: '20px',
            }}
          >
            <ShieldAlert size={32} color="var(--danger)" />
          </div>

          <h2 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '8px' }}>
            Operation Interrupted
          </h2>
          <p style={{ color: 'var(--text-secondary)', maxWidth: '480px', marginBottom: '16px', fontSize: '0.95rem' }}>
            {this.state.safeMessage}
          </p>

          <div
            style={{
              padding: '6px 14px',
              borderRadius: 'var(--radius-full)',
              background: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid var(--border-subtle)',
              fontSize: '0.8rem',
              fontFamily: 'var(--font-mono)',
              color: 'var(--text-muted)',
              marginBottom: '24px',
            }}
          >
            Reference Code: <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{this.state.errorCode}</span>
          </div>

          <div style={{ display: 'flex', gap: '12px' }}>
            <button
              onClick={this.handleReset}
              className="btn btn-primary"
              style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
            >
              <RefreshCw size={16} /> Reload Interface
            </button>
            <a
              href="/app/dashboard"
              className="btn btn-secondary"
              style={{ display: 'flex', alignItems: 'center', gap: '8px', textDecoration: 'none' }}
            >
              <Home size={16} /> Return to Dashboard
            </a>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}
