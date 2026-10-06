/**
 * DataWise AI — Authentication Store (Supabase-backed)
 * Real session management using Supabase Auth.
 * Replaces the previous demo/mock auth store.
 */

import { useState, useEffect } from 'react';
import { supabase } from '../lib/supabaseClient';
import type { Session, User } from '@supabase/supabase-js';
import type { Project } from '../types';

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
}

export interface AuthState {
  user: UserProfile | null;
  session: Session | null;
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
    let savedProject: Project | null = null;
    try {
      const raw = localStorage.getItem(STORAGE_KEY_PROJECT) || localStorage.getItem('datalab_active_project');
      if (raw) {
        const parsed = JSON.parse(raw);
        // Exclude legacy mock churn demo project
        if (parsed && parsed.name !== 'Customer Churn Intelligence' && parsed.id !== 'proj_default') {
          savedProject = parsed;
        } else {
          localStorage.removeItem('datalab_active_project');
          localStorage.removeItem(STORAGE_KEY_PROJECT);
        }
      }
    } catch {
      savedProject = null;
    }

    const savedTheme   = (localStorage.getItem(STORAGE_KEY_THEME) as 'dark' | 'light' | 'system') || 'dark';

    this.state = {
      user: null,
      session: null,
      token: null,
      isAuthenticated: false,
      isLoading: true,      // true until we check Supabase session
      currentProject: savedProject,
      theme: savedTheme,
      isOnline: navigator.onLine,
      notificationsCount: 0,
    };

    this.applyTheme(savedTheme);
    window.addEventListener('online',  () => this.setOnline(true));
    window.addEventListener('offline', () => this.setOnline(false));

    // Listen to Supabase auth state changes (handles refresh, logout from another tab, etc.)
    supabase.auth.onAuthStateChange(async (_event: any, session: any) => {
      if (session?.user) {
        const profile = await this.fetchProfile(session.user);
        this.state = {
          ...this.state,
          user: profile,
          session,
          token: session.access_token,
          isAuthenticated: true,
          isLoading: false,
        };
      } else {
        this.state = {
          ...this.state,
          user: null,
          session: null,
          token: null,
          isAuthenticated: false,
          isLoading: false,
        };
      }
      this.notify();
    });
  }

  // ── Fetch profile from public.users table ──────────────────
  private async fetchProfile(supabaseUser: User): Promise<UserProfile> {
    try {
      const { data, error } = await supabase
        .from('users')
        .select('id,email,name,avatar_url,role,organization_id,organization_name,mfa_enabled,created_at')
        .eq('id', supabaseUser.id)
        .single();

      if (error || !data) {
        // Fallback: build minimal profile from auth.user metadata
        return {
          id: supabaseUser.id,
          email: supabaseUser.email ?? '',
          name: supabaseUser.user_metadata?.name ?? supabaseUser.email?.split('@')[0] ?? 'User',
          avatar_url: supabaseUser.user_metadata?.avatar_url,
          role: 'data_scientist',
          mfa_enabled: false,
          created_at: supabaseUser.created_at,
        };
      }
      return data as UserProfile;
    } catch {
      return {
        id: supabaseUser.id,
        email: supabaseUser.email ?? '',
        name: supabaseUser.user_metadata?.name ?? 'User',
        role: 'data_scientist',
        mfa_enabled: false,
        created_at: supabaseUser.created_at,
      };
    }
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

  // signUp — creates Supabase auth user + profile row via trigger
  public async signUp(email: string, password: string, name: string): Promise<void> {
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
      options: { data: { name } },
    });
    if (error) throw new Error(error.message);
    if (!data.session) {
      // Email confirmation required
      throw new Error('CHECK_EMAIL');
    }
  }

  // signIn — logs in and triggers onAuthStateChange above
  public async signIn(email: string, password: string): Promise<void> {
    const { error } = await supabase.auth.signInWithPassword({ email, password });
    if (error) throw new Error(error.message);
  }

  // signInWithOAuth — Google, GitHub OAuth integration
  public async signInWithOAuth(provider: 'google' | 'github'): Promise<void> {
    const { error } = await supabase.auth.signInWithOAuth({
      provider,
      options: {
        redirectTo: window.location.origin + '/projects',
      },
    });
    if (error) throw new Error(error.message);
  }

  // signOut
  public async signOut(): Promise<void> {
    await supabase.auth.signOut();
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

  // Legacy compat: direct login used by old Login.tsx code
  public login(user: UserProfile, token: string): void {
    this.state.user            = user;
    this.state.token           = token;
    this.state.isAuthenticated = true;
    this.state.isLoading       = false;
    this.notify();
  }

  public signInAsDemo(): void {
    const demoUser: UserProfile = {
      id: 'usr_demo_workspace',
      email: 'demo@datawise.ai',
      name: 'Data Science Engineer',
      role: 'data_scientist',
      mfa_enabled: false,
      created_at: new Date().toISOString(),
    };
    this.login(demoUser, 'demo-token');
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
    setTheme: (t: 'dark' | 'light' | 'system') => authStore.setTheme(t),
    setOnline: (o: boolean) => authStore.setOnline(o),
    clearNotifications: () => authStore.clearNotifications(),
  };
}
