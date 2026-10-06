/**
 * DataWise AI — Register Page (Supabase Auth)
 * Matches Login aesthetic with full name + email + password fields.
 */

import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Mail, Lock, User, ArrowRight, AlertCircle, Eye, EyeOff, Cpu, CheckCircle } from 'lucide-react';
import { useAuthStore } from '../../services/authStore';

export const Register: React.FC = () => {
  const navigate = useNavigate();
  const { signUp, signInWithOAuth, isAuthenticated } = useAuthStore();

  const [name,     setName]     = useState('');
  const [email,    setEmail]    = useState('');
  const [password, setPassword] = useState('');
  const [confirm,  setConfirm]  = useState('');
  const [showPw,   setShowPw]   = useState(false);
  const [error,    setError]    = useState('');
  const [success,  setSuccess]  = useState(false);
  const [loading,  setLoading]  = useState(false);
  const [oauthLoading, setOauthLoading] = useState<'google' | 'github' | null>(null);
  const [mounted,  setMounted]  = useState(false);

  useEffect(() => { setTimeout(() => setMounted(true), 50); }, []);
  useEffect(() => {
    if (isAuthenticated) navigate('/projects', { replace: true });
  }, [isAuthenticated, navigate]);

  const passwordStrength = (): { label: string; color: string; width: string } => {
    if (password.length === 0) return { label: '', color: 'transparent', width: '0%' };
    if (password.length < 6)   return { label: 'Too short', color: '#ef4444', width: '20%' };
    if (password.length < 8)   return { label: 'Weak', color: '#f59e0b', width: '40%' };
    const hasUpper   = /[A-Z]/.test(password);
    const hasSpecial = /[^a-zA-Z0-9]/.test(password);
    if (hasUpper && hasSpecial) return { label: 'Strong', color: '#10b981', width: '100%' };
    if (hasUpper || hasSpecial) return { label: 'Good', color: '#6366f1', width: '70%' };
    return { label: 'Fair', color: '#f59e0b', width: '50%' };
  };

  const strength = passwordStrength();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (password !== confirm) { setError('Passwords do not match.'); return; }
    if (password.length < 6)  { setError('Password must be at least 6 characters.'); return; }
    setLoading(true);
    setError('');
    try {
      await signUp(email, password, name);
      // If no CHECK_EMAIL error, user is signed in automatically
    } catch (err: any) {
      if (err.message === 'CHECK_EMAIL') {
        setSuccess(true);
      } else {
        setError(err.message || 'Registration failed. Please try again.');
      }
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
      setError(err.message || `Failed to sign up with ${provider}`);
      setOauthLoading(null);
    }
  };

  const inputStyle: React.CSSProperties = {
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
  };

  const focusHandler = (e: React.FocusEvent<HTMLInputElement>) => {
    e.target.style.borderColor = 'rgba(99,102,241,0.6)';
    e.target.style.boxShadow   = '0 0 0 3px rgba(99,102,241,0.12)';
  };
  const blurHandler = (e: React.FocusEvent<HTMLInputElement>) => {
    e.target.style.borderColor = 'rgba(148,163,184,0.12)';
    e.target.style.boxShadow   = 'none';
  };

  if (success) {
    return (
      <div style={{
        minHeight: '100vh',
        background: 'var(--bg-primary)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        padding: 24, fontFamily: 'var(--font-sans)',
      }}>
        <div style={{
          textAlign: 'center',
          background: 'rgba(15,23,42,0.82)',
          backdropFilter: 'blur(24px)',
          border: '1px solid rgba(16,185,129,0.25)',
          borderRadius: 20, padding: '48px 36px', maxWidth: 400,
          boxShadow: '0 0 40px rgba(16,185,129,0.08)',
        }}>
          <div style={{
            width: 64, height: 64, borderRadius: 20, margin: '0 auto 20px',
            background: 'linear-gradient(135deg, #059669 0%, #10b981 100%)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            boxShadow: '0 8px 24px rgba(16,185,129,0.3)',
          }}>
            <CheckCircle size={30} color="white" />
          </div>
          <h2 style={{ fontSize: 22, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 12 }}>
            Check your email
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: 13, lineHeight: 1.7, marginBottom: 24 }}>
            We sent a confirmation link to <strong style={{ color: 'var(--text-primary)' }}>{email}</strong>.
            Click it to activate your DataWise AI account.
          </p>
          <Link to="/login" style={{
            display: 'inline-flex', alignItems: 'center', gap: 8,
            padding: '10px 24px',
            background: 'linear-gradient(135deg, #6366f1 0%, #a855f7 100%)',
            borderRadius: 10, color: '#fff',
            fontSize: 13, fontWeight: 600, textDecoration: 'none',
            boxShadow: '0 4px 20px rgba(99,102,241,0.35)',
          }}>
            Back to Sign In <ArrowRight size={14} />
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div style={{
      minHeight: '100vh',
      background: 'var(--bg-primary)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      padding: 24, position: 'relative', overflow: 'hidden',
      fontFamily: 'var(--font-sans)',
    }}>
      {/* Ambient glows */}
      <div style={{
        position: 'absolute', top: '20%', right: '20%',
        width: 500, height: 500,
        background: 'radial-gradient(circle, rgba(168,85,247,0.12) 0%, transparent 70%)',
        borderRadius: '50%', pointerEvents: 'none', zIndex: 0,
      }} />

      {/* Card */}
      <div style={{
        position: 'relative', zIndex: 1, width: '100%', maxWidth: 420,
        opacity: mounted ? 1 : 0,
        transform: mounted ? 'translateY(0)' : 'translateY(20px)',
        transition: 'opacity 0.6s ease, transform 0.6s ease',
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
          {/* Header */}
          <div style={{ textAlign: 'center', marginBottom: 28 }}>
            <div style={{
              width: 56, height: 56, borderRadius: 16, margin: '0 auto 16px',
              background: 'linear-gradient(135deg, #6366f1 0%, #a855f7 50%, #ec4899 100%)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              boxShadow: '0 8px 24px rgba(99,102,241,0.4)',
            }}>
              <Cpu size={26} color="white" />
            </div>
            <h2 style={{ fontSize: 22, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 6 }}>
              Create your account
            </h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: 13 }}>
              Start building ML pipelines with DataWise AI
            </p>
          </div>

          {/* Error */}
          {error && (
            <div style={{
              display: 'flex', alignItems: 'center', gap: 10,
              padding: '10px 14px', marginBottom: 20,
              background: 'rgba(239,68,68,0.08)',
              border: '1px solid rgba(239,68,68,0.25)',
              borderRadius: 10, color: '#f87171', fontSize: 12,
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
              id="reg-google-btn"
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
              id="reg-github-btn"
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
              or register with email
            </span>
            <div style={{ flex: 1, height: 1, background: 'rgba(148,163,184,0.12)' }} />
          </div>

          <form onSubmit={handleSubmit}>
            {/* Name */}
            <div style={{ marginBottom: 14 }}>
              <label style={{ display: 'block', marginBottom: 6, fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)' }}>
                Full name
              </label>
              <div style={{ position: 'relative' }}>
                <User size={15} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)', pointerEvents: 'none' }} />
                <input id="reg-name" type="text" required value={name} onChange={(e) => setName(e.target.value)}
                  placeholder="Dr. Jane Smith" style={inputStyle} onFocus={focusHandler} onBlur={blurHandler} />
              </div>
            </div>

            {/* Email */}
            <div style={{ marginBottom: 14 }}>
              <label style={{ display: 'block', marginBottom: 6, fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)' }}>
                Email address
              </label>
              <div style={{ position: 'relative' }}>
                <Mail size={15} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)', pointerEvents: 'none' }} />
                <input id="reg-email" type="email" required value={email} onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com" style={inputStyle} onFocus={focusHandler} onBlur={blurHandler} />
              </div>
            </div>

            {/* Password */}
            <div style={{ marginBottom: 14 }}>
              <label style={{ display: 'block', marginBottom: 6, fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)' }}>
                Password
              </label>
              <div style={{ position: 'relative' }}>
                <Lock size={15} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)', pointerEvents: 'none' }} />
                <input id="reg-password" type={showPw ? 'text' : 'password'} required value={password}
                  onChange={(e) => setPassword(e.target.value)} placeholder="Min. 6 characters"
                  style={{ ...inputStyle, paddingRight: 40 }} onFocus={focusHandler} onBlur={blurHandler} />
                <button type="button" onClick={() => setShowPw(!showPw)} style={{
                  position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)',
                  background: 'none', border: 'none', padding: 0, cursor: 'pointer', color: 'var(--text-muted)',
                  display: 'flex', alignItems: 'center',
                }}>
                  {showPw ? <EyeOff size={15} /> : <Eye size={15} />}
                </button>
              </div>
              {/* Password strength bar */}
              {password && (
                <div style={{ marginTop: 8 }}>
                  <div style={{ height: 3, background: 'rgba(148,163,184,0.1)', borderRadius: 3, overflow: 'hidden' }}>
                    <div style={{
                      height: '100%', width: strength.width,
                      background: strength.color, borderRadius: 3,
                      transition: 'width 0.3s ease, background 0.3s ease',
                    }} />
                  </div>
                  <span style={{ fontSize: 10, color: strength.color, marginTop: 4, display: 'block' }}>{strength.label}</span>
                </div>
              )}
            </div>

            {/* Confirm password */}
            <div style={{ marginBottom: 24 }}>
              <label style={{ display: 'block', marginBottom: 6, fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)' }}>
                Confirm password
              </label>
              <div style={{ position: 'relative' }}>
                <Lock size={15} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)', pointerEvents: 'none' }} />
                <input id="reg-confirm" type={showPw ? 'text' : 'password'} required value={confirm}
                  onChange={(e) => setConfirm(e.target.value)} placeholder="Re-enter password"
                  style={{
                    ...inputStyle,
                    borderColor: confirm && password !== confirm ? 'rgba(239,68,68,0.4)' : undefined,
                  }}
                  onFocus={focusHandler} onBlur={blurHandler} />
              </div>
              {confirm && password !== confirm && (
                <span style={{ fontSize: 11, color: '#f87171', marginTop: 4, display: 'block' }}>Passwords don't match</span>
              )}
            </div>

            <button id="reg-submit" type="submit" disabled={loading} style={{
              width: '100%',
              padding: '11px 20px',
              background: loading ? 'rgba(99,102,241,0.4)' : 'linear-gradient(135deg, #6366f1 0%, #a855f7 100%)',
              border: 'none', borderRadius: 10, color: '#fff',
              fontSize: 13, fontWeight: 600,
              cursor: loading ? 'not-allowed' : 'pointer',
              display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
              boxShadow: loading ? 'none' : '0 4px 20px rgba(99,102,241,0.35)',
              fontFamily: 'var(--font-sans)',
              transition: 'opacity 0.2s',
            }}>
              {loading ? (
                <>
                  <span style={{
                    width: 14, height: 14,
                    border: '2px solid rgba(255,255,255,0.4)', borderTopColor: '#fff',
                    borderRadius: '50%', display: 'inline-block',
                    animation: 'spin 0.7s linear infinite',
                  }} />
                  Creating account…
                </>
              ) : (
                <>Create Account <ArrowRight size={15} /></>
              )}
            </button>
          </form>

          <div style={{
            marginTop: 24, paddingTop: 20,
            borderTop: '1px solid rgba(148,163,184,0.08)',
            textAlign: 'center',
          }}>
            <span style={{ color: 'var(--text-muted)', fontSize: 12 }}>Already have an account? </span>
            <Link to="/login" style={{ color: 'var(--primary-light)', fontSize: 12, fontWeight: 600, textDecoration: 'none' }}
              onMouseEnter={(e) => (e.currentTarget.style.textDecoration = 'underline')}
              onMouseLeave={(e) => (e.currentTarget.style.textDecoration = 'none')}>
              Sign in
            </Link>
          </div>
        </div>

        <div style={{ display: 'flex', justifyContent: 'center', gap: 20, marginTop: 20, color: 'var(--text-muted)', fontSize: 11 }}>
          <span>🔒 TLS 1.3 encrypted</span>
          <span>🛡️ GDPR compliant</span>
          <span>☁️ Supabase Auth</span>
        </div>
      </div>

      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
        ::placeholder { color: rgba(100,116,139,0.7); }
      `}</style>
    </div>
  );
};
