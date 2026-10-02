import React, { useState } from 'react';
import { 
  User, ShieldCheck, Key, Laptop, Bell, 
  Trash2, RefreshCw, Plus, CheckCircle2, Lock, Smartphone
} from 'lucide-react';
import { useAuthStore } from '../../services/authStore';

export const SettingsView: React.FC = () => {
  const { user } = useAuthStore();
  const [activeTab, setActiveTab] = useState<'profile' | 'security' | 'sessions' | 'api'>('security');

  const [apiKeys, setApiKeys] = useState([
    { id: 'key-01', name: 'CI/CD Pipeline Runner', masked: '••••••••••••4f2b', created: '2026-09-01', lastUsed: '2 hours ago' },
    { id: 'key-02', name: 'Local Jupyter Integration', masked: '••••••••••••9e11', created: '2026-08-14', lastUsed: '5 days ago' }
  ]);

  const [sessions, setSessions] = useState([
    { id: 'sess-curr', device: 'Windows 11 (Desktop App)', ip: '192.168.1.104', location: 'Active Now', current: true },
    { id: 'sess-02', device: 'Chrome on macOS (Web Mode)', ip: '10.0.4.12', location: 'Yesterday', current: false }
  ]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Account & Security Settings</h1>
        <p className="text-sm text-slate-400 mt-1">
          Manage your credentials, multi-factor authentication, active sessions, and enterprise API keys.
        </p>
      </div>

      {/* Navigation Tabs */}
      <div className="flex items-center gap-2 border-b border-border pb-2">
        <button
          onClick={() => setActiveTab('security')}
          className={`px-3 py-1.5 text-xs rounded-lg font-medium transition-colors flex items-center gap-1.5 ${
            activeTab === 'security' ? 'bg-primary text-white' : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <ShieldCheck className="w-3.5 h-3.5" />
          Security & MFA
        </button>
        <button
          onClick={() => setActiveTab('sessions')}
          className={`px-3 py-1.5 text-xs rounded-lg font-medium transition-colors flex items-center gap-1.5 ${
            activeTab === 'sessions' ? 'bg-primary text-white' : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <Laptop className="w-3.5 h-3.5" />
          Active Sessions
        </button>
        <button
          onClick={() => setActiveTab('api')}
          className={`px-3 py-1.5 text-xs rounded-lg font-medium transition-colors flex items-center gap-1.5 ${
            activeTab === 'api' ? 'bg-primary text-white' : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <Key className="w-3.5 h-3.5" />
          API Keys
        </button>
        <button
          onClick={() => setActiveTab('profile')}
          className={`px-3 py-1.5 text-xs rounded-lg font-medium transition-colors flex items-center gap-1.5 ${
            activeTab === 'profile' ? 'bg-primary text-white' : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <User className="w-3.5 h-3.5" />
          Profile
        </button>
      </div>

      {/* Security Tab Content */}
      {activeTab === 'security' && (
        <div className="space-y-6 max-w-3xl">
          {/* MFA Panel */}
          <div className="panel p-5 space-y-4">
            <div className="flex items-start justify-between">
              <div>
                <h3 className="font-bold text-slate-100 text-sm flex items-center gap-2">
                  <Smartphone className="w-4 h-4 text-emerald-400" />
                  Two-Factor Authentication (TOTP / Authenticator)
                </h3>
                <p className="text-xs text-slate-400 mt-1">
                  Enforce strong cryptographic verification for all interactive sign-ins and sensitive model promotions.
                </p>
              </div>
              <span className="badge badge-success text-xs">Enabled</span>
            </div>

            <div className="p-3 rounded-lg bg-surface-elevated/40 border border-border flex items-center justify-between text-xs">
              <span className="text-slate-300">Authenticator App (Google Authenticator / 1Password)</span>
              <button 
                onClick={() => alert('Rotating MFA key...')}
                className="btn btn-secondary text-xs"
              >
                Reconfigure TOTP
              </button>
            </div>
          </div>

          {/* Password Change */}
          <div className="panel p-5 space-y-4">
            <h3 className="font-bold text-slate-100 text-sm flex items-center gap-2">
              <Lock className="w-4 h-4 text-primary-light" />
              Update Master Password
            </h3>
            <div className="space-y-3">
              <div>
                <label className="text-xs text-slate-400 block mb-1">Current Password</label>
                <input type="password" placeholder="••••••••••••" className="input text-xs w-full max-w-md" />
              </div>
              <div>
                <label className="text-xs text-slate-400 block mb-1">New Password (Min 14 chars, OWASP ASVS compliant)</label>
                <input type="password" placeholder="••••••••••••" className="input text-xs w-full max-w-md" />
              </div>
              <button 
                onClick={() => alert('Password updated successfully')}
                className="btn btn-primary text-xs"
              >
                Update Password
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Sessions Tab Content */}
      {activeTab === 'sessions' && (
        <div className="space-y-4 max-w-3xl">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400">
              Manage cryptographic session tokens across your devices.
            </span>
            <button 
              onClick={() => {
                alert('All secondary sessions revoked.');
                setSessions(prev => prev.filter(s => s.current));
              }}
              className="btn btn-secondary text-xs text-rose-400 hover:text-rose-300"
            >
              Revoke All Other Sessions
            </button>
          </div>

          <div className="space-y-3">
            {sessions.map((s) => (
              <div key={s.id} className="panel p-4 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Laptop className="w-5 h-5 text-slate-400" />
                  <div>
                    <div className="font-semibold text-xs text-slate-200 flex items-center gap-2">
                      {s.device}
                      {s.current && <span className="badge badge-success text-[10px]">Current Session</span>}
                    </div>
                    <div className="text-[11px] text-slate-500 font-mono mt-0.5">
                      IP: {s.ip} • Last Active: {s.location}
                    </div>
                  </div>
                </div>

                {!s.current && (
                  <button 
                    onClick={() => setSessions(prev => prev.filter(x => x.id !== s.id))}
                    className="btn btn-secondary text-xs text-rose-400"
                  >
                    Revoke
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* API Keys Tab Content */}
      {activeTab === 'api' && (
        <div className="space-y-4 max-w-3xl">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400">
              Personal access tokens for backend API automation and SDKs.
            </span>
            <button 
              onClick={() => {
                const name = prompt('Enter key description:');
                if (name) {
                  setApiKeys(prev => [
                    { id: `key-${Date.now()}`, name, masked: '••••••••••••a8f1', created: 'Just now', lastUsed: 'Never' },
                    ...prev
                  ]);
                }
              }}
              className="btn btn-primary text-xs flex items-center gap-1.5"
            >
              <Plus className="w-3.5 h-3.5" />
              Generate New Token
            </button>
          </div>

          <div className="space-y-3">
            {apiKeys.map((k) => (
              <div key={k.id} className="panel p-4 flex items-center justify-between">
                <div>
                  <h4 className="font-semibold text-xs text-slate-200">{k.name}</h4>
                  <div className="font-mono text-xs text-slate-400 mt-1">{k.masked}</div>
                  <div className="text-[11px] text-slate-500 mt-1">
                    Created: {k.created} • Last used: {k.lastUsed}
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <button 
                    onClick={() => alert(`Token ${k.name} rotated. New secret generated.`)}
                    className="btn btn-secondary text-xs"
                  >
                    Rotate
                  </button>
                  <button 
                    onClick={() => setApiKeys(prev => prev.filter(x => x.id !== k.id))}
                    className="btn btn-secondary text-xs text-rose-400"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Profile Tab Content */}
      {activeTab === 'profile' && (
        <div className="panel p-5 max-w-2xl space-y-4">
          <h3 className="font-bold text-slate-100 text-sm">User Profile Information</h3>
          <div className="space-y-3 text-xs">
            <div>
              <label className="text-slate-400 block mb-1">Full Name</label>
              <input type="text" defaultValue={user?.name || 'Lead Data Scientist'} className="input w-full" />
            </div>
            <div>
              <label className="text-slate-400 block mb-1">Email Address</label>
              <input type="email" disabled defaultValue={user?.email || 'scientist@datalab.internal'} className="input w-full opacity-60 cursor-not-allowed" />
            </div>
            <div>
              <label className="text-slate-400 block mb-1">Assigned Role</label>
              <input type="text" disabled defaultValue="OWNER / ADMIN" className="input w-full opacity-60 cursor-not-allowed font-mono" />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
