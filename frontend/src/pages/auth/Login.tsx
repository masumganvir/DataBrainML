/**
 * DataWise AI — Login Page (Supabase Auth)
 * Premium dark aesthetic with animated particle background.
 */

import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, Link, useLocation } from 'react-router-dom';
import { Mail, Lock, ArrowRight, AlertCircle, Eye, EyeOff, Cpu } from 'lucide-react';
import { useAuthStore } from '../../services/authStore';

// ── Animated particle canvas background ────────────────────────
const ParticleBackground: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animId: number;

    const resize = () => {
      canvas.width  = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    resize();
    window.addEventListener('resize', resize);

    type Dot = { x: number; y: number; vx: number; vy: number; r: number; opacity: number };
    const dots: Dot[] = Array.from({ length: 80 }, () => ({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      vx: (Math.random() - 0.5) * 0.4,
      vy: (Math.random() - 0.5) * 0.4,
      r:  Math.random() * 1.8 + 0.4,
      opacity: Math.random() * 0.5 + 0.15,
    }));

    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      // Draw connections
      for (let i = 0; i < dots.length; i++) {
        for (let j = i + 1; j < dots.length; j++) {
          const dx = dots[i].x - dots[j].x;
          const dy = dots[i].y - dots[j].y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < 140) {
            ctx.beginPath();
            ctx.strokeStyle = `rgba(99,102,241,${0.12 * (1 - dist / 140)})`;
            ctx.lineWidth = 0.6;
            ctx.moveTo(dots[i].x, dots[i].y);
            ctx.lineTo(dots[j].x, dots[j].y);
            ctx.stroke();
          }
        }
      }
      // Draw dots
      dots.forEach((d) => {
        ctx.beginPath();
        ctx.arc(d.x, d.y, d.r, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(139,92,246,${d.opacity})`;
        ctx.fill();
        d.x += d.vx;
        d.y += d.vy;
        if (d.x < 0 || d.x > canvas.width)  d.vx *= -1;
        if (d.y < 0 || d.y > canvas.height) d.vy *= -1;
      });
      animId = requestAnimationFrame(draw);
    };
    draw();
    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener('resize', resize);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: 'fixed', inset: 0, zIndex: 0,
        pointerEvents: 'none',
      }}
    />
  );
};

// ── Feature badge ──────────────────────────────────────────────
const FeatureBadge: React.FC<{ icon: string; label: string }> = ({ icon, label }) => (
  <div style={{
    display: 'flex', alignItems: 'center', gap: 8,
    padding: '6px 12px',
    background: 'rgba(99,102,241,0.08)',
    border: '1px solid rgba(99,102,241,0.2)',
    borderRadius: 999,
    fontSize: 11,
    color: 'var(--text-secondary)',
  }}>
    <span>{icon}</span>
    <span>{label}</span>
  </div>
);

// ── Main Login Component ───────────────────────────────────────
export const Login: React.FC = () => {
  const navigate  = useNavigate();
  const location  = useLocation();
  const { signIn, signInWithOAuth, signInAsDemo, isAuthenticated } = useAuthStore();

  const [email,     setEmail]     = useState('');
  const [password,  setPassword]  = useState('');
  const [showPw,    setShowPw]    = useState(false);
  const [error,     setError]     = useState('');
  const [loading,   setLoading]   = useState(false);
  const [oauthLoading, setOauthLoading] = useState<'google' | 'github' | null>(null);
  const [mounted,   setMounted]   = useState(false);

  useEffect(() => {
    setTimeout(() => setMounted(true), 50);
  }, []);

  // Redirect if already logged in
  useEffect(() => {
    if (isAuthenticated) {
      const from = (location.state as any)?.from?.pathname || '/projects';
      navigate(from, { replace: true });
    }
  }, [isAuthenticated, navigate, location]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      await signIn(email, password);
    } catch (err: any) {
      setError(err.message === 'Invalid login credentials'
        ? 'Incorrect email or password.'
        : err.message || 'Sign-in failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleOAuth = async (provider: 'google' | 'github') => {
    setOauthLoading(provider);
    setError('');
    try {
      await signInWithOAuth(provider);
    } catch (err: any) {
      setError(err.message || `Failed to sign in with ${provider}`);
      setOauthLoading(null);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      background: 'var(--bg-primary)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: 24,
      position: 'relative',
      overflow: 'hidden',
      fontFamily: 'var(--font-sans)',
    }}>
      <ParticleBackground />

      {/* Ambient glows */}
      <div style={{
        position: 'absolute', top: '15%', left: '25%',
        width: 600, height: 600,
        background: 'radial-gradient(circle, rgba(99,102,241,0.12) 0%, transparent 70%)',
        borderRadius: '50%', pointerEvents: 'none', zIndex: 0,
      }} />
      <div style={{
        position: 'absolute', bottom: '10%', right: '20%',
        width: 400, height: 400,
        background: 'radial-gradient(circle, rgba(168,85,247,0.10) 0%, transparent 70%)',
        borderRadius: '50%', pointerEvents: 'none', zIndex: 0,
      }} />

      {/* Left side — branding panel (hidden on small screens) */}
      <div style={{
        display: 'none',
        flexDirection: 'column',
        justifyContent: 'center',
        maxWidth: 420,
        marginRight: 80,
        position: 'relative', zIndex: 1,
        opacity: mounted ? 1 : 0,
        transform: mounted ? 'translateX(0)' : 'translateX(-20px)',
        transition: 'opacity 0.6s ease, transform 0.6s ease',
      }}
        className="left-brand-panel"
      >
        <div style={{
          display: 'inline-flex', alignItems: 'center', gap: 8,
          padding: '4px 12px',
          background: 'rgba(99,102,241,0.12)',
          border: '1px solid rgba(99,102,241,0.3)',
          borderRadius: 999, marginBottom: 24,
          fontSize: 11, color: 'var(--primary-light)',
          width: 'fit-content',
        }}>
          <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#10b981', display: 'inline-block' }} />
          Platform Online — All Systems Operational
        </div>

        <h1 style={{
          fontSize: 40, fontWeight: 800, lineHeight: 1.15,
          background: 'linear-gradient(135deg, #f8fafc 0%, #818cf8 100%)',
          WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
          marginBottom: 16,
        }}>
          The AI<br />Data Science<br />Platform
        </h1>
        <p style={{ color: 'var(--text-secondary)', lineHeight: 1.7, marginBottom: 32, fontSize: 14 }}>
          Upload a dataset, talk to the AI agent, get a production-ready ML pipeline
          — with full cloud storage and isolation per user.
        </p>

        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
          <FeatureBadge icon="🔍" label="AutoEDA" />
          <FeatureBadge icon="🤖" label="AutoML" />
          <FeatureBadge icon="📊" label="Visualizations" />
          <FeatureBadge icon="☁️" label="Cloud Storage" />
          <FeatureBadge icon="🔐" label="Row-Level Security" />
          <FeatureBadge icon="📓" label="Notebooks" />
        </div>
      </div>

      {/* Right side — Login Card */}
      <div style={{
        position: 'relative', zIndex: 1, width: '100%', maxWidth: 420,
        opacity: mounted ? 1 : 0,
        transform: mounted ? 'translateY(0)' : 'translateY(20px)',
        transition: 'opacity 0.6s ease 0.1s, transform 0.6s ease 0.1s',
      }}>
        <div style={{
          background: 'rgba(15,23,42,0.82)',
          backdropFilter: 'blur(24px)',
          WebkitBackdropFilter: 'blur(24px)',
          border: '1px solid rgba(99,102,241,0.25)',
          borderRadius: 20,
          padding: '40px 36px',
          boxShadow: '0 0 0 1px rgba(255,255,255,0.03), 0 20px 60px rgba(0,0,0,0.5), 0 0 40px rgba(99,102,241,0.08)',
        }}>
          {/* Logo + title */}
          <div style={{ textAlign: 'center', marginBottom: 32 }}>
            <div style={{
              width: 56, height: 56, borderRadius: 16, margin: '0 auto 16px',
              background: 'linear-gradient(135deg, #6366f1 0%, #a855f7 50%, #ec4899 100%)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              boxShadow: '0 8px 24px rgba(99,102,241,0.4)',
            }}>
              <Cpu size={26} color="white" />
            </div>
            <h2 style={{
              fontSize: 22, fontWeight: 700,
              color: 'var(--text-primary)', marginBottom: 6,
            }}>
              Welcome back
            </h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: 13 }}>
              Sign in to your DataWise AI workspace
            </p>
          </div>

          {/* Error alert */}
          {error && (
            <div style={{
              display: 'flex', alignItems: 'center', gap: 10,
              padding: '10px 14px', marginBottom: 20,
              background: 'rgba(239,68,68,0.08)',
              border: '1px solid rgba(239,68,68,0.25)',
              borderRadius: 10,
              color: '#f87171', fontSize: 12,
              animation: 'fadeIn 0.3s ease',
            }}>
              <AlertCircle size={14} style={{ flexShrink: 0 }} />
              <span>{error}</span>
            </div>
          )}

          {/* Social OAuth Logins */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 20 }}>
            {/* Google */}
            <button
              type="button"
              id="login-google-btn"
              disabled={oauthLoading !== null || loading}
              onClick={() => handleOAuth('google')}
              style={{
                display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
                padding: '10px 14px',
                background: 'rgba(30,41,59,0.7)',
                border: '1px solid rgba(148,163,184,0.18)',
                borderRadius: 10,
                color: 'var(--text-primary)',
                fontSize: 12, fontWeight: 600,
                cursor: oauthLoading || loading ? 'not-allowed' : 'pointer',
                transition: 'all 0.2s ease',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = 'rgba(51,65,85,0.85)';
                e.currentTarget.style.borderColor = 'rgba(99,102,241,0.4)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = 'rgba(30,41,59,0.7)';
                e.currentTarget.style.borderColor = 'rgba(148,163,184,0.18)';
              }}
            >
              <svg width="16" height="16" viewBox="0 0 24 24">
                <path fill="#4285F4" d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v4.51h6.6c-.29 1.52-1.14 2.8-2.4 3.65v3h3.86c2.26-2.09 3.685-5.17 3.685-9.09z" />
                <path fill="#34A853" d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.86-3c-1.08.72-2.45 1.16-4.07 1.16-3.13 0-5.78-2.11-6.73-4.96H1.29v3.09C3.26 21.3 7.37 24 12 24z" />
                <path fill="#FBBC05" d="M5.27 14.29c-.25-.72-.38-1.49-.38-2.29s.13-1.57.38-2.29V6.62H1.29C.47 8.24 0 10.06 0 12s.47 3.76 1.29 5.38l3.98-3.09z" />
                <path fill="#EA4335" d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.37 0 3.26 2.7 1.29 6.62l3.98 3.09c.95-2.85 3.6-4.96 6.73-4.96z" />
              </svg>
              <span>{oauthLoading === 'google' ? 'Connecting…' : 'Google'}</span>
            </button>

            {/* GitHub */}
            <button
              type="button"
              id="login-github-btn"
              disabled={oauthLoading !== null || loading}
              onClick={() => handleOAuth('github')}
              style={{
                display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
                padding: '10px 14px',
                background: 'rgba(30,41,59,0.7)',
                border: '1px solid rgba(148,163,184,0.18)',
                borderRadius: 10,
                color: 'var(--text-primary)',
                fontSize: 12, fontWeight: 600,
                cursor: oauthLoading || loading ? 'not-allowed' : 'pointer',
                transition: 'all 0.2s ease',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = 'rgba(51,65,85,0.85)';
                e.currentTarget.style.borderColor = 'rgba(99,102,241,0.4)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = 'rgba(30,41,59,0.7)';
                e.currentTarget.style.borderColor = 'rgba(148,163,184,0.18)';
              }}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                <path fillRule="evenodd" clipRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" />
              </svg>
              <span>{oauthLoading === 'github' ? 'Connecting…' : 'GitHub'}</span>
            </button>
          </div>

          {/* Divider */}
          <div style={{
            display: 'flex', alignItems: 'center', gap: 12,
            marginBottom: 20,
          }}>
            <div style={{ flex: 1, height: 1, background: 'rgba(148,163,184,0.12)' }} />
            <span style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              or continue with email
            </span>
            <div style={{ flex: 1, height: 1, background: 'rgba(148,163,184,0.12)' }} />
          </div>

          <form onSubmit={handleSubmit}>
            {/* Email */}
            <div style={{ marginBottom: 16 }}>
              <label style={{
                display: 'block', marginBottom: 6,
                fontSize: 12, fontWeight: 600,
                color: 'var(--text-secondary)',
              }}>
                Email address
              </label>
              <div style={{ position: 'relative' }}>
                <Mail size={15} style={{
                  position: 'absolute', left: 12, top: '50%',
                  transform: 'translateY(-50%)',
                  color: 'var(--text-muted)',
                  pointerEvents: 'none',
                }} />
                <input
                  id="login-email"
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  style={{
                    width: '100%',
                    padding: '10px 12px 10px 36px',
                    background: 'rgba(30,41,59,0.6)',
                    border: '1px solid rgba(148,163,184,0.12)',
                    borderRadius: 10,
                    color: 'var(--text-primary)',
                    fontSize: 13,
                    outline: 'none',
                    transition: 'border-color 0.2s, box-shadow 0.2s',
                    fontFamily: 'var(--font-sans)',
                  }}
                  onFocus={(e) => {
                    e.target.style.borderColor = 'rgba(99,102,241,0.6)';
                    e.target.style.boxShadow   = '0 0 0 3px rgba(99,102,241,0.12)';
                  }}
                  onBlur={(e) => {
                    e.target.style.borderColor = 'rgba(148,163,184,0.12)';
                    e.target.style.boxShadow   = 'none';
                  }}
                />
              </div>
            </div>

            {/* Password */}
            <div style={{ marginBottom: 24 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                <label style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)' }}>
                  Password
                </label>
                <button
                  type="button"
                  style={{
                    background: 'none', border: 'none', padding: 0, cursor: 'pointer',
                    fontSize: 11, color: 'var(--primary-light)',
                  }}
                  onClick={() => {}}
                >
                  Forgot password?
                </button>
              </div>
              <div style={{ position: 'relative' }}>
                <Lock size={15} style={{
                  position: 'absolute', left: 12, top: '50%',
                  transform: 'translateY(-50%)',
                  color: 'var(--text-muted)', pointerEvents: 'none',
                }} />
                <input
                  id="login-password"
                  type={showPw ? 'text' : 'password'}
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  style={{
                    width: '100%',
                    padding: '10px 40px 10px 36px',
                    background: 'rgba(30,41,59,0.6)',
                    border: '1px solid rgba(148,163,184,0.12)',
                    borderRadius: 10,
                    color: 'var(--text-primary)',
                    fontSize: 13,
                    outline: 'none',
                    transition: 'border-color 0.2s, box-shadow 0.2s',
                    fontFamily: 'var(--font-sans)',
                  }}
                  onFocus={(e) => {
                    e.target.style.borderColor = 'rgba(99,102,241,0.6)';
                    e.target.style.boxShadow   = '0 0 0 3px rgba(99,102,241,0.12)';
                  }}
                  onBlur={(e) => {
                    e.target.style.borderColor = 'rgba(148,163,184,0.12)';
                    e.target.style.boxShadow   = 'none';
                  }}
                />
                <button
                  type="button"
                  onClick={() => setShowPw(!showPw)}
                  style={{
                    position: 'absolute', right: 12, top: '50%',
                    transform: 'translateY(-50%)',
                    background: 'none', border: 'none', padding: 0,
                    cursor: 'pointer', color: 'var(--text-muted)',
                    display: 'flex', alignItems: 'center',
                  }}
                >
                  {showPw ? <EyeOff size={15} /> : <Eye size={15} />}
                </button>
              </div>
            </div>

            {/* Submit */}
            <button
              id="login-submit"
              type="submit"
              disabled={loading}
              style={{
                width: '100%',
                padding: '11px 20px',
                background: loading
                  ? 'rgba(99,102,241,0.4)'
                  : 'linear-gradient(135deg, #6366f1 0%, #a855f7 100%)',
                border: 'none', borderRadius: 10,
                color: '#fff',
                fontSize: 13, fontWeight: 600,
                cursor: loading ? 'not-allowed' : 'pointer',
                display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
                transition: 'opacity 0.2s, transform 0.15s',
                boxShadow: loading ? 'none' : '0 4px 20px rgba(99,102,241,0.35)',
                fontFamily: 'var(--font-sans)',
              }}
              onMouseEnter={(e) => {
                if (!loading) (e.currentTarget as HTMLButtonElement).style.opacity = '0.9';
              }}
              onMouseLeave={(e) => {
                (e.currentTarget as HTMLButtonElement).style.opacity = '1';
              }}
            >
              {loading ? (
                <>
                  <span style={{
                    width: 14, height: 14,
                    border: '2px solid rgba(255,255,255,0.4)',
                    borderTopColor: '#fff',
                    borderRadius: '50%',
                    display: 'inline-block',
                    animation: 'spin 0.7s linear infinite',
                  }} />
                  Authenticating…
                </>
              ) : (
                <>
                  Sign in to Workspace
                  <ArrowRight size={15} />
                </>
              )}
            </button>

            {/* Direct Multi-Project Workspace Demo Access */}
            <button
              id="demo-login-btn"
              type="button"
              onClick={() => {
                signInAsDemo();
                navigate('/projects');
              }}
              style={{
                width: '100%',
                marginTop: 12,
                padding: '10px 20px',
                background: 'rgba(99,102,241,0.12)',
                border: '1px solid rgba(99,102,241,0.3)',
                borderRadius: 10,
                color: 'var(--primary-light, #818cf8)',
                fontSize: 13,
                fontWeight: 600,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 8,
                transition: 'all 0.2s ease',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = 'rgba(99,102,241,0.22)';
                e.currentTarget.style.borderColor = 'rgba(99,102,241,0.5)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = 'rgba(99,102,241,0.12)';
                e.currentTarget.style.borderColor = 'rgba(99,102,241,0.3)';
              }}
            >
              🚀 Explore Multi-Project Workspace Demo
            </button>
          </form>

          {/* Footer */}
          <div style={{
            marginTop: 24, paddingTop: 20,
            borderTop: '1px solid rgba(148,163,184,0.08)',
            textAlign: 'center',
          }}>
            <span style={{ color: 'var(--text-muted)', fontSize: 12 }}>
              Don't have an account?{' '}
            </span>
            <Link to="/register" style={{
              color: 'var(--primary-light)',
              fontSize: 12, fontWeight: 600,
              textDecoration: 'none',
            }}
              onMouseEnter={(e) => (e.currentTarget.style.textDecoration = 'underline')}
              onMouseLeave={(e) => (e.currentTarget.style.textDecoration = 'none')}
            >
              Create account
            </Link>
          </div>
        </div>

        {/* Bottom trust badges */}
        <div style={{
          display: 'flex', justifyContent: 'center', gap: 20, marginTop: 20,
          color: 'var(--text-muted)', fontSize: 11,
        }}>
          <span>🔒 TLS 1.3 encrypted</span>
          <span>🛡️ Row-Level Security</span>
          <span>☁️ Supabase Auth</span>
        </div>
      </div>

      <style>{`
        @keyframes spin  { to { transform: rotate(360deg); } }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(-4px); } to { opacity: 1; transform: translateY(0); } }
        @media (min-width: 900px) {
          .left-brand-panel { display: flex !important; }
        }
        ::placeholder { color: rgba(100,116,139,0.7); }
      `}</style>
    </div>
  );
};
