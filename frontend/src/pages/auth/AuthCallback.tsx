/**
 * DataWise AI — OAuth Callback Handler
 * Receives redirect from backend Google/GitHub OAuth,
 * extracts token & user profile, commits session to authStore,
 * and seamlessly redirects to dashboard or requested page.
 */

import React, { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Cpu, AlertCircle, CheckCircle } from 'lucide-react';
import { authStore } from '../../services/authStore';

export const AuthCallback: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const token = params.get('token');
    const name = params.get('name');
    const email = params.get('email');
    const error = params.get('error');

    if (error) {
      navigate(`/login?error=${encodeURIComponent(error)}`, { replace: true });
      return;
    }

    if (!token) {
      setErrorMessage('No authentication token received from OAuth identity provider.');
      setTimeout(() => {
        navigate('/login?error=oauth_token_missing', { replace: true });
      }, 2500);
      return;
    }

    const decodedEmail = decodeURIComponent(email || '');
    const decodedName = decodeURIComponent(name || decodedEmail.split('@')[0] || 'User');

    // Commit to authStore
    authStore.login(
      {
        id: '',
        email: decodedEmail,
        name: decodedName,
        role: 'data_scientist',
        mfa_enabled: false,
        created_at: new Date().toISOString(),
      },
      token
    );

    // Clean URL query parameters and redirect to /projects
    window.history.replaceState({}, document.title, window.location.pathname);
    setTimeout(() => {
      navigate('/projects', { replace: true });
    }, 400);
  }, [location, navigate]);

  return (
    <div
      style={{
        minHeight: '100vh',
        background: 'var(--bg-primary)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontFamily: 'var(--font-sans)',
        padding: 24,
      }}
    >
      <div
        style={{
          background: 'rgba(15,23,42,0.85)',
          backdropFilter: 'blur(24px)',
          border: '1px solid rgba(99,102,241,0.25)',
          borderRadius: 20,
          padding: '48px 36px',
          maxWidth: 420,
          width: '100%',
          textAlign: 'center',
          boxShadow: '0 20px 60px rgba(0,0,0,0.5), 0 0 40px rgba(99,102,241,0.1)',
        }}
      >
        {errorMessage ? (
          <>
            <div
              style={{
                width: 56,
                height: 56,
                borderRadius: 16,
                margin: '0 auto 16px',
                background: 'rgba(239,68,68,0.15)',
                border: '1px solid rgba(239,68,68,0.3)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <AlertCircle size={28} color="#f87171" />
            </div>
            <h2 style={{ fontSize: 18, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 8 }}>
              Authentication Failed
            </h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: 13, lineHeight: 1.6, marginBottom: 16 }}>
              {errorMessage}
            </p>
            <p style={{ color: 'var(--text-muted)', fontSize: 12 }}>Redirecting back to login...</p>
          </>
        ) : (
          <>
            <div
              style={{
                width: 56,
                height: 56,
                borderRadius: 16,
                margin: '0 auto 16px',
                background: 'linear-gradient(135deg, #6366f1 0%, #a855f7 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 8px 24px rgba(99,102,241,0.4)',
              }}
            >
              <Cpu size={28} color="white" />
            </div>
            <h2 style={{ fontSize: 20, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 8 }}>
              Completing Secure Sign-in
            </h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: 13, lineHeight: 1.6, marginBottom: 24 }}>
              Verifying credentials and restoring your DataWise AI workspace...
            </p>
            <div
              style={{
                width: 32,
                height: 32,
                border: '2px solid var(--primary)',
                borderTopColor: 'transparent',
                borderRadius: '50%',
                margin: '0 auto',
                animation: 'spin 0.8s linear infinite',
              }}
            />
            <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
          </>
        )}
      </div>
    </div>
  );
};
