/**
 * DataWise AI — App Router
 * All protected routes require authentication via Supabase session.
 */

import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { AppShell } from './components/layout/AppShell';
import { ProtectedRoute } from './components/auth/ProtectedRoute';

// Auth Pages
import { Login }    from './pages/auth/Login';
import { Register } from './pages/auth/Register';

// Workspace Pages
import { Dashboard }              from './pages/Dashboard';
import { ProjectsList }           from './pages/projects/ProjectsList';
import { ProjectDetail }          from './pages/projects/ProjectDetail';
import { NewProject }             from './pages/projects/NewProject';
import { LiveWorkflow }           from './pages/projects/LiveWorkflow';
import { ResultsWorkspace }       from './pages/projects/ResultsWorkspace';
import { PredictionAgent }        from './pages/projects/PredictionAgent';
import { ProjectSectionWorkspace } from './pages/projects/ProjectSectionWorkspace';
import { DatasetWorkspace }       from './pages/datasets/DatasetWorkspace';
import { ExperimentsLab }         from './pages/experiments/ExperimentsLab';
import { PipelineVisualizer }     from './pages/pipelines/PipelineVisualizer';
import { ModelRegistry }          from './pages/models/ModelRegistry';
import { DeploymentManager }      from './pages/deployments/DeploymentManager';
import { MonitoringDashboard }    from './pages/monitoring/MonitoringDashboard';
import { AlertCenter }            from './pages/monitoring/AlertCenter';
import { ReportsCenter }          from './pages/reports/ReportsCenter';
import { NotebooksViewer }        from './pages/notebooks/NotebooksViewer';
import { AIAssistant }            from './pages/assistant/AIAssistant';
import { ConnectionsManager }     from './pages/connections/ConnectionsManager';
import { SettingsView }           from './pages/settings/SettingsView';
import { AdminDashboard }         from './pages/admin/AdminDashboard';
import { QADashboard }            from './pages/admin/QADashboard';

// Legacy compatibility
const LegacyAnalysis = React.lazy(() => import('@/pages/Analysis'));

export default function App() {
  return (
    <React.Suspense fallback={
      <div style={{
        minHeight: '100vh',
        background: 'var(--bg-primary)',
        display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center',
        color: 'var(--text-secondary)',
      }}>
        <div style={{
          width: 32, height: 32,
          border: '2px solid var(--primary)',
          borderTopColor: 'transparent',
          borderRadius: '50%',
          animation: 'spin 0.8s linear infinite',
          marginBottom: 12,
        }} />
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
        <p style={{ fontSize: 12, fontFamily: 'var(--font-mono)' }}>Initializing AI DataLab…</p>
      </div>
    }>
      <Routes>
        {/* ─── Public Routes ──────────────────────────── */}
        <Route path="/login"    element={<Login />} />
        <Route path="/register" element={<Register />} />

        {/* ─── Protected Top-Level Workbench Routes ────── */}
        <Route element={<ProtectedRoute><AppShell /></ProtectedRoute>}>
          <Route path="/dashboard"   element={<Dashboard />} />
          <Route path="/workspace/new" element={<NewProject />} />

          {/* Projects */}
          <Route path="/projects"                                       element={<ProjectsList />} />
          <Route path="/projects/new"                                   element={<NewProject />} />
          <Route path="/projects/:projectId/run/:runId"                 element={<LiveWorkflow />} />
          <Route path="/projects/:projectId/runs/:runId"                element={<LiveWorkflow />} />
          <Route path="/projects/:projectId/results/:runId"             element={<ResultsWorkspace />} />
          <Route path="/projects/:projectId/dataset"                    element={<ProjectSectionWorkspace />} />
          <Route path="/projects/:projectId/eda"                        element={<ProjectSectionWorkspace />} />
          <Route path="/projects/:projectId/preprocessing"              element={<ProjectSectionWorkspace />} />
          <Route path="/projects/:projectId/features"                   element={<ProjectSectionWorkspace />} />
          <Route path="/projects/:projectId/visualizations"             element={<ProjectSectionWorkspace />} />
          <Route path="/projects/:projectId/models"                     element={<ProjectSectionWorkspace />} />
          <Route path="/projects/:projectId/evaluation"                 element={<ProjectSectionWorkspace />} />
          <Route path="/projects/:projectId/model"                      element={<ProjectSectionWorkspace />} />
          <Route path="/projects/:projectId/notebook"                   element={<ProjectSectionWorkspace />} />
          <Route path="/projects/:projectId/notebooks"                  element={<ProjectSectionWorkspace />} />
          <Route path="/projects/:projectId/reports"                    element={<ProjectSectionWorkspace />} />
          <Route path="/projects/:projectId/artifacts"                  element={<ProjectSectionWorkspace />} />
          <Route path="/projects/:projectId/activity"                   element={<ProjectSectionWorkspace />} />
          <Route path="/projects/:projectId/deployment"                 element={<ProjectSectionWorkspace />} />
          <Route path="/projects/:projectId/predict"                    element={<PredictionAgent />} />
          <Route path="/projects/:projectId/monitoring"                 element={<ProjectSectionWorkspace />} />
          <Route path="/projects/:projectId/runs"                       element={<ProjectSectionWorkspace />} />
          <Route path="/projects/:projectId/settings"                   element={<ProjectSectionWorkspace />} />
          <Route path="/projects/:projectId"                            element={<ProjectSectionWorkspace />} />
        </Route>

        {/* ─── Protected /app Sub-routes (legacy compat) ─ */}
        <Route path="/app" element={<ProtectedRoute><AppShell /></ProtectedRoute>}>
          <Route index               element={<Navigate to="/projects" replace />} />
          <Route path="dashboard"    element={<Dashboard />} />
          <Route path="projects"     element={<ProjectsList />} />
          <Route path="projects/new" element={<NewProject />} />
          <Route path="projects/:projectId" element={<ProjectSectionWorkspace />} />
          <Route path="datasets"             element={<DatasetWorkspace />} />
          <Route path="datasets/:datasetId"  element={<DatasetWorkspace />} />
          <Route path="experiments"          element={<ExperimentsLab />} />
          <Route path="pipelines"            element={<PipelineVisualizer />} />
          <Route path="models"               element={<ModelRegistry />} />
          <Route path="deployments"          element={<DeploymentManager />} />
          <Route path="monitoring"           element={<MonitoringDashboard />} />
          <Route path="monitoring/alerts"    element={<AlertCenter />} />
          <Route path="reports"              element={<ReportsCenter />} />
          <Route path="notebooks"            element={<NotebooksViewer />} />
          <Route path="assistant"            element={<AIAssistant />} />
          <Route path="connections"          element={<ConnectionsManager />} />
          <Route path="settings"             element={<SettingsView />} />
          <Route path="settings/:tab"        element={<SettingsView />} />
        </Route>

        {/* ─── Protected Admin Center ──────────────────── */}
        <Route path="/admin" element={<ProtectedRoute><AppShell /></ProtectedRoute>}>
          <Route index              element={<Navigate to="/admin/audit-logs" replace />} />
          <Route path="audit-logs"  element={<AdminDashboard />} />
          <Route path="security"    element={<AdminDashboard />} />
          <Route path="system"      element={<AdminDashboard />} />
          <Route path="qa"          element={<QADashboard />} />
        </Route>

        <Route path="/qa" element={<Navigate to="/admin/qa" replace />} />

        {/* Legacy Analysis Route */}
        <Route path="/analysis/:sessionId" element={<LegacyAnalysis />} />

        {/* Root Fallbacks */}
        <Route path="/"  element={<Navigate to="/login" replace />} />
        <Route path="*"  element={<Navigate to="/login" replace />} />
      </Routes>
    </React.Suspense>
  );
}
