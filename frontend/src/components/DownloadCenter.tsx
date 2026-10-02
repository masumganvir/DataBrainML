import React, { useState } from 'react';
import {
  Download, FileText, Code2, Package, Sparkles, CheckCircle2,
  RefreshCw, Copy, Check, ExternalLink, BookOpen, Layers, Terminal
} from 'lucide-react';
import { mlApi, BASE_URL } from '@/services/api';

interface DownloadCenterProps {
  sessionId: string;
}

export const DownloadCenter: React.FC<DownloadCenterProps> = ({ sessionId }) => {
  const [isPackaging, setIsPackaging] = useState(false);
  const [isGeneratingNotebook, setIsGeneratingNotebook] = useState(false);
  const [bundleInfo, setBundleInfo] = useState<{ filename: string; download_url: string; zip_size_bytes: number } | null>(null);
  const [notebookInfo, setNotebookInfo] = useState<{ filename: string; download_url: string } | null>(null);
  const [copiedCode, setCopiedCode] = useState(false);

  const sampleInferenceCode = `import joblib
import pandas as pd

# 1. Load serialized production pipeline (preprocessing + estimator)
pipeline = joblib.load("model/final_model.joblib")

# 2. Ingest unlabelled incoming data
new_data = pd.read_csv("new_customers.csv")

# 3. Generate predictions directly through enclosed ColumnTransformer
predictions = pipeline.predict(new_data)
print("Predictions:", predictions)

# For probability estimation (classification)
if hasattr(pipeline, "predict_proba"):
    probabilities = pipeline.predict_proba(new_data)
    print("Probabilities:", probabilities)`;

  const handleGenerateNotebook = async () => {
    setIsGeneratingNotebook(true);
    try {
      const resp = await mlApi.generateNotebook(sessionId);
      setNotebookInfo(resp);
    } catch (err: any) {
      alert(`Notebook generation failed: ${err.message}`);
    } finally {
      setIsGeneratingNotebook(false);
    }
  };

  const handlePackageBundle = async () => {
    setIsPackaging(true);
    try {
      const resp = await mlApi.packageArtifacts(sessionId);
      setBundleInfo(resp);
    } catch (err: any) {
      alert(`Packaging failed: ${err.message}`);
    } finally {
      setIsPackaging(false);
    }
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(sampleInferenceCode);
    setCopiedCode(true);
    setTimeout(() => setCopiedCode(false), 2000);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', paddingBottom: '32px' }}>
      {/* ── Top Header ── */}
      <div className="glass-card" style={{
        padding: '24px',
        border: '1px solid rgba(99, 102, 241, 0.25)',
        background: 'linear-gradient(180deg, rgba(99, 102, 241, 0.06) 0%, rgba(9, 13, 22, 0.6) 100%)',
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
              <Package size={20} color="#818cf8" />
              <h2 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 700, color: '#f8fafc' }}>
                Deliverables & Production Export Center
              </h2>
            </div>
            <p style={{ margin: 0, fontSize: '0.85rem', color: '#94a3b8' }}>
              Export standalone reproducible artifacts: Jupyter Notebooks, serialized model pipelines, reports, and inference code.
            </p>
          </div>

          <button
            onClick={handlePackageBundle}
            disabled={isPackaging}
            className="btn btn-primary"
            style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '10px 18px', fontWeight: 700 }}
          >
            {isPackaging ? (
              <>
                <RefreshCw size={15} style={{ animation: 'spin 1s linear infinite' }} />
                Packaging Project…
              </>
            ) : (
              <>
                <Download size={15} />
                Download Complete Project ZIP
              </>
            )}
          </button>
        </div>
      </div>

      {/* ── Grid of Deliverables (Section 34 & 45) ── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' }}>
        {/* 1. Complete ZIP Package */}
        <div className="glass-card" style={{ padding: '20px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px' }}>
              <div style={{ width: '36px', height: '36px', borderRadius: '8px', background: 'rgba(99, 102, 241, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Package size={18} color="#818cf8" />
              </div>
              <div>
                <h4 style={{ margin: 0, fontSize: '0.95rem', fontWeight: 700, color: '#f8fafc' }}>
                  Complete Project Package
                </h4>
                <span style={{ fontSize: '0.72rem', color: '#94a3b8' }}>All-in-one ZIP archive</span>
              </div>
            </div>
            <p style={{ fontSize: '0.8rem', color: '#cbd5e1', lineHeight: 1.5, marginBottom: '16px' }}>
              Contains model (.joblib), metadata (.json), standalone Jupyter notebook (.ipynb), reports (.html/.md), and inference scripts.
            </p>
          </div>

          <div style={{ display: 'flex', gap: '8px' }}>
            <a
              href={mlApi.getBundleDownloadUrl(sessionId)}
              download
              className="btn btn-primary btn-sm"
              style={{ flex: 1, textDecoration: 'none', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px' }}
            >
              <Download size={13} />
              Download ZIP Bundle
            </a>
          </div>
        </div>

        {/* 2. Executable Jupyter Notebook */}
        <div className="glass-card" style={{ padding: '20px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px' }}>
              <div style={{ width: '36px', height: '36px', borderRadius: '8px', background: 'rgba(245, 158, 11, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <BookOpen size={18} color="#fbbf24" />
              </div>
              <div>
                <h4 style={{ margin: 0, fontSize: '0.95rem', fontWeight: 700, color: '#f8fafc' }}>
                  Jupyter Notebook (.ipynb)
                </h4>
                <span style={{ fontSize: '0.72rem', color: '#94a3b8' }}>24-section executable notebook</span>
              </div>
            </div>
            <p style={{ fontSize: '0.8rem', color: '#cbd5e1', lineHeight: 1.5, marginBottom: '16px' }}>
              Genuine executable Python cells covering schema analysis, EDA, leak-free preprocessing, cross-validation, and pipeline saving.
            </p>
          </div>

          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              onClick={handleGenerateNotebook}
              disabled={isGeneratingNotebook}
              className="btn btn-outline btn-sm"
              style={{ flex: 1 }}
            >
              {isGeneratingNotebook ? 'Generating…' : 'Generate Notebook'}
            </button>
            <a
              href={mlApi.getNotebookDownloadUrl(sessionId)}
              download
              className="btn btn-primary btn-sm"
              style={{ flex: 1, textDecoration: 'none', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px' }}
            >
              <Download size={13} />
              Download .ipynb
            </a>
          </div>
        </div>

        {/* 3. Production Model Pipeline */}
        <div className="glass-card" style={{ padding: '20px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px' }}>
              <div style={{ width: '36px', height: '36px', borderRadius: '8px', background: 'rgba(16, 185, 129, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Layers size={18} color="#34d399" />
              </div>
              <div>
                <h4 style={{ margin: 0, fontSize: '0.95rem', fontWeight: 700, color: '#f8fafc' }}>
                  Model Pipeline (.joblib)
                </h4>
                <span style={{ fontSize: '0.72rem', color: '#94a3b8' }}>Serialized Scikit-learn Pipeline</span>
              </div>
            </div>
            <p style={{ fontSize: '0.8rem', color: '#cbd5e1', lineHeight: 1.5, marginBottom: '16px' }}>
              Encloses preprocessing ColumnTransformer and champion estimator in a single serializable object for direct batch inference.
            </p>
          </div>

          <div style={{ display: 'flex', gap: '8px' }}>
            <a
              href={mlApi.getModelDownloadUrl(sessionId)}
              download
              className="btn btn-primary btn-sm"
              style={{ flex: 1, textDecoration: 'none', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px' }}
            >
              <Download size={13} />
              Download final_model.joblib
            </a>
          </div>
        </div>

        {/* 4. Analysis Reports (HTML & Markdown) */}
        <div className="glass-card" style={{ padding: '20px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px' }}>
              <div style={{ width: '36px', height: '36px', borderRadius: '8px', background: 'rgba(14, 165, 233, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <FileText size={18} color="#38bdf8" />
              </div>
              <div>
                <h4 style={{ margin: 0, fontSize: '0.95rem', fontWeight: 700, color: '#f8fafc' }}>
                  Analysis Report (19 Sections)
                </h4>
                <span style={{ fontSize: '0.72rem', color: '#94a3b8' }}>HTML & Markdown formats</span>
              </div>
            </div>
            <p style={{ fontSize: '0.8rem', color: '#cbd5e1', lineHeight: 1.5, marginBottom: '16px' }}>
              Complete 19-section diagnostic report covering data quality, outliers, correlations, cross-validation, and limitations.
            </p>
          </div>

          <div style={{ display: 'flex', gap: '8px' }}>
            <a
              href={mlApi.getReportHtmlUrl(sessionId)}
              target="_blank"
              rel="noreferrer"
              className="btn btn-outline btn-sm"
              style={{ flex: 1, textDecoration: 'none', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px' }}
            >
              <ExternalLink size={12} />
              HTML Report
            </a>
            <a
              href={mlApi.getReportMarkdownUrl(sessionId)}
              download
              className="btn btn-primary btn-sm"
              style={{ flex: 1, textDecoration: 'none', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px' }}
            >
              <Download size={12} />
              Markdown
            </a>
          </div>
        </div>
      </div>

      {/* ── Standalone Production Inference Code (Section 33) ── */}
      <div className="glass-card" style={{ padding: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Terminal size={18} color="#818cf8" />
            <h3 style={{ margin: 0, fontSize: '1.05rem', fontWeight: 700, color: '#f8fafc' }}>
              Production Inference Script (inference.py)
            </h3>
          </div>
          <button
            onClick={copyToClipboard}
            style={{
              background: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: '6px',
              padding: '6px 12px',
              color: '#c7d2fe',
              fontSize: '0.75rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            {copiedCode ? <Check size={13} color="#34d399" /> : <Copy size={13} />}
            {copiedCode ? 'Copied!' : 'Copy Code'}
          </button>
        </div>

        <pre style={{
          margin: 0,
          padding: '16px',
          borderRadius: '8px',
          background: '#090d16',
          border: '1px solid rgba(255, 255, 255, 0.06)',
          fontSize: '0.8rem',
          color: '#e2e8f0',
          fontFamily: 'monospace',
          overflowX: 'auto',
          lineHeight: 1.5,
        }}>
          <code>{sampleInferenceCode}</code>
        </pre>
      </div>
    </div>
  );
};
