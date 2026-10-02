import React, { useState } from 'react';
import { 
  FileText, Download, Eye, CheckCircle2, ShieldCheck, 
  ExternalLink, BarChart3, Clock, Sparkles
} from 'lucide-react';
import { useAuthStore } from '../../services/authStore';

interface ReportDoc {
  id: string;
  title: string;
  type: 'EXECUTIVE_ML' | 'DATA_QUALITY' | 'DEPLOYMENT_AUDIT';
  author: string;
  generatedAt: string;
  pages: number;
  summary: string;
}

const REPORTS: ReportDoc[] = [
  {
    id: 'rep-exec-01',
    title: 'Customer Churn AutoML Executive Technical Summary',
    type: 'EXECUTIVE_ML',
    author: 'Autonomous Report Agent',
    generatedAt: '2026-09-30 09:30 UTC',
    pages: 14,
    summary: 'Comprehensive analysis of 5 evaluated ML architectures. Details why XGBoost was selected as Champion with F1: 0.9082 and ROC-AUC: 0.9741.'
  },
  {
    id: 'rep-data-02',
    title: 'Data Quality & Invariant Verification Dossier',
    type: 'DATA_QUALITY',
    author: 'Dataset Profiler Agent',
    generatedAt: '2026-09-30 09:12 UTC',
    pages: 8,
    summary: 'Documenting 100% preservation of legitimate account balance outliers, median imputation for TotalCharges, and target encoding validation.'
  },
  {
    id: 'rep-deploy-03',
    title: 'Production Model Governance & Security Compliance',
    type: 'DEPLOYMENT_AUDIT',
    author: 'DevSecOps & MLOps Agent',
    generatedAt: '2026-09-30 09:25 UTC',
    pages: 6,
    summary: 'SHA-256 weight integrity hash checks, P99 latency benchmarks, container security scan results (0 CVEs), and drift threshold configurations.'
  }
];

export const ReportsCenter: React.FC = () => {
  const { activeProject } = useAuthStore();
  const [reports] = useState<ReportDoc[]>(REPORTS);
  const [selectedReport, setSelectedReport] = useState<ReportDoc>(REPORTS[0]);

  const handleDownload = (format: 'PDF' | 'HTML' | 'MD') => {
    alert(`Downloading ${selectedReport.title} as ${format}...`);
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
            <h1 className="text-2xl font-bold tracking-tight">Report Center</h1>
            <span className="badge badge-success text-xs">3 Published Reports</span>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Audit-ready technical documentation, governance dossiers, and executive summaries for <strong className="text-slate-200">{activeProject?.name || 'Customer Churn Prevention'}</strong>
          </p>
        </div>

        <div className="flex items-center gap-2">
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
          <div className="border-b border-border pb-4">
            <div className="flex items-center justify-between">
              <span className="badge badge-success text-xs flex items-center gap-1">
                <ShieldCheck className="w-3.5 h-3.5" /> Verified Technical Dossier
              </span>
              <span className="text-xs text-slate-500 font-mono">ID: {selectedReport.id}</span>
            </div>
            <h2 className="text-xl font-bold text-slate-100 mt-2">{selectedReport.title}</h2>
            <p className="text-xs text-slate-400 mt-1">
              Generated by {selectedReport.author} on {selectedReport.generatedAt}
            </p>
          </div>

          {/* Structured Document Content Simulation */}
          <div className="space-y-4 text-xs text-slate-300 leading-relaxed bg-surface-elevated/40 p-5 rounded-xl border border-border">
            <section>
              <h4 className="font-bold text-sm text-slate-100 mb-1 flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-primary-light" />
                1. Executive Summary & Problem Formulation
              </h4>
              <p>
                The objective of this pipeline run is to deterministically forecast customer churn risk across 7,043 telecom subscribers using stratified 5-fold cross-validation. The project established a multi-model benchmark evaluating Gradient Boosted Trees and deep neural nets.
              </p>
            </section>

            <section>
              <h4 className="font-bold text-sm text-slate-100 mb-1 flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-emerald-400" />
                2. Model Performance Benchmark Leaderboard
              </h4>
              <p>
                XGBoost achieved the highest validation F1-score of <strong>0.9082</strong> and ROC-AUC of <strong>0.9741</strong> with an average inference latency of <strong>4.2ms</strong>. LightGBM demonstrated faster inference at 2.1ms with a marginal score difference (F1: 0.9003).
              </p>
            </section>

            <section>
              <h4 className="font-bold text-sm text-slate-100 mb-1 flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-sky-400" />
                3. Governance, Invariants, & Explainability
              </h4>
              <p>
                All 14 extreme account balance values ($115+) were proven to be legitimate customer subscriptions and preserved without data distortion. Global TreeSHAP feature attributions show that ContractType (Month-to-Month) and MonthlyCharges dominate 52% of the decision boundary.
              </p>
            </section>
          </div>

          <div className="flex items-center justify-between text-xs text-slate-400 border-t border-border pt-4">
            <span className="flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              Cryptographic signature valid
            </span>
            <span>Page 1 of {selectedReport.pages}</span>
          </div>
        </div>
      </div>
    </div>
  );
};
