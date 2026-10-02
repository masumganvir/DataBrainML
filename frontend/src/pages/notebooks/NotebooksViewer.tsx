import React, { useState } from 'react';
import { 
  BookOpen, Download, Terminal, Play, CheckCircle2, 
  Layers, Code, FileCode2, Copy, Check
} from 'lucide-react';
import { useAuthStore } from '../../services/authStore';

interface NotebookCell {
  id: string;
  type: 'markdown' | 'code';
  content: string;
  output?: string;
}

const NOTEBOOK_SECTIONS: { id: string; title: string; cells: NotebookCell[] }[] = [
  {
    id: 'sec-eda',
    title: '1. Ingestion & EDA',
    cells: [
      {
        id: 'cell-1',
        type: 'markdown',
        content: '### Section 1: Data Ingestion and Statistical Profiling\nWe load the validated dataset and inspect quantile distributions and missingness invariants.'
      },
      {
        id: 'cell-2',
        type: 'code',
        content: `import pandas as pd
import numpy as np

# Load validated dataset
df = pd.read_csv('churn_data_clean.csv')
print(f"Dataset shape: {df.shape}")
print(df.info())`,
        output: `<class 'pandas.core.frame.DataFrame'>
RangeIndex: 7043 entries, 0 to 7042
Data columns (total 21 columns):
 #   Column            Non-Null Count  Dtype  
---  ------            --------------  -----  
 0   customerID        7043 non-null   object 
 1   gender            7043 non-null   object 
 2   SeniorCitizen     7043 non-null   int64  
 3   Partner           7043 non-null   object 
 4   Dependents        7043 non-null   object 
 5   tenure            7043 non-null   int64  
 6   MonthlyCharges    7043 non-null   float64
 7   TotalCharges      7032 non-null   float64
 8   Churn             7043 non-null   object 
dtypes: float64(2), int64(2), object(17)`
      }
    ]
  },
  {
    id: 'sec-prep',
    title: '2. Preprocessing & Outliers',
    cells: [
      {
        id: 'cell-3',
        type: 'markdown',
        content: '### Section 2: Non-Destructive Outlier Handling & Encoding\nOutlier detection identified 14 extreme account balances. By domain policy, they are preserved with a boolean flag.'
      },
      {
        id: 'cell-4',
        type: 'code',
        content: `# Verify non-destructive outlier retention
q99 = df['MonthlyCharges'].quantile(0.99)
print(f"99th percentile threshold: \${q99:.2f}")
outliers = df[df['MonthlyCharges'] > q99]
print(f"Preserved high-value customer records: {len(outliers)}")
# Impute missing TotalCharges with median
df['TotalCharges'] = df['TotalCharges'].fillna(df['TotalCharges'].median())`,
        output: `99th percentile threshold: $114.80
Preserved high-value customer records: 14
Missing values resolved. Total non-null records: 7043`
      }
    ]
  },
  {
    id: 'sec-model',
    title: '3. Model Training & Evaluation',
    cells: [
      {
        id: 'cell-5',
        type: 'markdown',
        content: '### Section 3: XGBoost Champion Model Fitting & Cross-Validation'
      },
      {
        id: 'cell-6',
        type: 'code',
        content: `from xgboost import XGBClassifier
from sklearn.model_selection import StratifiedKFold, cross_val_score

model = XGBClassifier(
    learning_rate=0.042,
    max_depth=6,
    n_estimators=280,
    random_state=42
)

# Stratified 5-Fold Evaluation
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
scores = cross_val_score(model, X_train, y_train, cv=cv, scoring='f1')
print(f"5-Fold CV Mean F1-Score: {scores.mean():.4f} (+/- {scores.std():.4f})")`,
        output: `5-Fold CV Mean F1-Score: 0.9082 (+/- 0.0084)
Test Holdout Evaluation: ROC-AUC 0.9741, Precision 0.9230, Recall 0.8940`
      }
    ]
  }
];

export const NotebooksViewer: React.FC = () => {
  const { activeProject } = useAuthStore();
  const [activeTab, setActiveTab] = useState<string>('sec-eda');
  const [copiedCell, setCopiedCell] = useState<string | null>(null);

  const activeSection = NOTEBOOK_SECTIONS.find(s => s.id === activeTab) || NOTEBOOK_SECTIONS[0];

  const handleCopyCode = (cellId: string, code: string) => {
    navigator.clipboard.writeText(code);
    setCopiedCell(cellId);
    setTimeout(() => setCopiedCell(null), 2000);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400">
              <BookOpen className="w-5 h-5" />
            </span>
            <h1 className="text-2xl font-bold tracking-tight">Generated Jupyter Notebooks</h1>
            <span className="badge badge-success text-xs font-mono">v1.4.0-reproducible.ipynb</span>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Deterministic, standalone Jupyter notebook replicating all steps for <strong className="text-slate-200">{activeProject?.name || 'Customer Churn Prevention'}</strong>
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button 
            onClick={() => alert('Downloading notebook (.ipynb)...')}
            className="btn btn-primary text-xs flex items-center gap-1.5"
          >
            <Download className="w-3.5 h-3.5" />
            Download Notebook (.ipynb)
          </button>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex items-center gap-2 border-b border-border pb-2 overflow-x-auto">
        {NOTEBOOK_SECTIONS.map((sec) => (
          <button
            key={sec.id}
            onClick={() => setActiveTab(sec.id)}
            className={`px-3 py-1.5 text-xs rounded-lg font-medium transition-colors ${
              activeTab === sec.id
                ? 'bg-primary text-white'
                : 'text-slate-400 hover:text-slate-200 hover:bg-surface-elevated'
            }`}
          >
            {sec.title}
          </button>
        ))}
      </div>

      {/* Cells List */}
      <div className="space-y-4">
        {activeSection.cells.map((cell) => (
          <div key={cell.id} className="panel overflow-hidden">
            {cell.type === 'markdown' ? (
              <div className="p-4 bg-surface/50 text-xs text-slate-300 leading-relaxed border-l-4 border-l-primary">
                <div className="font-semibold text-sm text-slate-100 mb-1">{cell.content.split('\n')[0]}</div>
                <p className="text-slate-400">{cell.content.split('\n').slice(1).join('\n')}</p>
              </div>
            ) : (
              <div className="flex flex-col">
                <div className="bg-slate-950 p-2.5 px-4 border-b border-slate-800 flex items-center justify-between">
                  <div className="flex items-center gap-2 text-slate-400 text-xs font-mono">
                    <Code className="w-3.5 h-3.5 text-primary-light" />
                    <span>In [ ]: Python 3.11 (Isolated Kernel)</span>
                  </div>
                  <button
                    onClick={() => handleCopyCode(cell.id, cell.content)}
                    className="text-slate-400 hover:text-slate-200 text-xs flex items-center gap-1 transition-colors"
                  >
                    {copiedCell === cell.id ? (
                      <Check className="w-3.5 h-3.5 text-emerald-400" />
                    ) : (
                      <Copy className="w-3.5 h-3.5" />
                    )}
                    <span className="text-[11px]">{copiedCell === cell.id ? 'Copied' : 'Copy'}</span>
                  </button>
                </div>

                <div className="p-4 bg-slate-950/80 font-mono text-xs text-slate-200 overflow-x-auto whitespace-pre leading-relaxed">
                  {cell.content}
                </div>

                {cell.output && (
                  <div className="bg-slate-900/60 p-4 border-t border-slate-800/80">
                    <div className="text-[11px] font-mono text-slate-500 mb-1">Out [ ]:</div>
                    <div className="font-mono text-xs text-slate-300 overflow-x-auto whitespace-pre leading-relaxed">
                      {cell.output}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
