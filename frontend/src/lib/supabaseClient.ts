/**
 * DataWise AI — Supabase JavaScript Client Singleton
 * Import this wherever you need auth or storage access.
 */

import { createClient } from '@supabase/supabase-js';

const supabaseUrl  = import.meta.env.VITE_SUPABASE_URL  as string;
const supabaseAnon = import.meta.env.VITE_SUPABASE_ANON_KEY as string;

if (!supabaseUrl || !supabaseAnon) {
  console.error(
    '[Supabase] VITE_SUPABASE_URL or VITE_SUPABASE_ANON_KEY is not set. ' +
    'Create a frontend/.env file with these variables.'
  );
}

export const supabase = createClient(supabaseUrl ?? '', supabaseAnon ?? '', {
  auth: {
    autoRefreshToken:  true,
    persistSession:    true,
    detectSessionInUrl: true,
  },
});

export type { Session, User } from '@supabase/supabase-js';
