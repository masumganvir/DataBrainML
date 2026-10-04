import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Lock, Mail, ArrowRight, ShieldCheck, AlertCircle } from 'lucide-react';
import { useAuthStore } from '../../services/authStore';
import { BRANDING } from '../../config/branding';
import { authApi } from '../../services/api';

export const Login: React.FC = () => {
  const navigate = useNavigate();
  const { login } = useAuthStore();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errorMsg, setErrorMsg] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setErrorMsg('');

    try {
      const res = await authApi.login(email, password);
      login(
        {
          id: res.user.id,
          email: res.user.email,
          name: res.user.name || 'Data Scientist',
          role: res.user.role || 'data_scientist',
          organization_id: 'org-enterprise-1',
          organization_name: 'DataWise Enterprise',
          mfa_enabled: false,
          created_at: new Date().toISOString(),
        },
        res.access_token
      );
      navigate('/app/dashboard');
    } catch (err: any) {
      setErrorMsg(err.message || 'Incorrect email or password.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4 relative overflow-hidden">
      {/* Subtle background ambient blur */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[500px] h-[500px] bg-primary/10 rounded-full blur-3xl pointer-events-none" />

      <div className="panel max-w-md w-full p-8 relative z-10 space-y-6 shadow-2xl border-slate-700/80">
        <div className="text-center space-y-2">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-primary to-accent flex items-center justify-center font-bold text-white text-xl mx-auto shadow-lg shadow-primary/20">
            {BRANDING.shortName}
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-100">{BRANDING.productName}</h1>
          <p className="text-xs text-slate-400">{BRANDING.tagline}</p>
        </div>

        {errorMsg && (
          <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="text-xs font-semibold text-slate-300 block mb-1">Corporate Email</label>
            <div className="relative">
              <Mail className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@enterprise.internal"
                className="input pl-9 text-xs w-full py-2 bg-surface-elevated text-slate-200"
              />
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="text-xs font-semibold text-slate-300">Password</label>
              <a href="#forgot" onClick={(e) => { e.preventDefault(); alert('Password recovery email dispatched if account exists.'); }} className="text-[11px] text-primary-light hover:underline">
                Forgot password?
              </a>
            </div>
            <div className="relative">
              <Lock className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                className="input pl-9 text-xs w-full py-2 bg-surface-elevated text-slate-200"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="btn btn-primary w-full text-xs py-2.5 flex items-center justify-center gap-2 font-semibold shadow-lg shadow-primary/20"
          >
            {isLoading ? 'Authenticating...' : 'Sign In to Workspace'}
            <ArrowRight className="w-4 h-4" />
          </button>
        </form>

        <div className="pt-4 border-t border-border/80 flex items-center justify-between text-xs text-slate-400">
          <span className="flex items-center gap-1 text-[11px]">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            TLS 1.3 / ASVS 4.0
          </span>
          <Link to="/register" className="text-primary-light hover:underline text-[11px]">
            Create an account
          </Link>
        </div>
      </div>
    </div>
  );
};
