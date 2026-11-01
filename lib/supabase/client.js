import { createBrowserClient } from '@supabase/ssr';

/**
 * Creates a Supabase client for Browser / Client Components
 */
export function createClient() {
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://mock.supabase.co';
  const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || 'mock-anon-key';

  return createBrowserClient(supabaseUrl, supabaseAnonKey);
}
