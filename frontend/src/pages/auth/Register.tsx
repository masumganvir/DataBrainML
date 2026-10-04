import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Lock, Mail, User, Building, ArrowRight, ShieldCheck, AlertCircle } from 'lucide-react';
import { useAuthStore } from '../../services/authStore';
import { BRANDING } from '../../config/branding';
import { authApi } from '../../services/api';

export const Register: React.FC = () => {
  const navigate = useNavigate();
  const { login } = useAuthStore();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [org, setOrg] = useState('');
  const [password, setPassword] = useState('');
  const [errorMsg, setErrorMsg] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setErrorMsg('');

    try {
      const res = await authApi.register({
        email,
        password,
        name: name || 'Data Scientist',
        role: 'data_scientist',
      });
      login(
        {
          id: res.user.id,
          email: res.user.email,
          name: res.user.name || name || 'Data Scientist',
          role: res.user.role || 'data_scientist',
          organization_id: org ? `org-${org.toLowerCase().replace(/\s+/g, '-')}` : 'org-default',
          organization_name: org || 'Personal Workspace',
          mfa_enabled: false,
          created_at: new Date().toISOString(),
        },
        res.access_token
      );
      navigate('/app/dashboard');
    } catch (err: any) {
      setErrorMsg(err.message || 'Registration failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4 relative overflow-hidden">
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[500px] h-[500px] bg-primary/10 rounded-full blur-3xl pointer-events-none" />

      <div className="panel max-w-md w-full p-8 relative z-10 space-y-6 shadow-2xl border-slate-700/80">
        <div className="text-center space-y-2">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-primary to-accent flex items-center justify-center font-bold text-white text-xl mx-auto shadow-lg shadow-primary/20">
            {BRANDING.shortName}
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-100">Create an Account</h1>
          <p className="text-xs text-slate-400">Join your enterprise AI workspace</p>
        </div>

        {errorMsg && (
          <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-3.5">
          <div>
            <label className="text-xs font-semibold text-slate-300 block mb-1">Full Name</label>
            <div className="relative">
              <User className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
              <input
                type="text"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Dr. Jane Doe"
                className="input pl-9 text-xs w-full py-2 bg-surface-elevated text-slate-200"
              />
            </div>
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-300 block mb-1">Organization / Team</label>
            <div className="relative">
              <Building className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
              <input
                type="text"
                required
                value={org}
                onChange={(e) => setOrg(e.target.value)}
                placeholder="Acme Financial Research"
                className="input pl-9 text-xs w-full py-2 bg-surface-elevated text-slate-200"
              />
            </div>
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-300 block mb-1">Work Email</label>
            <div className="relative">
              <Mail className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="jane.doe@acme.internal"
                className="input pl-9 text-xs w-full py-2 bg-surface-elevated text-slate-200"
              />
            </div>
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-300 block mb-1">Password</label>
            <div className="relative">
              <Lock className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
              <input
                type="password"
                required
                minLength={12}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="At least 12 characters..."
                className="input pl-9 text-xs w-full py-2 bg-surface-elevated text-slate-200"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="btn btn-primary w-full text-xs py-2.5 flex items-center justify-center gap-2 font-semibold shadow-lg shadow-primary/20 mt-2"
          >
            {isLoading ? 'Creating Account...' : 'Register & Enter Workspace'}
            <ArrowRight className="w-4 h-4" />
          </button>
        </form>

        <div className="pt-4 border-t border-border/80 flex items-center justify-between text-xs text-slate-400">
          <span className="flex items-center gap-1 text-[11px]">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            Tenant Isolation Enabled
          </span>
          <Link to="/login" className="text-primary-light hover:underline text-[11px]">
            Already have an account?
          </Link>
        </div>
      </div>
    </div>
  );
};
