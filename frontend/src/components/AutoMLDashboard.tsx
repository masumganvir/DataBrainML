import React, { useState } from 'react';
import {
  TrendingUp, Award, Clock, CheckCircle2, AlertTriangle, ShieldCheck,
  Zap, HelpCircle, ChevronRight, Play, RefreshCw, BarChart2,
  Sliders, Cpu, FileText, Check, AlertCircle, Info, Sparkles
} from 'lucide-react';
import { mlApi } from '@/services/api';
import type { ModelComparisonResult, TrainingResponse } from '@/types';

interface AutoMLDashboardProps {
  sessionId: string;
  trainingData: TrainingResponse | null;
  onTrainingComplete: (data: TrainingResponse) => void;
  datasetDomain?: string;
  predictionObjective?: string;
  targetColumn?: string;
  taskType?: string;
}

export const AutoMLDashboard: React.FC<AutoMLDashboardProps> = ({
  sessionId,
  trainingData,
  onTrainingComplete,
  datasetDomain,
  predictionObjective,
  targetColumn: initialTarget,
  taskType: initialTask = 'classification',
}) => {
  const [isTraining, setIsTraining] = useState(false);
  const [selectedModel, setSelectedModel] = useState<string | null>(
    trainingData?.selected_final_model || null
  );
  const [targetCol, setTargetCol] = useState(initialTarget || trainingData?.target_column || '');
  const [task, setTask] = useState(initialTask || trainingData?.task_type || 'classification');
  const [cvFolds, setCvFolds] = useState(5);
  const [primaryMetric, setPrimaryMetric] = useState(trainingData?.primary_metric || 'Auto');
  const [activeWhy, setActiveWhy] = useState<{ title: string; content: string } | null>(null);
  const [isSelecting, setIsSelecting] = useState(false);

  const models: ModelComparisonResult[] = trainingData?.models || [];
  const readiness = trainingData?.production_readiness;
  const shift = trainingData?.dataset_shift;
  const featureImportances = trainingData?.feature_importance || {};

  const handleTrain = async () => {
    if (!sessionId) return;
    setIsTraining(true);
    try {
      const resp = await mlApi.train(sessionId, {
        target_column: targetCol || undefined,
        task_type: task,
        primary_metric: primaryMetric === 'Auto' ? undefined : primaryMetric,
        cv_folds: cvFolds,
      });
      onTrainingComplete(resp);
      setSelectedModel(resp.selected_final_model);
    } catch (err: any) {
      console.error('Training failed:', err);
      alert(`Model training error: ${err.message}`);
    } finally {
      setIsTraining(false);
    }
  };

  const handleSelectModel = async (modelName: string) => {
    if (!sessionId || isSelecting) return;
    setIsSelecting(true);
    try {
      await mlApi.selectModel(sessionId, modelName, `User manually selected ${modelName} as the production champion`);
      setSelectedModel(modelName);
      if (trainingData) {
        const updated = {
          ...trainingData,
          selected_final_model: modelName,
          models: trainingData.models.map(m => ({
            ...m,
            is_champion: m.model_name === modelName,
            is_selected: m.model_name === modelName,
          })),
        };
        onTrainingComplete(updated);
      }
    } catch (err: any) {
      alert(`Failed to select model: ${err.message}`);
    } finally {
      setIsSelecting(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', paddingBottom: '32px' }}>
      {/* ── Top Strategy & Configuration Banner ── */}
      <div className="glass-card" style={{
        padding: '24px',
        border: '1px solid rgba(99, 102, 241, 0.25)',
        background: 'linear-gradient(180deg, rgba(99, 102, 241, 0.06) 0%, rgba(9, 13, 22, 0.6) 100%)',
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px', marginBottom: '20px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
              <Sparkles size={18} color="#818cf8" />
              <h2 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 700, color: '#f8fafc' }}>
                Automated ML & Model Selection Engine
              </h2>
            </div>
            <p style={{ margin: 0, fontSize: '0.85rem', color: '#94a3b8' }}>
              Leak-free training pipeline: train/test split strictly preceding preprocessing, K-Fold cross-validation, and multi-factor selection.
            </p>
          </div>

          <div style={{ display: 'flex', gap: '10px' }}>
            <button
              onClick={handleTrain}
              disabled={isTraining}
              className="btn btn-primary"
              style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '10px 18px', fontWeight: 600 }}
            >
              {isTraining ? (
                <>
                  <RefreshCw size={15} style={{ animation: 'spin 1s linear infinite' }} />
                  Training Models…
                </>
              ) : (
                <>
                  <Play size={15} />
                  {models.length > 0 ? 'Retrain Models' : 'Train Candidate Models'}
                </>
              )}
            </button>
          </div>
        </div>

        {/* Configuration Row */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
          gap: '12px',
          padding: '16px',
          background: 'rgba(0, 0, 0, 0.25)',
          borderRadius: '10px',
          border: '1px solid rgba(255, 255, 255, 0.05)',
        }}>
          <div>
            <label style={{ display: 'block', fontSize: '0.7rem', fontWeight: 600, color: '#94a3b8', marginBottom: '4px', textTransform: 'uppercase' }}>
              Target Column
            </label>
            <input
              type="text"
              value={targetCol}
              onChange={e => setTargetCol(e.target.value)}
              placeholder="e.g. is_churn, is_fraud"
              style={{
                width: '100%',
                padding: '6px 10px',
                borderRadius: '6px',
                background: 'rgba(255, 255, 255, 0.05)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                color: '#fff',
                fontSize: '0.8rem',
              }}
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.7rem', fontWeight: 600, color: '#94a3b8', marginBottom: '4px', textTransform: 'uppercase' }}>
              Task Type
            </label>
            <select
              value={task}
              onChange={e => setTask(e.target.value)}
              style={{
                width: '100%',
                padding: '6px 10px',
                borderRadius: '6px',
                background: 'rgba(255, 255, 255, 0.05)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                color: '#fff',
                fontSize: '0.8rem',
              }}
            >
              <option value="classification">Classification</option>
              <option value="regression">Regression</option>
            </select>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.7rem', fontWeight: 600, color: '#94a3b8', marginBottom: '4px', textTransform: 'uppercase' }}>
              Evaluation Metric
            </label>
            <select
              value={primaryMetric}
              onChange={e => setPrimaryMetric(e.target.value)}
              style={{
                width: '100%',
                padding: '6px 10px',
                borderRadius: '6px',
                background: 'rgba(255, 255, 255, 0.05)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                color: '#fff',
                fontSize: '0.8rem',
              }}
            >
              <option value="Auto">Auto (Context-Aware)</option>
              {task === 'classification' ? (
                <>
                  <option value="PR-AUC">PR-AUC (Imbalanced Data)</option>
                  <option value="ROC-AUC">ROC-AUC</option>
                  <option value="Weighted F1">Weighted F1</option>
                  <option value="Accuracy">Accuracy</option>
                </>
              ) : (
                <>
                  <option value="RMSE">RMSE (Root Mean Squared)</option>
                  <option value="MAE">MAE (Mean Absolute)</option>
                  <option value="R2">R² Score</option>
                </>
              )}
            </select>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.7rem', fontWeight: 600, color: '#94a3b8', marginBottom: '4px', textTransform: 'uppercase' }}>
              Cross-Validation Folds
            </label>
            <select
              value={cvFolds}
              onChange={e => setCvFolds(Number(e.target.value))}
              style={{
                width: '100%',
                padding: '6px 10px',
                borderRadius: '6px',
                background: 'rgba(255, 255, 255, 0.05)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                color: '#fff',
                fontSize: '0.8rem',
              }}
            >
              <option value={3}>3-Fold CV</option>
              <option value={5}>5-Fold CV (Recommended)</option>
              <option value={10}>10-Fold CV</option>
            </select>
          </div>
        </div>
      </div>

      {/* ── Model Comparison Table (Prompt Section 23) ── */}
      {models.length > 0 ? (
        <div className="glass-card" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <div>
              <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 700, color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <TrendingUp size={18} color="#818cf8" />
                Model Comparison Dashboard
              </h3>
              <p style={{ margin: '4px 0 0', fontSize: '0.8rem', color: '#94a3b8' }}>
                Primary Objective: <strong style={{ color: '#818cf8' }}>{trainingData?.primary_metric}</strong> via {trainingData?.cv_strategy}
              </p>
            </div>

            <button
              onClick={() => setActiveWhy({
                title: `Why ${trainingData?.primary_metric} was chosen as Primary Metric`,
                content: `Evaluation metric selection depends strictly on the ML objective and class balance. In imbalanced tasks (e.g. fraud, churn), high accuracy is deceptive because a trivial model predicting only the majority class achieves inflated scores. PR-AUC and F1 isolate minority-class retrieval performance.`,
              })}
              style={{
                background: 'rgba(99, 102, 241, 0.1)',
                border: '1px solid rgba(99, 102, 241, 0.3)',
                color: '#c7d2fe',
                borderRadius: '6px',
                padding: '5px 10px',
                fontSize: '0.75rem',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
              }}
            >
              <HelpCircle size={12} />
              Why this metric?
            </button>
          </div>

          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.1)', color: '#94a3b8', textAlign: 'left' }}>
                  <th style={{ padding: '12px' }}>Model</th>
                  <th style={{ padding: '12px' }}>Architecture</th>
                  <th style={{ padding: '12px', textAlign: 'right' }}>CV Score (Mean ± Std)</th>
                  <th style={{ padding: '12px', textAlign: 'right' }}>Hold-Out Test Score</th>
                  <th style={{ padding: '12px', textAlign: 'right' }}>Training Time</th>
                  <th style={{ padding: '12px', textAlign: 'center' }}>Role</th>
                  <th style={{ padding: '12px', textAlign: 'right' }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {models.map((m) => {
                  const isChamp = m.model_name === selectedModel;
                  return (
                    <tr
                      key={m.model_name}
                      style={{
                        borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
                        background: isChamp ? 'rgba(99, 102, 241, 0.08)' : 'transparent',
                        transition: 'background 0.15s',
                      }}
                    >
                      <td style={{ padding: '12px', fontWeight: 600, color: isChamp ? '#c7d2fe' : '#e2e8f0' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          {isChamp && <Award size={15} color="#fbbf24" />}
                          {m.model_name}
                        </div>
                      </td>
                      <td style={{ padding: '12px', color: '#94a3b8', fontSize: '0.78rem' }}>
                        {m.model_class}
                      </td>
                      <td style={{ padding: '12px', textAlign: 'right', fontWeight: 600, color: '#f8fafc' }}>
                        {m.cv_mean.toFixed(4)} <span style={{ color: '#64748b', fontSize: '0.75rem' }}>± {m.cv_std.toFixed(4)}</span>
                      </td>
                      <td style={{ padding: '12px', textAlign: 'right', fontWeight: 700, color: isChamp ? '#34d399' : '#cbd5e1' }}>
                        {m.test_metrics?.[trainingData?.primary_metric || ''] !== undefined
                          ? m.test_metrics[trainingData!.primary_metric].toFixed(4)
                          : Object.values(m.test_metrics || {})[0]?.toFixed(4) || 'N/A'}
                      </td>
                      <td style={{ padding: '12px', textAlign: 'right', color: '#94a3b8' }}>
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '4px' }}>
                          <Clock size={12} color="#64748b" />
                          {m.training_time_seconds.toFixed(2)}s
                        </div>
                      </td>
                      <td style={{ padding: '12px', textAlign: 'center' }}>
                        {isChamp ? (
                          <span style={{
                            padding: '3px 8px',
                            borderRadius: '12px',
                            background: 'rgba(245, 158, 11, 0.15)',
                            border: '1px solid rgba(245, 158, 11, 0.4)',
                            color: '#fbbf24',
                            fontSize: '0.72rem',
                            fontWeight: 700,
                          }}>
                            Production Champion
                          </span>
                        ) : (
                          <span style={{ color: '#64748b', fontSize: '0.72rem' }}>Candidate</span>
                        )}
                      </td>
                      <td style={{ padding: '12px', textAlign: 'right' }}>
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '6px' }}>
                          <button
                            onClick={() => setActiveWhy({
                              title: `Model Evaluation: ${m.model_name}`,
                              content: m.selection_rationale ||
                                `Architecture: ${m.model_class}. CV Score: ${m.cv_mean} ± ${m.cv_std}. Test metrics: ${JSON.stringify(m.test_metrics, null, 2)}. Fitted strictly inside a leak-free ColumnTransformer pipeline.`,
                            })}
                            style={{
                              background: 'none',
                              border: 'none',
                              color: '#818cf8',
                              cursor: 'pointer',
                              padding: '4px',
                            }}
                            title="Explain this model"
                          >
                            <HelpCircle size={14} />
                          </button>

                          {!isChamp && (
                            <button
                              onClick={() => handleSelectModel(m.model_name)}
                              disabled={isSelecting}
                              className="btn btn-outline btn-sm"
                              style={{ padding: '4px 8px', fontSize: '0.72rem' }}
                            >
                              Select as Champion
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Champion Rationale Card (Section 24) */}
          <div style={{
            marginTop: '20px',
            padding: '16px',
            borderRadius: '10px',
            background: 'rgba(99, 102, 241, 0.08)',
            border: '1px solid rgba(99, 102, 241, 0.2)',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
              <Award size={16} color="#fbbf24" />
              <strong style={{ fontSize: '0.85rem', color: '#c7d2fe' }}>
                Multi-Factor Selection Rationale for {selectedModel}
              </strong>
            </div>
            <p style={{ margin: 0, fontSize: '0.8rem', color: '#cbd5e1', lineHeight: 1.5 }}>
              {trainingData?.selection_rationale ||
                `Model selected based on optimal cross-validation score under primary metric ${trainingData?.primary_metric}, generalizability on hold-out test split, and variance stability across CV partitions.`}
            </p>
          </div>
        </div>
      ) : (
        <div className="glass-card" style={{ padding: '48px 24px', textAlign: 'center' }}>
          <Cpu size={48} color="#818cf8" style={{ opacity: 0.4, margin: '0 auto 16px' }} />
          <h3 style={{ margin: '0 0 8px', fontSize: '1.1rem', color: '#f8fafc' }}>
            No models trained yet
          </h3>
          <p style={{ margin: '0 0 20px', fontSize: '0.85rem', color: '#94a3b8', maxWidth: '460px', marginLeft: 'auto', marginRight: 'auto' }}>
            Configure your target column and click "Train Candidate Models" to execute leak-free cross-validation and compare multiple architectures.
          </p>
          <button
            onClick={handleTrain}
            disabled={isTraining}
            className="btn btn-primary"
            style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}
          >
            <Play size={14} />
            Train Candidate Models
          </button>
        </div>
      )}

      {/* ── Feature Importance & Permutation Importance (Section 35) ── */}
      {Object.keys(featureImportances).length > 0 && (
        <div className="glass-card" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 700, color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <BarChart2 size={18} color="#818cf8" />
              Feature Importance & Predictive Signal
            </h3>
            <button
              onClick={() => setActiveWhy({
                title: 'Understanding Feature Importance',
                content: 'Feature importances quantify how much each variable contributes to reducing uncertainty or error in the champion model. Higher values indicate critical predictive drivers.',
              })}
              style={{ background: 'none', border: 'none', color: '#818cf8', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.75rem' }}
            >
              <HelpCircle size={12} />
              [Why?]
            </button>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {Object.entries(featureImportances).slice(0, 10).map(([feat, score]) => {
              const maxScore = Math.max(...Object.values(featureImportances), 0.001);
              const pct = Math.min(100, Math.round((score / maxScore) * 100));
              return (
                <div key={feat} style={{ display: 'flex', alignItems: 'center', gap: '12px', fontSize: '0.8rem' }}>
                  <span style={{ width: '160px', color: '#cbd5e1', fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {feat}
                  </span>
                  <div style={{ flex: 1, height: '8px', background: 'rgba(255, 255, 255, 0.05)', borderRadius: '4px', overflow: 'hidden' }}>
                    <div style={{ width: `${pct}%`, height: '100%', background: 'linear-gradient(90deg, #6366f1, #34d399)', borderRadius: '4px' }} />
                  </div>
                  <span style={{ width: '60px', textAlign: 'right', color: '#94a3b8', fontSize: '0.75rem', fontWeight: 600 }}>
                    {score.toFixed(4)}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* ── Covariate Shift Check (Section 37) ── */}
      {shift && (
        <div className="glass-card" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
            {shift.has_distribution_shift ? (
              <AlertTriangle size={18} color="#fbbf24" />
            ) : (
              <CheckCircle2 size={18} color="#34d399" />
            )}
            <h3 style={{ margin: 0, fontSize: '1.05rem', fontWeight: 700, color: '#f8fafc' }}>
              Dataset Distribution Shift Analysis (KS-Test)
            </h3>
          </div>
          <p style={{ margin: '0 0 14px', fontSize: '0.82rem', color: '#94a3b8' }}>
            {shift.has_distribution_shift
              ? '⚠️ Potential distribution drift detected between training partition and hold-out test set. Review shifted features below.'
              : '✅ No statistically significant covariate shift detected (Kolmogorov-Smirnov p > 0.05 across numerical predictors).'}
          </p>

          {shift.numerical_shifts && shift.numerical_shifts.length > 0 && (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
              {shift.numerical_shifts.map(s => (
                <div
                  key={s.feature}
                  style={{
                    padding: '6px 12px',
                    borderRadius: '8px',
                    background: s.status === 'SHIFT_DETECTED' ? 'rgba(245, 158, 11, 0.1)' : 'rgba(255, 255, 255, 0.03)',
                    border: s.status === 'SHIFT_DETECTED' ? '1px solid rgba(245, 158, 11, 0.3)' : '1px solid rgba(255, 255, 255, 0.06)',
                    fontSize: '0.75rem',
                    color: s.status === 'SHIFT_DETECTED' ? '#fbbf24' : '#cbd5e1',
                  }}
                >
                  <strong>{s.feature}</strong>: p={s.p_value.toFixed(3)} ({s.status})
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ── 8-Point Production Readiness Audit (Section 38) ── */}
      {readiness && (
        <div className="glass-card" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <div>
              <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 700, color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <ShieldCheck size={18} color="#34d399" />
                Production Readiness Audit
              </h3>
              <p style={{ margin: '4px 0 0', fontSize: '0.8rem', color: '#94a3b8' }}>
                Automated 8-point deployment integrity verification
              </p>
            </div>

            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '6px 14px',
              borderRadius: '20px',
              background: readiness.status === 'PASS' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(245, 158, 11, 0.15)',
              border: readiness.status === 'PASS' ? '1px solid #10b981' : '1px solid #f59e0b',
              color: readiness.status === 'PASS' ? '#34d399' : '#fbbf24',
              fontWeight: 800,
              fontSize: '0.85rem',
            }}>
              <span>Status: {readiness.status}</span>
              <span style={{ fontSize: '0.75rem', opacity: 0.8 }}>({readiness.readiness_score}/100)</span>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '10px' }}>
            {readiness.checklist.map((item, idx) => (
              <div
                key={idx}
                style={{
                  padding: '12px',
                  borderRadius: '8px',
                  background: item.passed ? 'rgba(16, 185, 129, 0.05)' : 'rgba(245, 158, 11, 0.05)',
                  border: item.passed ? '1px solid rgba(16, 185, 129, 0.2)' : '1px solid rgba(245, 158, 11, 0.2)',
                  display: 'flex',
                  gap: '10px',
                  alignItems: 'flex-start',
                }}
              >
                {item.passed ? (
                  <CheckCircle2 size={16} color="#34d399" style={{ flexShrink: 0, marginTop: '2px' }} />
                ) : (
                  <AlertCircle size={16} color="#fbbf24" style={{ flexShrink: 0, marginTop: '2px' }} />
                )}
                <div>
                  <div style={{ fontSize: '0.8rem', fontWeight: 600, color: item.passed ? '#f8fafc' : '#fbbf24', marginBottom: '2px' }}>
                    {item.check}
                  </div>
                  <div style={{ fontSize: '0.72rem', color: '#94a3b8', lineHeight: 1.4 }}>
                    {item.detail}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Limitations Section (Section 36) ── */}
      {trainingData?.limitations && trainingData.limitations.length > 0 && (
        <div className="glass-card" style={{ padding: '24px', borderColor: 'rgba(148, 163, 184, 0.15)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
            <Info size={16} color="#94a3b8" />
            <h3 style={{ margin: 0, fontSize: '1rem', fontWeight: 700, color: '#f8fafc' }}>
              Scientifically Grounded Model Limitations
            </h3>
          </div>
          <ul style={{ margin: 0, paddingLeft: '20px', fontSize: '0.8rem', color: '#94a3b8', lineHeight: 1.6 }}>
            {trainingData.limitations.map((lim, i) => (
              <li key={i}>{lim}</li>
            ))}
          </ul>
        </div>
      )}

      {/* ── Interactive [Why?] Rationale Modal (Section 31 & 46) ── */}
      {activeWhy && (
        <div style={{
          position: 'fixed',
          inset: 0,
          zIndex: 110,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: 'rgba(0, 0, 0, 0.7)',
          backdropFilter: 'blur(6px)',
          padding: '16px',
        }}>
          <div style={{
            background: '#0f172a',
            border: '1px solid rgba(99, 102, 241, 0.4)',
            borderRadius: '14px',
            width: '100%',
            maxWidth: '500px',
            padding: '24px',
            boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.7)',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Sparkles size={16} color="#818cf8" />
                <h4 style={{ margin: 0, fontSize: '1rem', fontWeight: 700, color: '#f8fafc' }}>
                  {activeWhy.title}
                </h4>
              </div>
              <button
                onClick={() => setActiveWhy(null)}
                style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer' }}
              >
                ✕
              </button>
            </div>
            <p style={{ fontSize: '0.85rem', color: '#cbd5e1', lineHeight: 1.6, margin: '0 0 20px', whiteSpace: 'pre-wrap' }}>
              {activeWhy.content}
            </p>
            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <button
                className="btn btn-primary btn-sm"
                onClick={() => setActiveWhy(null)}
              >
                Understood
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
