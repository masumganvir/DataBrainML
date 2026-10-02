import React, { useState } from 'react';
import { Target, Building2, Shield, Sparkles, X, Check, HelpCircle } from 'lucide-react';
import { mlApi } from '@/services/api';

interface ContextModalProps {
  sessionId: string;
  initialDomain?: string;
  initialObjective?: string;
  initialMode?: 'guided' | 'autonomous';
  isOpen: boolean;
  onClose: () => void;
  onSaved: (context: { datasetDomain: string; predictionObjective: string; executionMode: 'guided' | 'autonomous' }) => void;
}

const DOMAIN_OPTIONS = [
  { value: 'finance', label: 'Finance & Banking', icon: '🏦', desc: 'Fraud detection, credit scoring, transaction risks' },
  { value: 'healthcare', label: 'Healthcare & Medicine', icon: '🏥', desc: 'Patient diagnosis, disease prognosis, clinical trials' },
  { value: 'ecommerce', label: 'E-Commerce & Retail', icon: '🛒', desc: 'Customer churn, demand forecasting, recommendation' },
  { value: 'cybersecurity', label: 'Cybersecurity', icon: '🛡️', desc: 'Intrusion detection, anomaly isolation, malware scans' },
  { value: 'marketing', label: 'Marketing & Sales', icon: '📈', desc: 'Conversion rate, lead scoring, customer lifetime value' },
  { value: 'manufacturing', label: 'Manufacturing & IoT', icon: '⚙️', desc: 'Predictive maintenance, sensor degradation, quality assurance' },
  { value: 'general', label: 'General / Other', icon: '📊', desc: 'Standard tabular supervised or unsupervised learning' },
];

export const ContextModal: React.FC<ContextModalProps> = ({
  sessionId,
  initialDomain = '',
  initialObjective = '',
  initialMode = 'guided',
  isOpen,
  onClose,
  onSaved,
}) => {
  const [domain, setDomain] = useState(initialDomain);
  const [objective, setObjective] = useState(initialObjective);
  const [mode, setMode] = useState<'guided' | 'autonomous'>(initialMode);
  const [isSaving, setIsSaving] = useState(false);
  const [showHelp, setShowHelp] = useState(false);

  if (!isOpen) return null;

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await mlApi.setContext(sessionId, {
        dataset_domain: domain || undefined,
        prediction_objective: objective || undefined,
        execution_mode: mode,
      });
      onSaved({ datasetDomain: domain, predictionObjective: objective, executionMode: mode });
      onClose();
    } catch (err) {
      console.error('Failed to set context:', err);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      zIndex: 100,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'rgba(0, 0, 0, 0.75)',
      backdropFilter: 'blur(8px)',
      padding: '16px',
    }}>
      <div style={{
        background: '#0d1321',
        border: '1px solid rgba(99, 102, 241, 0.3)',
        borderRadius: '16px',
        width: '100%',
        maxWidth: '560px',
        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.7), 0 0 30px rgba(99, 102, 241, 0.2)',
        overflow: 'hidden',
        animation: 'fadeIn 0.2s ease-out',
      }}>
        {/* Header */}
        <div style={{
          padding: '20px 24px',
          borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          background: 'rgba(99, 102, 241, 0.04)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{
              width: '32px',
              height: '32px',
              borderRadius: '8px',
              background: 'linear-gradient(135deg, #6366f1, #a855f7)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}>
              <Building2 size={16} color="#fff" />
            </div>
            <div>
              <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 700, color: '#f8fafc' }}>
                Domain & Objective Context
              </h3>
              <p style={{ margin: 0, fontSize: '0.75rem', color: '#94a3b8' }}>
                Context-aware reasoning prevents naive data removal (e.g. retaining fraud outliers)
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              color: '#94a3b8',
              cursor: 'pointer',
              padding: '6px',
              borderRadius: '6px',
            }}
          >
            <X size={18} />
          </button>
        </div>

        {/* Body */}
        <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px', maxHeight: '70vh', overflowY: 'auto' }}>
          {/* Execution Mode */}
          <div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
              <label style={{ fontSize: '0.85rem', fontWeight: 600, color: '#e2e8f0', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Shield size={14} color="#818cf8" />
                Execution Mode
              </label>
              <button
                type="button"
                onClick={() => setShowHelp(!showHelp)}
                style={{ background: 'none', border: 'none', color: '#818cf8', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.75rem' }}
              >
                <HelpCircle size={12} />
                {showHelp ? 'Hide info' : 'What is this?'}
              </button>
            </div>

            {showHelp && (
              <div style={{
                padding: '10px 14px',
                borderRadius: '8px',
                background: 'rgba(99, 102, 241, 0.08)',
                border: '1px solid rgba(99, 102, 241, 0.2)',
                fontSize: '0.75rem',
                color: '#cbd5e1',
                marginBottom: '10px',
                lineHeight: 1.5,
              }}>
                <strong>Guided Mode (Recommended):</strong> The AI asks for human confirmation before any critical preprocessing or modeling steps.<br />
                <strong>Autonomous Mode:</strong> The agent automatically makes decisions based on analytical evidence and records an auditable decision log.
              </div>
            )}

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
              <button
                type="button"
                onClick={() => setMode('guided')}
                style={{
                  padding: '12px',
                  borderRadius: '10px',
                  background: mode === 'guided' ? 'rgba(99, 102, 241, 0.15)' : 'rgba(255, 255, 255, 0.03)',
                  border: mode === 'guided' ? '1px solid #6366f1' : '1px solid rgba(255, 255, 255, 0.08)',
                  color: mode === 'guided' ? '#c7d2fe' : '#94a3b8',
                  textAlign: 'left',
                  cursor: 'pointer',
                  transition: 'all 0.15s',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
                  <span style={{ fontWeight: 700, fontSize: '0.85rem' }}>Guided Mode</span>
                  {mode === 'guided' && <Check size={14} color="#818cf8" />}
                </div>
                <p style={{ margin: 0, fontSize: '0.7rem', color: '#94a3b8', lineHeight: 1.4 }}>
                  Human-in-the-loop approvals before major actions.
                </p>
              </button>

              <button
                type="button"
                onClick={() => setMode('autonomous')}
                style={{
                  padding: '12px',
                  borderRadius: '10px',
                  background: mode === 'autonomous' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(255, 255, 255, 0.03)',
                  border: mode === 'autonomous' ? '1px solid #10b981' : '1px solid rgba(255, 255, 255, 0.08)',
                  color: mode === 'autonomous' ? '#a7f3d0' : '#94a3b8',
                  textAlign: 'left',
                  cursor: 'pointer',
                  transition: 'all 0.15s',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
                  <span style={{ fontWeight: 700, fontSize: '0.85rem' }}>Autonomous Mode</span>
                  {mode === 'autonomous' && <Check size={14} color="#34d399" />}
                </div>
                <p style={{ margin: 0, fontSize: '0.7rem', color: '#94a3b8', lineHeight: 1.4 }}>
                  Automated execution with strict safeguards & decision log.
                </p>
              </button>
            </div>
          </div>

          {/* Dataset Domain */}
          <div>
            <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#e2e8f0', marginBottom: '8px' }}>
              Dataset Domain
            </label>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))', gap: '8px' }}>
              {DOMAIN_OPTIONS.map(opt => (
                <button
                  key={opt.value}
                  type="button"
                  onClick={() => setDomain(opt.value)}
                  style={{
                    padding: '8px 10px',
                    borderRadius: '8px',
                    background: domain === opt.value ? 'rgba(99, 102, 241, 0.15)' : 'rgba(255, 255, 255, 0.03)',
                    border: domain === opt.value ? '1px solid #818cf8' : '1px solid rgba(255, 255, 255, 0.06)',
                    color: domain === opt.value ? '#c7d2fe' : '#94a3b8',
                    textAlign: 'left',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    fontSize: '0.78rem',
                  }}
                >
                  <span>{opt.icon}</span>
                  <span style={{ fontWeight: domain === opt.value ? 700 : 400 }}>{opt.label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Prediction Objective */}
          <div>
            <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, color: '#e2e8f0', marginBottom: '6px' }}>
              What are you trying to predict?
            </label>
            <div style={{ position: 'relative' }}>
              <input
                type="text"
                value={objective}
                onChange={e => setObjective(e.target.value)}
                placeholder="e.g. fraud, customer churn, house price, credit risk, disease"
                style={{
                  width: '100%',
                  padding: '10px 14px',
                  borderRadius: '8px',
                  background: 'rgba(255, 255, 255, 0.04)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  color: '#fff',
                  fontSize: '0.85rem',
                  outline: 'none',
                }}
              />
            </div>
            <p style={{ margin: '6px 0 0', fontSize: '0.7rem', color: '#64748b' }}>
              Used to guide outlier retention reasoning, metric selection (e.g. PR-AUC for fraud), and algorithms.
            </p>
          </div>
        </div>

        {/* Footer */}
        <div style={{
          padding: '16px 24px',
          borderTop: '1px solid rgba(255, 255, 255, 0.08)',
          background: 'rgba(9, 13, 22, 0.5)',
          display: 'flex',
          justifyContent: 'flex-end',
          gap: '10px',
        }}>
          <button
            type="button"
            className="btn btn-outline btn-sm"
            onClick={onClose}
          >
            Cancel
          </button>
          <button
            type="button"
            className="btn btn-primary btn-sm"
            onClick={handleSave}
            disabled={isSaving}
          >
            {isSaving ? 'Saving...' : 'Save Context'}
          </button>
        </div>
      </div>
    </div>
  );
};
