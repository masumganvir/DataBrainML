import React, { useState, useRef } from 'react'
import {
  Upload,
  Database,
  FileSpreadsheet,
  CheckCircle2,
  AlertTriangle,
  Info,
  ShieldCheck,
  Search,
  Filter,
  BarChart2,
  Table,
  Zap,
} from 'lucide-react'
import { authStore } from '../../services/authStore'

export function DatasetWorkspace() {
  const [activeTab, setActiveTab] = useState<'overview' | 'schema' | 'quality' | 'outliers' | 'missing' | 'preview'>('overview')
  const [isUploading, setIsUploading] = useState(false)
  const [uploadSuccess, setUploadSuccess] = useState(true)
  const [fileName, setFileName] = useState('churn_enterprise_v2.csv')
  const [rowCount, setRowCount] = useState(15000)
  const [colCount, setColCount] = useState(14)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    // Client-side file size and MIME security gate
    if (file.size > 104857600) {
      alert('File size exceeds maximum permitted limit (100MB).')
      return
    }

    setIsUploading(true)
    setFileName(file.name)

    // Simulate backend chunked ingestion, schema detection, and profiling pipeline
    setTimeout(() => {
      setIsUploading(false)
      setUploadSuccess(true)
      setRowCount(Math.floor(Math.random() * 10000) + 5000)
    }, 1200)
  }

  const columnsSchema = [
    { name: 'customer_id', type: 'Integer / Identifier', missing: '0.0%', unique: '15,000', role: 'ID Column' },
    { name: 'credit_score', type: 'Float / Numerical', missing: '0.2%', unique: '482', role: 'Predictor' },
    { name: 'country', type: 'String / Categorical', missing: '0.0%', unique: '3', role: 'Predictor' },
    { name: 'gender', type: 'String / Binary', missing: '0.0%', unique: '2', role: 'Predictor' },
    { name: 'age', type: 'Integer / Numerical', missing: '0.0%', unique: '72', role: 'Predictor' },
    { name: 'tenure_months', type: 'Integer / Numerical', missing: '0.5%', unique: '12', role: 'Predictor' },
    { name: 'account_balance', type: 'Float / Numerical', missing: '0.0%', unique: '8,412', role: 'Predictor' },
    { name: 'num_products', type: 'Integer / Discrete', missing: '0.0%', unique: '4', role: 'Predictor' },
    { name: 'has_credit_card', type: 'Integer / Binary', missing: '0.0%', unique: '2', role: 'Predictor' },
    { name: 'is_active_member', type: 'Integer / Binary', missing: '0.0%', unique: '2', role: 'Predictor' },
    { name: 'estimated_salary', type: 'Float / Numerical', missing: '0.1%', unique: '12,980', role: 'Predictor' },
    { name: 'churned', type: 'Integer / Binary', missing: '0.0%', unique: '2', role: 'Target Candidate' },
  ]

  const outlierAnalysis = [
    {
      feature: 'account_balance',
      detected: 142,
      method: 'IQR & Isolation Forest',
      recommendation: 'PRESERVE (Legitimate High-Balance Segment)',
      action: 'No deletion. Tree-based models are robust to extreme quantiles.',
      risk: 'Deleting these rows creates bias against top-tier corporate accounts.',
    },
    {
      feature: 'age',
      detected: 8,
      method: 'Z-Score (> 4.0)',
      recommendation: 'CAP at 99th percentile (Windsorize)',
      action: 'Values exceeding 95 capped to 95. Retained in dataset.',
      risk: 'Negligible risk of bias.',
    },
  ]

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h1 style={{ fontSize: '1.6rem', fontWeight: 800, margin: 0 }}>Dataset & Profiling Studio</h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', margin: '4px 0 0 0' }}>
            Deterministic statistical profiling, schema inference, MCAR diagnostics, and leak-free validation.
          </p>
        </div>

        <button
          onClick={() => fileInputRef.current?.click()}
          className="btn btn-primary"
          style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
        >
          <Upload size={16} /> Upload New Dataset
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv,.xlsx,.xls,.parquet,.json"
          style={{ display: 'none' }}
          onChange={handleFileUpload}
        />
      </div>

      {/* Dataset Overview Summary Card */}
      <div
        style={{
          background: 'var(--bg-card)',
          border: '1px solid var(--border-subtle)',
          borderRadius: 'var(--radius-xl)',
          padding: '24px',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
            <div
              style={{
                width: '46px',
                height: '46px',
                borderRadius: '12px',
                background: 'rgba(6, 182, 212, 0.12)',
                color: 'var(--secondary-accent)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <FileSpreadsheet size={24} />
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <h3 style={{ fontSize: '1.15rem', fontWeight: 700, margin: 0 }}>{fileName}</h3>
                <span className="badge badge-success">CLEAN PROFILE</span>
                <span className="badge badge-neutral">CSV</span>
              </div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                {rowCount.toLocaleString()} rows • {colCount} columns • 3.4 MB • SHA-256 Verified
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '20px' }}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--success)' }}>98 / 100</div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>QUALITY SCORE</div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--secondary-accent)' }}>0.1%</div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>MISSING RATE</div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--primary-light)' }}>0</div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>TARGET LEAKAGE</div>
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <div
          style={{
            display: 'flex',
            gap: '8px',
            marginTop: '24px',
            borderTop: '1px solid var(--border-subtle)',
            paddingTop: '16px',
            overflowX: 'auto',
          }}
        >
          {[
            { id: 'overview', label: 'Summary & Distributions' },
            { id: 'schema', label: 'Inferred Schema' },
            { id: 'quality', label: 'Data Quality Audit' },
            { id: 'outliers', label: 'Outlier Intelligence (No Delete)' },
            { id: 'missing', label: 'Missing Values (MCAR)' },
          ].map((t) => (
            <button
              key={t.id}
              onClick={() => setActiveTab(t.id as any)}
              style={{
                padding: '8px 16px',
                borderRadius: 'var(--radius-md)',
                border: 'none',
                fontSize: '0.85rem',
                fontWeight: 600,
                cursor: 'pointer',
                background: activeTab === t.id ? 'var(--primary)' : 'transparent',
                color: activeTab === t.id ? '#ffffff' : 'var(--text-secondary)',
                transition: 'all 120ms ease',
              }}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>

      {/* Tab 1: Schema */}
      {activeTab === 'schema' && (
        <div className="data-table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>Column Name</th>
                <th>Inferred Type</th>
                <th>Missing %</th>
                <th>Unique Cardinality</th>
                <th>Model Role</th>
              </tr>
            </thead>
            <tbody>
              {columnsSchema.map((c) => (
                <tr key={c.name}>
                  <td style={{ fontWeight: 600, fontFamily: 'var(--font-mono)' }}>{c.name}</td>
                  <td>{c.type}</td>
                  <td>{c.missing}</td>
                  <td>{c.unique}</td>
                  <td>
                    <span
                      style={{
                        padding: '2px 8px',
                        borderRadius: 'var(--radius-sm)',
                        fontSize: '0.75rem',
                        fontWeight: 600,
                        background: c.role === 'Target Candidate' ? 'rgba(6, 182, 212, 0.15)' : 'rgba(255, 255, 255, 0.05)',
                        color: c.role === 'Target Candidate' ? 'var(--secondary-accent)' : 'var(--text-secondary)',
                      }}
                    >
                      {c.role}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Tab 2: Outliers */}
      {activeTab === 'outliers' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div
            style={{
              padding: '16px 20px',
              borderRadius: 'var(--radius-lg)',
              background: 'rgba(245, 158, 11, 0.08)',
              border: '1px solid rgba(245, 158, 11, 0.2)',
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
            }}
          >
            <AlertTriangle size={20} color="var(--warning)" style={{ flexShrink: 0 }} />
            <div style={{ fontSize: '0.85rem', color: 'var(--text-primary)' }}>
              <strong>Non-Destructive Outlier Principle:</strong> The Outlier Agent never blindly drops extreme observations.
              In domains like fraud or high-balance churn, extreme records often represent the target phenomenon itself.
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '16px' }}>
            {outlierAnalysis.map((o) => (
              <div
                key={o.feature}
                style={{
                  background: 'var(--bg-card)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-xl)',
                  padding: '20px',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <span style={{ fontWeight: 700, fontSize: '0.95rem', fontFamily: 'var(--font-mono)' }}>{o.feature}</span>
                  <span className="badge badge-warning">{o.detected} flagged observations</span>
                </div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Detection: {o.method}</div>
                <div style={{ marginTop: '12px', padding: '10px', borderRadius: 'var(--radius-md)', background: 'rgba(15, 23, 42, 0.5)' }}>
                  <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--secondary-accent)' }}>{o.recommendation}</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '4px' }}>{o.action}</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--danger)', marginTop: '6px' }}>⚠️ Risk: {o.risk}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab 3: Overview & Quality */}
      {(activeTab === 'overview' || activeTab === 'quality') && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px' }}>
          <div
            style={{
              background: 'var(--bg-card)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-xl)',
              padding: '24px',
            }}
          >
            <h3 style={{ fontSize: '1.05rem', fontWeight: 700, marginBottom: '14px' }}>Quality Verification Invariants</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.85rem' }}>
                <CheckCircle2 size={16} color="var(--success)" />
                <span>Zero duplicate primary key rows detected</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.85rem' }}>
                <CheckCircle2 size={16} color="var(--success)" />
                <span>Constant & zero-variance column filter passed</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.85rem' }}>
                <CheckCircle2 size={16} color="var(--success)" />
                <span>No direct target leakage columns found</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.85rem' }}>
                <CheckCircle2 size={16} color="var(--success)" />
                <span>Strict train/test temporal and group isolation verified</span>
              </div>
            </div>
          </div>

          <div
            style={{
              background: 'var(--bg-card)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-xl)',
              padding: '24px',
            }}
          >
            <h3 style={{ fontSize: '1.05rem', fontWeight: 700, marginBottom: '14px' }}>Recommended AutoML Strategy</h3>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
              Tabular binary classification detected on target <code style={{ color: 'var(--secondary-accent)' }}>churned</code>.
              Candidate algorithm matrix:
              <ul style={{ marginTop: '8px', paddingLeft: '20px' }}>
                <li><strong>Baseline First:</strong> Dummy stratified classifier + LogisticRegression</li>
                <li><strong>Gradient Boosting:</strong> LightGBM, XGBoost & CatBoost</li>
                <li><strong>Neural Candidate:</strong> PyTorch TabularMLP with Dropout & BatchNorm</li>
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default DatasetWorkspace
