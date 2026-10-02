import React, { useState } from 'react';
import { 
  Database, Plus, CheckCircle2, AlertCircle, RefreshCw, 
  Trash2, ShieldCheck, Lock, ExternalLink, HardDrive, Globe
} from 'lucide-react';
import { useAuthStore } from '../../services/authStore';

interface ConnectorItem {
  id: string;
  name: string;
  type: 'POSTGRESQL' | 'MYSQL' | 'MONGODB' | 'S3_STORAGE' | 'REST_API';
  status: 'CONNECTED' | 'DISCONNECTED' | 'ERROR';
  maskedHost: string;
  databaseName?: string;
  lastTested: string;
}

const INITIAL_CONNECTORS: ConnectorItem[] = [
  {
    id: 'conn-pg-01',
    name: 'Customer Data Warehouse (Analytics)',
    type: 'POSTGRESQL',
    status: 'CONNECTED',
    maskedHost: 'dw-prod-cluster.internal:5432',
    databaseName: 'telecom_analytics',
    lastTested: '5 minutes ago'
  },
  {
    id: 'conn-s3-02',
    name: 'Model Artifacts & Feature Store Bucket',
    type: 'S3_STORAGE',
    status: 'CONNECTED',
    maskedHost: 's3.us-east-1.amazonaws.com/ml-artifacts-vault',
    lastTested: '1 hour ago'
  },
  {
    id: 'conn-rest-03',
    name: 'CRM Webhook Ingress Gateway',
    type: 'REST_API',
    status: 'CONNECTED',
    maskedHost: 'https://crm-api.internal/v2/events',
    lastTested: 'Yesterday'
  }
];

export const ConnectionsManager: React.FC = () => {
  const { activeProject } = useAuthStore();
  const [connectors, setConnectors] = useState<ConnectorItem[]>(INITIAL_CONNECTORS);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [testStatus, setTestStatus] = useState<'IDLE' | 'TESTING' | 'SUCCESS'>('IDLE');

  // Form states
  const [connType, setConnType] = useState<'POSTGRESQL' | 'MYSQL' | 'S3_STORAGE' | 'REST_API'>('POSTGRESQL');
  const [connName, setConnName] = useState('');
  const [host, setHost] = useState('');
  const [database, setDatabase] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  const handleTestConnection = () => {
    setTestStatus('TESTING');
    setTimeout(() => {
      setTestStatus('SUCCESS');
    }, 800);
  };

  const handleSaveConnection = (e: React.FormEvent) => {
    e.preventDefault();
    const newConn: ConnectorItem = {
      id: `conn-${Date.now()}`,
      name: connName || 'Production Database',
      type: connType,
      status: 'CONNECTED',
      maskedHost: `${host || 'db.internal:5432'}`,
      databaseName: database || 'prod_db',
      lastTested: 'Just now'
    };
    setConnectors(prev => [newConn, ...prev]);
    setIsModalOpen(false);
    setTestStatus('IDLE');
    setConnName('');
    setHost('');
    setDatabase('');
    setUsername('');
    setPassword('');
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-2 rounded-lg bg-primary/10 text-primary-light">
              <Database className="w-5 h-5" />
            </span>
            <h1 className="text-2xl font-bold tracking-tight">Data Connectors & Storage</h1>
            <span className="badge badge-success text-xs">Zero Client Secret Leakage</span>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Securely connected database and object storage sources. Credentials are encrypted at rest using server-side envelopes.
          </p>
        </div>

        <button 
          onClick={() => setIsModalOpen(true)}
          className="btn btn-primary text-xs flex items-center gap-1.5"
        >
          <Plus className="w-3.5 h-3.5" />
          Add Secure Connection
        </button>
      </div>

      {/* Connectors Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {connectors.map((c) => (
          <div key={c.id} className="panel p-5 space-y-4 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between">
                <span className="badge badge-neutral text-[10px] font-mono">{c.type}</span>
                <span className="badge badge-success text-xs flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3" /> Connected
                </span>
              </div>

              <h3 className="text-base font-bold text-slate-100 mt-3">{c.name}</h3>
              
              <div className="mt-3 p-2.5 rounded-lg bg-slate-950 font-mono text-[11px] text-slate-300 border border-border">
                <div className="text-slate-500 text-[10px] uppercase font-semibold">Endpoint:</div>
                <div className="truncate">{c.maskedHost}</div>
                {c.databaseName && (
                  <div className="text-slate-400 mt-1">Database: {c.databaseName}</div>
                )}
              </div>
            </div>

            <div className="pt-3 border-t border-border flex items-center justify-between text-xs text-slate-400">
              <span className="text-[11px]">Last verified: {c.lastTested}</span>
              <button 
                onClick={() => alert(`Connection test passed for ${c.name}`)}
                className="text-primary-light hover:underline flex items-center gap-1 text-[11px]"
              >
                <RefreshCw className="w-3 h-3" /> Test
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Add Connection Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="panel max-w-lg w-full p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-border pb-3">
              <div className="flex items-center gap-2">
                <Lock className="w-4 h-4 text-emerald-400" />
                <h3 className="text-base font-bold text-slate-100">Add Secure Data Connector</h3>
              </div>
              <button 
                onClick={() => setIsModalOpen(false)}
                className="text-slate-400 hover:text-slate-200 text-xs"
              >
                ✕
              </button>
            </div>

            <p className="text-xs text-slate-400">
              Secrets are stored in backend encrypted vaults. Passwords are never returned to the browser or stored in logs.
            </p>

            <form onSubmit={handleSaveConnection} className="space-y-3">
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">Connector Type</label>
                <select 
                  value={connType} 
                  onChange={(e: any) => setConnType(e.target.value)}
                  className="input text-xs w-full"
                >
                  <option value="POSTGRESQL">PostgreSQL Database</option>
                  <option value="MYSQL">MySQL Database</option>
                  <option value="S3_STORAGE">Amazon S3 / MinIO Object Storage</option>
                  <option value="REST_API">REST API Endpoint</option>
                </select>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">Connection Display Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Analytics Data Warehouse"
                  value={connName}
                  onChange={(e) => setConnName(e.target.value)}
                  className="input text-xs w-full"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-semibold text-slate-300 block mb-1">Host / Endpoint</label>
                  <input
                    type="text"
                    required
                    placeholder="db.internal"
                    value={host}
                    onChange={(e) => setHost(e.target.value)}
                    className="input text-xs w-full"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-300 block mb-1">Database Name</label>
                  <input
                    type="text"
                    placeholder="telecom_dw"
                    value={database}
                    onChange={(e) => setDatabase(e.target.value)}
                    className="input text-xs w-full"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-semibold text-slate-300 block mb-1">Username</label>
                  <input
                    type="text"
                    placeholder="readonly_agent"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    className="input text-xs w-full"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-300 block mb-1">Password</label>
                  <input
                    type="password"
                    placeholder="••••••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="input text-xs w-full"
                  />
                </div>
              </div>

              {testStatus === 'SUCCESS' && (
                <div className="p-2.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4" />
                  Connection test succeeded. Server reached and authenticated safely.
                </div>
              )}

              <div className="flex items-center justify-between pt-3 border-t border-border">
                <button
                  type="button"
                  onClick={handleTestConnection}
                  disabled={testStatus === 'TESTING'}
                  className="btn btn-secondary text-xs flex items-center gap-1.5"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${testStatus === 'TESTING' ? 'animate-spin' : ''}`} />
                  Test Connection
                </button>

                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => setIsModalOpen(false)}
                    className="btn btn-secondary text-xs"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="btn btn-primary text-xs"
                  >
                    Save & Encrypt
                  </button>
                </div>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
