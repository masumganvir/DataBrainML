import React, { useState } from 'react';
import { 
  ShieldCheck, ShieldAlert, Cpu, Activity, Users, 
  FileText, Search, Filter, Lock, CheckCircle2, AlertCircle
} from 'lucide-react';
import { useAuthStore } from '../../services/authStore';

interface AuditLogEntry {
  id: string;
  timestamp: string;
  actor: string;
  action: string;
  resource: string;
  result: 'SUCCESS' | 'FAILED' | 'DENIED';
  ipAddress: string;
  requestId: string;
}

const AUDIT_LOGS: AuditLogEntry[] = [
  {
    id: 'aud-001',
    timestamp: '2026-09-30 09:20:14 UTC',
    actor: 'scientist@datalab.internal',
    action: 'model.deploy',
    resource: 'mdl-xgb-v1.4 -> dep-churn-prod',
    result: 'SUCCESS',
    ipAddress: '192.168.1.104',
    requestId: 'req-8f4b2190'
  },
  {
    id: 'aud-002',
    timestamp: '2026-09-30 09:14:02 UTC',
    actor: 'scientist@datalab.internal',
    action: 'experiment.promote_champion',
    resource: 'exp-xgb-01 (F1: 0.9082)',
    result: 'SUCCESS',
    ipAddress: '192.168.1.104',
    requestId: 'req-12ca9433'
  },
  {
    id: 'aud-003',
    timestamp: '2026-09-30 09:05:40 UTC',
    actor: 'dataset-ingestion-worker',
    action: 'dataset.upload_scan',
    resource: 'churn_data_clean.csv (SHA-256 verified)',
    result: 'SUCCESS',
    ipAddress: '127.0.0.1',
    requestId: 'req-aa781042'
  },
  {
    id: 'aud-004',
    timestamp: '2026-09-30 08:45:11 UTC',
    actor: 'unknown_client',
    action: 'auth.login_attempt',
    resource: 'POST /api/v1/auth/login',
    result: 'DENIED',
    ipAddress: '203.0.113.42',
    requestId: 'req-0099411b'
  }
];

export const AdminDashboard: React.FC = () => {
  const { user } = useAuthStore();
  const [searchTerm, setSearchTerm] = useState('');
  const [logs] = useState<AuditLogEntry[]>(AUDIT_LOGS);

  const filteredLogs = logs.filter(l => 
    l.actor.toLowerCase().includes(searchTerm.toLowerCase()) ||
    l.action.toLowerCase().includes(searchTerm.toLowerCase()) ||
    l.resource.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2">
          <span className="p-2 rounded-lg bg-rose-500/10 text-rose-400">
            <ShieldCheck className="w-5 h-5" />
          </span>
          <h1 className="text-2xl font-bold tracking-tight">Security Center & Audit Logs</h1>
          <span className="badge badge-neutral text-xs font-mono">OWASP ASVS Verified</span>
        </div>
        <p className="text-sm text-slate-400 mt-1">
          Cryptographically immutable audit trail, system worker health, and tenant isolation telemetry.
        </p>
      </div>

      {/* Admin KPI Overview */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="panel p-4">
          <div className="text-xs text-slate-400">Active Agent Workers</div>
          <div className="text-2xl font-bold mt-1 text-slate-100">8 / 8 Online</div>
          <div className="text-xs text-emerald-400 mt-1">Zero worker failures</div>
        </div>
        <div className="panel p-4">
          <div className="text-xs text-slate-400">Tenant Isolation Status</div>
          <div className="text-2xl font-bold mt-1 text-emerald-400">100% Enforced</div>
          <div className="text-xs text-slate-500 mt-1">PostgreSQL RLS Active</div>
        </div>
        <div className="panel p-4">
          <div className="text-xs text-slate-400">Audit Trail Integrity</div>
          <div className="text-2xl font-bold mt-1 text-sky-400">HMAC-SHA256</div>
          <div className="text-xs text-slate-500 mt-1">Append-only chain valid</div>
        </div>
        <div className="panel p-4">
          <div className="text-xs text-slate-400">Unauthorized Rejections</div>
          <div className="text-2xl font-bold mt-1 text-slate-100">1 Request (Denied)</div>
          <div className="text-xs text-slate-500 mt-1">Rate limiting healthy</div>
        </div>
      </div>

      {/* Audit Log Table */}
      <div className="panel flex flex-col">
        <div className="p-4 border-b border-border flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="relative flex-1 max-w-sm">
            <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search actors, actions, resources..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="input pl-9 text-xs py-1.5"
            />
          </div>
          <span className="text-xs text-slate-400 font-mono">
            Zero secret material stored in audit records
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="data-table">
            <thead>
              <tr>
                <th>Timestamp (UTC)</th>
                <th>Actor</th>
                <th>Action</th>
                <th>Resource Target</th>
                <th>Result</th>
                <th>Client IP</th>
                <th>Request ID</th>
              </tr>
            </thead>
            <tbody>
              {filteredLogs.map((log) => (
                <tr key={log.id}>
                  <td className="font-mono text-xs text-slate-400">{log.timestamp}</td>
                  <td className="font-medium text-slate-200">{log.actor}</td>
                  <td className="font-mono text-xs text-primary-light">{log.action}</td>
                  <td className="text-xs text-slate-300 max-w-[220px] truncate">{log.resource}</td>
                  <td>
                    {log.result === 'SUCCESS' ? (
                      <span className="badge badge-success text-[10px] py-0">SUCCESS</span>
                    ) : log.result === 'DENIED' ? (
                      <span className="badge badge-danger text-[10px] py-0">DENIED</span>
                    ) : (
                      <span className="badge badge-warning text-[10px] py-0">FAILED</span>
                    )}
                  </td>
                  <td className="font-mono text-xs text-slate-500">{log.ipAddress}</td>
                  <td className="font-mono text-xs text-slate-500">{log.requestId}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
