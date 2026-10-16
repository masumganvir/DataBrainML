/**
 * DataWise AI — Authentication Store (Backend JWT)
 *
 * Uses backend FastAPI JWT endpoints for all email/password auth.
 * OAuth (Google/GitHub) is initiated via backend redirects.
 * Session token stored in localStorage under 'access_token'.
 * Supabase SDK no longer used for session management.
 */

import { useState, useEffect } from 'react';
import type { Project } from '../types';

const API_BASE = import.meta.env.VITE_API_URL || import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// ─────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────

export interface UserProfile {
  id: string;
  email: string;
  name: string;
  avatar_url?: string;
  role: string;
  organization_id?: string;
  organization_name?: string;
  mfa_enabled: boolean;
  created_at: string;
  is_active?: boolean;
}

export interface AuthState {
  user: UserProfile | null;
  session: null;           // kept for API compat
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  currentProject: Project | null;
  theme: 'dark' | 'light' | 'system';
  isOnline: boolean;
  notificationsCount: number;
}

// ─────────────────────────────────────────────────────────────
// Storage Keys
// ─────────────────────────────────────────────────────────────
const STORAGE_KEY_TOKEN   = 'access_token';
const STORAGE_KEY_USER    = 'datawise_user';
const STORAGE_KEY_PROJECT = 'datawise_active_project';
const STORAGE_KEY_THEME   = 'datawise_theme';

export const DEMO_PROJECTS: Project[] = [];

// ─────────────────────────────────────────────────────────────
// Auth Store Class
// ─────────────────────────────────────────────────────────────
class AuthStore {
  private state: AuthState;
  private listeners: Set<() => void> = new Set();

  constructor() {
    // Restore persisted auth
    const savedToken = localStorage.getItem(STORAGE_KEY_TOKEN);
    let savedUser: UserProfile | null = null;
    try {
      const raw = localStorage.getItem(STORAGE_KEY_USER);
      if (raw) savedUser = JSON.parse(raw) as UserProfile;
    } catch { savedUser = null; }

    let savedProject: Project | null = null;
    try {
      const raw = localStorage.getItem(STORAGE_KEY_PROJECT) || localStorage.getItem('datalab_active_project');
      if (raw) {
        const parsed = JSON.parse(raw);
        if (parsed && parsed.name !== 'Customer Churn Intelligence' && parsed.id !== 'proj_default') {
          savedProject = parsed;
        } else {
          localStorage.removeItem('datalab_active_project');
          localStorage.removeItem(STORAGE_KEY_PROJECT);
        }
      }
    } catch { savedProject = null; }

    const savedTheme = (localStorage.getItem(STORAGE_KEY_THEME) as 'dark' | 'light' | 'system') || 'dark';

    this.state = {
      user: savedUser,
      session: null,
      token: savedToken,
      isAuthenticated: !!(savedToken && savedUser),
      isLoading: !!(savedToken && savedUser), // will verify in background if has token
      currentProject: savedProject,
      theme: savedTheme,
      isOnline: navigator.onLine,
      notificationsCount: 0,
    };

    this.applyTheme(savedTheme);
    window.addEventListener('online',  () => this.setOnline(true));
    window.addEventListener('offline', () => this.setOnline(false));

    // Handle OAuth callback tokens in URL
    this._handleCallbackToken();

    // Verify existing token in background
    if (savedToken && savedUser) {
      this._verifyToken(savedToken);
    } else {
      this.state.isLoading = false;
    }
  }

  // ── Handle OAuth callback token from URL ───────────────────
  private _handleCallbackToken(): void {
    const params = new URLSearchParams(window.location.search);
    const urlToken = params.get('token');
    const urlName  = params.get('name');
    const urlEmail = params.get('email');
    if (urlToken) {
      localStorage.setItem(STORAGE_KEY_TOKEN, urlToken);
      const partialUser: UserProfile = {
        id: '',
        email: decodeURIComponent(urlEmail || ''),
        name: decodeURIComponent(urlName || 'User'),
        role: 'data_scientist',
        mfa_enabled: false,
        created_at: new Date().toISOString(),
      };
      this.state.token = urlToken;
      this.state.user  = partialUser;
      this.state.isAuthenticated = true;
      this.state.isLoading = true;
      // Clean URL
      window.history.replaceState({}, document.title, window.location.pathname);
      // Fetch full profile
      this._verifyToken(urlToken);
    }
  }

  // ── Verify token and refresh user profile from backend ─────
  private async _verifyToken(token: string): Promise<void> {
    try {
      const resp = await fetch(`${API_BASE}/api/auth/me`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (resp.ok) {
        const userData = await resp.json();
        const profile: UserProfile = {
          id:          userData.id ?? '',
          email:       userData.email ?? '',
          name:        userData.name ?? '',
          role:        userData.role ?? 'data_scientist',
          mfa_enabled: false,
          created_at:  userData.created_at ?? new Date().toISOString(),
          is_active:   userData.is_active,
        };
        localStorage.setItem(STORAGE_KEY_USER, JSON.stringify(profile));
        this.state = {
          ...this.state,
          user: profile,
          isAuthenticated: true,
          isLoading: false,
        };
      } else {
        // Token invalid / expired
        this._clearSession();
      }
    } catch {
      // Network error — keep existing session data but mark not loading
      this.state.isLoading = false;
    }
    this.notify();
  }

  private _clearSession(): void {
    localStorage.removeItem(STORAGE_KEY_TOKEN);
    localStorage.removeItem(STORAGE_KEY_USER);
    this.state = {
      ...this.state,
      user: null,
      session: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
    };
  }

  // ── Public API ─────────────────────────────────────────────
  public getState(): AuthState { return this.state; }

  public subscribe(listener: () => void): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  private notify(): void {
    this.listeners.forEach((l) => l());
  }

  // ── Email/password registration via backend API ────────────
  public async signUp(email: string, password: string, name: string): Promise<void> {
    const resp = await fetch(`${API_BASE}/api/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, name }),
    });
    const data = await resp.json();
    if (!resp.ok) {
      throw new Error(data.detail || 'Registration failed.');
    }
    // Auto-login after registration
    const { access_token, user } = data;
    this._applySession(access_token, user);
  }

  // ── Email/password sign-in via backend API ─────────────────
  public async signIn(email: string, password: string): Promise<void> {
    const resp = await fetch(`${API_BASE}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    const data = await resp.json();
    if (!resp.ok) {
      throw new Error(data.detail || 'Incorrect email or password.');
    }
    const { access_token, user } = data;
    this._applySession(access_token, user);
  }

  private _applySession(token: string, user: any): void {
    const profile: UserProfile = {
      id:          user.id ?? '',
      email:       user.email ?? '',
      name:        user.name ?? user.email?.split('@')[0] ?? 'User',
      role:        user.role ?? 'data_scientist',
      mfa_enabled: false,
      created_at:  user.created_at ?? new Date().toISOString(),
      is_active:   user.is_active,
    };
    localStorage.setItem(STORAGE_KEY_TOKEN, token);
    localStorage.setItem(STORAGE_KEY_USER, JSON.stringify(profile));
    this.state = {
      ...this.state,
      user: profile,
      token,
      isAuthenticated: true,
      isLoading: false,
    };
    this.notify();
  }

  // ── OAuth — redirect to backend OAuth endpoint ─────────────
  public async signInWithOAuth(provider: 'google' | 'github'): Promise<void> {
    window.location.href = `${API_BASE}/api/auth/${provider}`;
  }

  // ── Sign out ───────────────────────────────────────────────
  public async signOut(): Promise<void> {
    const token = this.state.token;
    if (token) {
      try {
        await fetch(`${API_BASE}/api/auth/logout`, {
          method: 'POST',
          headers: { Authorization: `Bearer ${token}` },
        });
      } catch { /* best effort */ }
    }
    this._clearSession();
    localStorage.removeItem(STORAGE_KEY_PROJECT);
    localStorage.removeItem('datalab_active_project');
    this.state.currentProject = null;
    this.notify();
  }

  // ── Demo mode (UI testing only — no real backend auth) ────
  public signInAsDemo(): void {
    const demoUser: UserProfile = {
      id: 'usr_demo_workspace',
      email: 'demo@datawise.ai',
      name: 'Data Science Engineer (Demo)',
      role: 'data_scientist',
      mfa_enabled: false,
      created_at: new Date().toISOString(),
    };
    // Store demo token so api.ts interceptor picks it up
    localStorage.setItem(STORAGE_KEY_TOKEN, 'demo-token-no-real-auth');
    localStorage.setItem(STORAGE_KEY_USER, JSON.stringify(demoUser));
    this.state = {
      ...this.state,
      user: demoUser,
      token: 'demo-token-no-real-auth',
      isAuthenticated: true,
      isLoading: false,
    };
    this.notify();
  }

  // ── Utility ────────────────────────────────────────────────
  public setCurrentProject(project: Project): void {
    this.state.currentProject = project;
    localStorage.setItem(STORAGE_KEY_PROJECT, JSON.stringify(project));
    this.notify();
  }

  public clearCurrentProject(): void {
    this.state.currentProject = null;
    localStorage.removeItem(STORAGE_KEY_PROJECT);
    localStorage.removeItem('datalab_active_project');
    this.notify();
  }

  public setTheme(theme: 'dark' | 'light' | 'system'): void {
    this.state.theme = theme;
    localStorage.setItem(STORAGE_KEY_THEME, theme);
    this.applyTheme(theme);
    this.notify();
  }

  private applyTheme(theme: 'dark' | 'light' | 'system'): void {
    const effective =
      theme === 'system'
        ? window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
        : theme;
    document.documentElement.setAttribute('data-theme', effective);
  }

  public setOnline(isOnline: boolean): void {
    this.state.isOnline = isOnline;
    this.notify();
  }

  public clearNotifications(): void {
    this.state.notificationsCount = 0;
    this.notify();
  }

  // Legacy compat
  public login(user: UserProfile, token: string): void {
    this._applySession(token, user);
  }

  public logout(): void {
    this.signOut();
  }
}

export const authStore = new AuthStore();

// ─────────────────────────────────────────────────────────────
// React Hook
// ─────────────────────────────────────────────────────────────
export function useAuthStore() {
  const [state, setState] = useState<AuthState>(authStore.getState());

  useEffect(() => {
    return authStore.subscribe(() => {
      setState({ ...authStore.getState() });
    });
  }, []);

  return {
    ...state,
    activeProject: state.currentProject,
    signIn:  (email: string, password: string) => authStore.signIn(email, password),
    signInAsDemo: () => authStore.signInAsDemo(),
    signInWithOAuth: (provider: 'google' | 'github') => authStore.signInWithOAuth(provider),
    signUp:  (email: string, password: string, name: string) => authStore.signUp(email, password, name),
    signOut: () => authStore.signOut(),
    // legacy compat
    login:   (user: UserProfile, token: string) => authStore.login(user, token),
    logout:  () => authStore.logout(),
    setCurrentProject: (p: Project) => authStore.setCurrentProject(p),
    clearCurrentProject: () => authStore.clearCurrentProject(),
    setTheme: (t: 'dark' | 'light' | 'system') => authStore.setTheme(t),
    setOnline: (o: boolean) => authStore.setOnline(o),
    clearNotifications: () => authStore.clearNotifications(),
  };
}
