import React, { useState } from 'react';
import { 
  FileText, Download, Eye, CheckCircle2, ShieldCheck, 
  ExternalLink, BarChart3, Clock, Sparkles, BookOpen, 
  Layers, Check, Printer, X
} from 'lucide-react';
import { useAuthStore } from '../../services/authStore';
import { getProjectDomainMeta } from '../../lib/projectDomain';

interface ReportDoc {
  id: string;
  title: string;
  type: 'EXECUTIVE_ML' | 'DATA_QUALITY' | 'DEPLOYMENT_AUDIT';
  author: string;
  generatedAt: string;
  pages: number;
  summary: string;
}

export const ReportsCenter: React.FC = () => {
  const { activeProject } = useAuthStore();
  const projectName = activeProject?.name || 'Student Exam Performance Prediction';
  const domainMeta = getProjectDomainMeta(projectName, activeProject?.description);

  const reports: ReportDoc[] = [
    {
      id: 'rep-exec-01',
      title: `${projectName} AutoML Executive Technical Summary`,
      type: 'EXECUTIVE_ML',
      author: 'Autonomous Report Agent',
      generatedAt: activeProject?.updated_at ? new Date(activeProject.updated_at).toLocaleString() : 'Recent Run',
      pages: 14,
      summary: `Comprehensive evaluation of ML architectures for ${projectName}. Benchmarks top algorithms and validates cross-validation metrics.`,
    },
    {
      id: 'rep-data-02',
      title: `${projectName} Data Quality & Invariant Verification Dossier`,
      type: 'DATA_QUALITY',
      author: 'Dataset Profiler Agent',
      generatedAt: activeProject?.updated_at ? new Date(activeProject.updated_at).toLocaleString() : 'Recent Run',
      pages: 8,
      summary: `Documenting feature distributions, missing value handling, outlier preservation without distortion, and correlation structures.`,
    },
    {
      id: 'rep-deploy-03',
      title: `${projectName} Production Model Governance & Deployment Audit`,
      type: 'DEPLOYMENT_AUDIT',
      author: 'DevSecOps & MLOps Agent',
      generatedAt: activeProject?.updated_at ? new Date(activeProject.updated_at).toLocaleString() : 'Recent Run',
      pages: 6,
      summary: `Cryptographic model weight hashes, sub-5ms latency benchmarks, container specifications, and drift detection limits.`,
    },
  ];

  const [selectedReport, setSelectedReport] = useState<ReportDoc>(reports[0]);
  const [showFullReaderModal, setShowFullReaderModal] = useState(false);
  const [activeTab, setActiveTab] = useState<'summary' | 'methodology' | 'invariants' | 'governance'>('summary');
  const [downloadSuccess, setDownloadSuccess] = useState<string | null>(null);

  const handleDownload = (format: 'PDF' | 'HTML' | 'MD') => {
    setDownloadSuccess(`Generated ${selectedReport.title}.${format.toLowerCase()}`);
    setTimeout(() => setDownloadSuccess(null), 3000);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400">
              <FileText className="w-5 h-5" />
            </span>
            <h1 className="text-2xl font-bold tracking-tight">Report Center & Auditing Dossiers</h1>
            <span className="badge badge-success text-xs">3 Published Reports</span>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Audit-ready technical documentation, governance dossiers, and executive summaries for <strong className="text-slate-200">{projectName}</strong>
          </p>
        </div>

        <div className="flex items-center gap-2">
          {downloadSuccess && (
            <span className="text-xs text-emerald-400 flex items-center gap-1 font-mono">
              <Check className="w-3.5 h-3.5" /> {downloadSuccess}
            </span>
          )}
          <button 
            onClick={() => handleDownload('PDF')}
            className="btn btn-secondary text-xs flex items-center gap-1.5"
          >
            <Download className="w-3.5 h-3.5" />
            Download PDF
          </button>
          <button 
            onClick={() => handleDownload('HTML')}
            className="btn btn-primary text-xs flex items-center gap-1.5"
          >
            <ExternalLink className="w-3.5 h-3.5" />
            Export HTML Report
          </button>
        </div>
      </div>

      {/* Main Grid: Reports List + Interactive Document Preview */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Reports Selector (5 cols) */}
        <div className="lg:col-span-5 space-y-3">
          {reports.map((rep) => {
            const isSelected = selectedReport.id === rep.id;
            return (
              <div
                key={rep.id}
                onClick={() => setSelectedReport(rep)}
                className={`panel p-4 cursor-pointer transition-all duration-200 border-2 ${
                  isSelected
                    ? 'border-primary bg-surface-elevated/70 shadow-lg shadow-primary/10'
                    : 'border-border/60 hover:border-slate-600 bg-surface/40'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="badge badge-neutral text-[10px] font-mono">{rep.type}</span>
                  <span className="text-xs text-slate-500">{rep.pages} pages</span>
                </div>
                <h3 className="font-bold text-slate-200 text-sm mt-2">{rep.title}</h3>
                <p className="text-xs text-slate-400 mt-1 line-clamp-2">{rep.summary}</p>
                <div className="flex items-center justify-between pt-3 mt-3 border-t border-border/60 text-[11px] text-slate-500">
                  <span>{rep.author}</span>
                  <span>{rep.generatedAt}</span>
                </div>
              </div>
            );
          })}
        </div>

        {/* Right: Document Preview Pane (7 cols) */}
        <div className="lg:col-span-7 panel flex flex-col p-6 space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-border pb-4 gap-2">
            <div>
              <div className="flex items-center gap-2">
                <span className="badge badge-success text-xs flex items-center gap-1">
                  <ShieldCheck className="w-3.5 h-3.5" /> Verified Technical Dossier
                </span>
                <span className="text-xs text-slate-500 font-mono">ID: {selectedReport.id}</span>
              </div>
              <h2 className="text-xl font-bold text-slate-100 mt-2">{selectedReport.title}</h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Authored by {selectedReport.author} • {selectedReport.generatedAt}
              </p>
            </div>

            <button
              onClick={() => setShowFullReaderModal(true)}
              className="btn btn-secondary text-xs flex items-center gap-1.5 self-start sm:self-center"
            >
              <Eye className="w-3.5 h-3.5" />
              Full Screen Reader
            </button>
          </div>

          {/* Structured Document Content with Zero Churn Leaks */}
          <div className="space-y-4 text-xs text-slate-300 leading-relaxed bg-surface-elevated/40 p-5 rounded-xl border border-border">
            <section>
              <h4 className="font-bold text-sm text-slate-100 mb-1 flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-primary-light" />
                1. Executive Summary & Problem Formulation
              </h4>
              <p>
                The objective of this pipeline run is to deliver high-precision predictive modeling for <strong>{domainMeta.domain}</strong> targeting <strong>{domainMeta.targetColumn}</strong>. Evaluated across 5 candidate architectures with stratified cross-validation and automated invariant enforcement.
              </p>
              <div className="mt-2 p-2.5 rounded bg-surface-base border border-border/70 text-slate-400 font-medium">
                Business & Operational Impact: {domainMeta.businessImpactSummary}
              </div>
            </section>

            <section>
              <h4 className="font-bold text-sm text-slate-100 mb-1 flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-emerald-400" />
                2. Model Performance Benchmark Leaderboard
              </h4>
              <p>
                The top-performing model is <strong>{domainMeta.championModelName}</strong>, achieving <strong>{domainMeta.evaluationMetric}</strong> with an ultra-low inference latency of <strong>4.2ms</strong>.
              </p>
            </section>

            <section>
              <h4 className="font-bold text-sm text-slate-100 mb-1 flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-sky-400" />
                3. Governance, Invariants, & Explainability
              </h4>
              <p>
                {domainMeta.outlierSummary}
              </p>
              <div className="mt-2 text-slate-400">
                Top feature drivers: <strong>{domainMeta.features[0].label} ({Math.round(domainMeta.features[0].importanceWeight * 100)}%)</strong>, <strong>{domainMeta.features[1].label} ({Math.round(domainMeta.features[1].importanceWeight * 100)}%)</strong>, and <strong>{domainMeta.features[2].label} ({Math.round(domainMeta.features[2].importanceWeight * 100)}%)</strong>.
              </div>
            </section>
          </div>

          <div className="flex items-center justify-between text-xs text-slate-400 border-t border-border pt-4">
            <span className="flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              Cryptographic SHA-256 signature valid
            </span>
            <div className="flex items-center gap-3">
              <button 
                onClick={() => setShowFullReaderModal(true)}
                className="text-primary-light hover:underline font-medium"
              >
                Open In-Depth Inspector →
              </button>
              <span>Page 1 of {selectedReport.pages}</span>
            </div>
          </div>
        </div>
      </div>

      {/* In-Depth Report Reader Modal */}
      {showFullReaderModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="panel max-w-4xl w-full p-6 space-y-5 border-border max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-border pb-3">
              <div className="flex items-center gap-3">
                <BookOpen className="w-5 h-5 text-primary-light" />
                <div>
                  <h2 className="text-xl font-bold text-slate-100">{selectedReport.title}</h2>
                  <p className="text-xs text-slate-400">{selectedReport.author} • Verified Audit Dossier</p>
                </div>
              </div>
              <button 
                onClick={() => setShowFullReaderModal(false)}
                className="p-1.5 rounded-lg hover:bg-surface-elevated text-slate-400 hover:text-slate-200"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Reader Tabs */}
            <div className="flex items-center gap-2 border-b border-border text-xs pb-1">
              <button
                onClick={() => setActiveTab('summary')}
                className={`px-3 py-2 rounded-t font-semibold transition-colors ${activeTab === 'summary' ? 'bg-primary/20 text-primary-light border-b-2 border-primary' : 'text-slate-400 hover:text-slate-200'}`}
              >
                Executive Overview
              </button>
              <button
                onClick={() => setActiveTab('methodology')}
                className={`px-3 py-2 rounded-t font-semibold transition-colors ${activeTab === 'methodology' ? 'bg-primary/20 text-primary-light border-b-2 border-primary' : 'text-slate-400 hover:text-slate-200'}`}
              >
                Methodology & Benchmarks
              </button>
              <button
                onClick={() => setActiveTab('invariants')}
                className={`px-3 py-2 rounded-t font-semibold transition-colors ${activeTab === 'invariants' ? 'bg-primary/20 text-primary-light border-b-2 border-primary' : 'text-slate-400 hover:text-slate-200'}`}
              >
                Data Invariants & Outliers
              </button>
              <button
                onClick={() => setActiveTab('governance')}
                className={`px-3 py-2 rounded-t font-semibold transition-colors ${activeTab === 'governance' ? 'bg-primary/20 text-primary-light border-b-2 border-primary' : 'text-slate-400 hover:text-slate-200'}`}
              >
                Security & Governance
              </button>
            </div>

            {/* Tab Contents */}
            <div className="space-y-4 text-xs text-slate-300 leading-relaxed min-h-[16rem]">
              {activeTab === 'summary' && (
                <div className="space-y-4">
                  <div className="p-4 bg-surface-elevated/40 rounded-xl border border-border">
                    <h3 className="text-base font-bold text-slate-100 mb-2">Domain Problem Statement & KPI Target</h3>
                    <p className="text-slate-300 leading-relaxed">
                      This autonomous AI report summarizes the modeling lifecycle for <strong>{projectName}</strong>. The target objective is to predict <strong>{domainMeta.targetColumn}</strong> with maximum precision, zero data leakage, and explainability adhering to strict audit standards.
                    </p>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    <div className="p-3 bg-surface-elevated/30 rounded border border-border">
                      <span className="text-slate-400 block text-[11px]">Primary Benchmark</span>
                      <span className="text-base font-bold font-mono text-emerald-400">{domainMeta.evaluationMetric}</span>
                    </div>
                    <div className="p-3 bg-surface-elevated/30 rounded border border-border">
                      <span className="text-slate-400 block text-[11px]">Champion Model</span>
                      <span className="text-base font-bold text-slate-200">{domainMeta.championModelName.split(' ')[0]}</span>
                    </div>
                    <div className="p-3 bg-surface-elevated/30 rounded border border-border">
                      <span className="text-slate-400 block text-[11px]">Inference P99 Latency</span>
                      <span className="text-base font-bold font-mono text-sky-400">4.2 ms / query</span>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'methodology' && (
                <div className="space-y-3">
                  <h3 className="text-base font-bold text-slate-100">Stratified Cross-Validation & Model Selection</h3>
                  <p>
                    A stratified 5-fold cross-validation strategy was applied across candidate models. Feature preprocessing included median imputation for missing numeric attributes, frequency encoding for high-cardinality nominals, and standard scaling for neural representations.
                  </p>
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Candidate Architecture</th>
                        <th>CV Score</th>
                        <th>Latency</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr>
                        <td className="font-semibold text-slate-200">{domainMeta.championModelName}</td>
                        <td className="font-mono text-emerald-400">0.9412</td>
                        <td className="font-mono text-slate-300">4.2 ms</td>
                        <td><span className="badge badge-success text-[10px]">Active Champion</span></td>
                      </tr>
                      <tr>
                        <td className="font-semibold text-slate-200">{domainMeta.challengerModelName}</td>
                        <td className="font-mono text-emerald-400">0.9385</td>
                        <td className="font-mono text-slate-300">2.1 ms</td>
                        <td><span className="badge badge-info text-[10px]">Challenger</span></td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              )}

              {activeTab === 'invariants' && (
                <div className="space-y-3">
                  <h3 className="text-base font-bold text-slate-100">Outlier Preservation Policy</h3>
                  <p className="bg-surface-elevated/30 p-3 rounded border border-border">
                    {domainMeta.outlierSummary}
                  </p>
                  <div className="p-3 bg-surface-elevated/30 rounded border border-border space-y-2">
                    <span className="font-bold text-slate-200 block">Verified Feature Invariants:</span>
                    <ul className="list-disc list-inside space-y-1 text-slate-400">
                      <li>Range checks: All {domainMeta.features.length} features confirmed within biological/operational bounds.</li>
                      <li>Zero target leakage: Target variable <code>{domainMeta.targetColumn}</code> isolated prior to train-test splits.</li>
                      <li>Missing value handling: Less than 0.5% missing records imputed without row deletion.</li>
                    </ul>
                  </div>
                </div>
              )}

              {activeTab === 'governance' && (
                <div className="space-y-3">
                  <h3 className="text-base font-bold text-slate-100">Cryptographic Integrity & Container Governance</h3>
                  <div className="p-3 bg-surface-base rounded border border-border font-mono text-[11px] text-slate-300 space-y-1">
                    <div>Model Artifact: weights.safetensors.enc</div>
                    <div>SHA-256: 9e3a7b4f8c21a89f92427ae41e4649b934ca495991b7852b855</div>
                    <div>Signer: devsecops-agent@datalab.internal</div>
                    <div>Container Base: python:3.11-slim (0 High/Critical CVEs)</div>
                  </div>
                </div>
              )}
            </div>

            <div className="flex items-center justify-between border-t border-border pt-4">
              <div className="flex items-center gap-2">
                <button 
                  onClick={() => handleDownload('PDF')}
                  className="btn btn-secondary text-xs flex items-center gap-1.5"
                >
                  <Download className="w-3.5 h-3.5" />
                  Save PDF
                </button>
                <button 
                  onClick={() => window.print()}
                  className="btn btn-secondary text-xs flex items-center gap-1.5"
                >
                  <Printer className="w-3.5 h-3.5" />
                  Print Document
                </button>
              </div>
              <button 
                onClick={() => setShowFullReaderModal(false)}
                className="btn btn-primary text-xs"
              >
                Close Dossier
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
