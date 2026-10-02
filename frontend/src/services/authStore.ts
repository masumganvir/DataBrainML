/**
 * AI DataLab — Authentication, Multi-Tenancy & Project State Store
 * Controls active user session, organization, project context, and theme.
 */

import { UserProfile, Project } from '../types'

export interface AuthState {
  user: UserProfile | null
  token: string | null
  isAuthenticated: boolean
  currentProject: Project | null
  activeProjects: Project[]
  theme: 'dark' | 'light' | 'system'
  isOnline: boolean
  notificationsCount: number
}

const STORAGE_KEY_AUTH = 'datalab_auth_state'
const STORAGE_KEY_PROJECT = 'datalab_active_project'
const STORAGE_KEY_THEME = 'datalab_theme'

// Default Demo User for zero-friction exploration
const DEFAULT_USER: UserProfile = {
  id: 'usr_enterprise_01',
  email: 'lead.scientist@datalab.ai',
  name: 'Dr. Elena Rostova',
  role: 'data_scientist',
  organization_id: 'org_acme_analytics',
  organization_name: 'Acme Predictive Labs',
  mfa_enabled: true,
  created_at: new Date().toISOString(),
}

export const DEMO_PROJECTS: Project[] = [
  {
    id: 'proj_churn_prod',
    name: 'Customer Churn Predictor',
    description: 'High-throughput customer retention & churn likelihood scoring pipeline with LightGBM.',
    created_at: '2026-09-15T10:00:00Z',
    updated_at: '2026-09-30T12:00:00Z',
    dataset_count: 3,
    experiment_count: 8,
    model_count: 4,
    active_deployment: true,
    status: 'active',
    current_champion_model: 'LightGBM Classifier (v2.1.0)',
    tags: ['Production', 'Customer Analytics', 'High Priority'],
  },
  {
    id: 'proj_fraud_shield',
    name: 'Realtime Fraud Shield',
    description: 'Extreme-value preservation and fraud anomaly detection using PyTorch autoencoder and XGBoost.',
    created_at: '2026-09-20T08:30:00Z',
    updated_at: '2026-09-29T16:45:00Z',
    dataset_count: 2,
    experiment_count: 14,
    model_count: 6,
    active_deployment: true,
    status: 'active',
    current_champion_model: 'Hybrid PyTorch-XGBoost (v1.4.0)',
    tags: ['Security', 'Risk', 'Streaming'],
  },
  {
    id: 'proj_ltv_forecasting',
    name: 'E-Commerce LTV Forecaster',
    description: 'Customer lifetime value regression using CatBoost and feature interaction cross-terms.',
    created_at: '2026-09-25T14:15:00Z',
    updated_at: '2026-09-30T11:20:00Z',
    dataset_count: 1,
    experiment_count: 5,
    model_count: 2,
    active_deployment: false,
    status: 'training',
    current_champion_model: 'CatBoost Regressor (v0.9.1)',
    tags: ['Revenue', 'Experimental'],
  },
]

class AuthStore {
  private state: AuthState
  private listeners: Set<() => void> = new Set()

  constructor() {
    const savedToken = localStorage.getItem(STORAGE_KEY_AUTH)
    const savedProject = localStorage.getItem(STORAGE_KEY_PROJECT)
    const savedTheme = (localStorage.getItem(STORAGE_KEY_THEME) as 'dark' | 'light' | 'system') || 'dark'

    const activeProject = savedProject
      ? JSON.parse(savedProject)
      : DEMO_PROJECTS[0]

    this.state = {
      user: savedToken ? DEFAULT_USER : DEFAULT_USER, // Pre-authenticated for seamless desktop UX
      token: savedToken || 'jwt_demo_token_authenticated',
      isAuthenticated: true,
      currentProject: activeProject,
      activeProjects: DEMO_PROJECTS,
      theme: savedTheme,
      isOnline: navigator.onLine,
      notificationsCount: 3,
    }

    window.addEventListener('online', () => this.setOnline(true))
    window.addEventListener('offline', () => this.setOnline(false))
    this.applyTheme(savedTheme)
  }

  public getState(): AuthState {
    return this.state
  }

  public subscribe(listener: () => void): () => void {
    this.listeners.add(listener)
    return () => this.listeners.delete(listener)
  }

  private notify(): void {
    this.listeners.forEach((l) => l())
  }

  public login(user: UserProfile, token: string): void {
    this.state.user = user
    this.state.token = token
    this.state.isAuthenticated = true
    localStorage.setItem(STORAGE_KEY_AUTH, token)
    this.notify()
  }

  public logout(): void {
    this.state.user = null
    this.state.token = null
    this.state.isAuthenticated = false
    localStorage.removeItem(STORAGE_KEY_AUTH)
    this.notify()
  }

  public setCurrentProject(project: Project): void {
    this.state.currentProject = project
    localStorage.setItem(STORAGE_KEY_PROJECT, JSON.stringify(project))
    this.notify()
  }

  public setTheme(theme: 'dark' | 'light' | 'system'): void {
    this.state.theme = theme
    localStorage.setItem(STORAGE_KEY_THEME, theme)
    this.applyTheme(theme)
    this.notify()
  }

  private applyTheme(theme: 'dark' | 'light' | 'system'): void {
    const effectiveTheme =
      theme === 'system'
        ? window.matchMedia('(prefers-color-scheme: dark)').matches
          ? 'dark'
          : 'light'
        : theme
    document.documentElement.setAttribute('data-theme', effectiveTheme)
  }

  public setOnline(isOnline: boolean): void {
    this.state.isOnline = isOnline
    this.notify()
  }

  public clearNotifications(): void {
    this.state.notificationsCount = 0
    this.notify()
  }
}

export const authStore = new AuthStore()

import { useState, useEffect } from 'react'

export function useAuthStore() {
  const [state, setState] = useState<AuthState>(authStore.getState())

  useEffect(() => {
    return authStore.subscribe(() => {
      setState({ ...authStore.getState() })
    })
  }, [])

  return {
    ...state,
    activeProject: state.currentProject,
    login: (user: UserProfile, token: string) => authStore.login(user, token),
    logout: () => authStore.logout(),
    setCurrentProject: (p: Project) => authStore.setCurrentProject(p),
    setTheme: (t: 'dark' | 'light' | 'system') => authStore.setTheme(t),
    setOnline: (o: boolean) => authStore.setOnline(o),
    clearNotifications: () => authStore.clearNotifications()
  }
}
