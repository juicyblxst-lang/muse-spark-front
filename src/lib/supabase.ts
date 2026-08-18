import { createClient } from "@supabase/supabase-js";

const supabaseUrl = import.meta.env["VITE_SUPABASE_URL"] as string | undefined;
const supabaseAnonKey = import.meta.env["VITE_SUPABASE_ANON_KEY"] as string | undefined;

if (!supabaseUrl || !supabaseAnonKey) {
  console.warn(
    "Muse Supabase Auth is not configured. Set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY to enable it.",
  );
}

/** Browser-side Supabase client. The anon key is safe to expose to the browser.
 * Row Level Security, not this client, must enforce data ownership in Postgres.
 */
export const supabase = createClient(
  supabaseUrl ?? "https://placeholder.supabase.co",
  supabaseAnonKey ?? "placeholder-anon-key",
  {
    auth: {
      persistSession: true,
      autoRefreshToken: true,
      detectSessionInUrl: true,
    },
  },
);

export const supabaseAuthConfigured = Boolean(supabaseUrl && supabaseAnonKey);
