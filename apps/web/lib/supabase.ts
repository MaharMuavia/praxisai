import { createBrowserClient } from "@supabase/ssr";
import type { SupabaseClient } from "@supabase/supabase-js";

let client: SupabaseClient | undefined;

export function getSupabaseClient(): SupabaseClient {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const publishableKey = process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY;
  if (!url || !publishableKey) {
    throw new Error("Supabase browser configuration is missing");
  }
  client ??= createBrowserClient(url, publishableKey, {
    auth: { detectSessionInUrl: false },
  });
  return client;
}

export function getSupabaseAuth() {
  return getSupabaseClient().auth;
}
