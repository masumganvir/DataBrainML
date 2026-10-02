import React, { useState } from 'react';
import { 
  Bell, AlertTriangle, ShieldAlert, CheckCircle2, 
  Info, Filter, Check, Clock
} from 'lucide-react';
import { useAuthStore } from '../../services/authStore';

interface AlertItem {
  id: string;
  title: string;
  description: string;
  severity: 'CRITICAL' | 'WARNING' | 'INFO';
  timestamp: string;
  source: string;
  acknowledged: boolean;
}

const INITIAL_ALERTS: AlertItem[] = [
  {
    id: 'alt-001',
    title: 'Data Drift Detected in ContractType',
    description: 'Population Stability Index (PSI) reached 0.142 exceeding the configured threshold of 0.100.',
    severity: 'WARNING',
    timestamp: '12 minutes ago',
    source: 'MLOps Drift Monitor',
    acknowledged: false,
  },
  {
    id: 'alt-002',
    title: 'Model Retraining Job Trigger Available',
    description: 'Continuous evaluation suggests retraining champion XGBoost model with latest 30-day window.',
    severity: 'INFO',
    timestamp: '2 hours ago',
    source: 'AutoML Scheduler',
    acknowledged: false,
  },
  {
    id: 'alt-003',
    title: 'Ingress Peak Latency Exceeded 10ms',
    description: 'Endpoint /v1/predict observed 3 queries with 14ms latency during upstream network spike.',
    severity: 'WARNING',
    timestamp: '5 hours ago',
    source: 'API Gateway Probe',
    acknowledged: true,
  },
  {
    id: 'alt-004',
    title: 'TLS Certificate Renewal Successful',
    description: 'Mutual TLS certificate for deployment ingress renewed securely for 90 days.',
    severity: 'INFO',
    timestamp: '1 day ago',
    source: 'DevSecOps Certificate Vault',
    acknowledged: true,
  }
];

export const AlertCenter: React.FC = () => {
  const { activeProject } = useAuthStore();
  const [alerts, setAlerts] = useState<AlertItem[]>(INITIAL_ALERTS);
  const [filter, setFilter] = useState<'ALL' | 'UNACKNOWLEDGED'>('ALL');

  const filteredAlerts = alerts.filter(a => {
    if (filter === 'UNACKNOWLEDGED') return !a.acknowledged;
    return true;
  });

  const handleAcknowledge = (id: string) => {
    setAlerts(prev => prev.map(a => a.id === id ? { ...a, acknowledged: true } : a));
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-2 rounded-lg bg-rose-500/10 text-rose-400">
              <Bell className="w-5 h-5" />
            </span>
            <h1 className="text-2xl font-bold tracking-tight">Alert Center</h1>
            <span className="badge badge-danger text-xs">
              {alerts.filter(a => !a.acknowledged).length} Pending Actions
            </span>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            System, model, and infrastructure alerts for <strong className="text-slate-200">{activeProject?.name || 'Customer Churn Prevention'}</strong>
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setFilter('ALL')}
            className={`btn text-xs ${filter === 'ALL' ? 'btn-primary' : 'btn-secondary'}`}
          >
            All Alerts ({alerts.length})
          </button>
          <button
            onClick={() => setFilter('UNACKNOWLEDGED')}
            className={`btn text-xs ${filter === 'UNACKNOWLEDGED' ? 'btn-primary' : 'btn-secondary'}`}
          >
            Unacknowledged ({alerts.filter(a => !a.acknowledged).length})
          </button>
        </div>
      </div>

      {/* Alerts List */}
      <div className="space-y-3">
        {filteredAlerts.length === 0 ? (
          <div className="panel p-12 text-center text-slate-400">
            <CheckCircle2 className="w-10 h-10 text-emerald-400 mx-auto mb-3" />
            <h3 className="font-bold text-slate-200">All alerts resolved</h3>
            <p className="text-xs text-slate-500 mt-1">No pending unacknowledged alerts in this project.</p>
          </div>
        ) : (
          filteredAlerts.map((alert) => (
            <div
              key={alert.id}
              className={`panel p-4 flex flex-col md:flex-row md:items-center justify-between gap-4 transition-colors ${
                !alert.acknowledged ? 'border-l-4 border-l-rose-500 bg-surface-elevated/40' : 'opacity-70'
              }`}
            >
              <div className="flex items-start gap-3">
                <div className="mt-0.5">
                  {alert.severity === 'CRITICAL' && <ShieldAlert className="w-5 h-5 text-rose-500" />}
                  {alert.severity === 'WARNING' && <AlertTriangle className="w-5 h-5 text-amber-500" />}
                  {alert.severity === 'INFO' && <Info className="w-5 h-5 text-sky-400" />}
                </div>

                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="font-bold text-slate-200 text-sm">{alert.title}</h3>
                    <span className={`badge text-[10px] font-semibold ${
                      alert.severity === 'CRITICAL' ? 'badge-danger' : alert.severity === 'WARNING' ? 'badge-warning' : 'badge-neutral'
                    }`}>
                      {alert.severity}
                    </span>
                  </div>
                  <p className="text-xs text-slate-400 mt-1">{alert.description}</p>
                  <div className="flex items-center gap-3 text-[11px] text-slate-500 mt-2 font-mono">
                    <span>Source: {alert.source}</span>
                    <span>•</span>
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3" /> {alert.timestamp}
                    </span>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-2 shrink-0">
                {!alert.acknowledged ? (
                  <button
                    onClick={() => handleAcknowledge(alert.id)}
                    className="btn btn-secondary text-xs flex items-center gap-1.5"
                  >
                    <Check className="w-3.5 h-3.5" />
                    Acknowledge
                  </button>
                ) : (
                  <span className="text-xs text-slate-500 flex items-center gap-1">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                    Acknowledged
                  </span>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
