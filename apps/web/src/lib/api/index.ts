import type { MuseApi } from "@/types/api";
import { httpApi } from "./http-adapter";
import { mockApi } from "./mock-adapter";
import { supabaseAuthApi } from "./supabase-auth-adapter";
import { supabaseAuthConfigured } from "@/lib/supabase";

export { endpoints, API_BASE_URL } from "./endpoints";

const mode = import.meta.env["VITE_MUSE_API_MODE"] ?? "mock";

/**
 * The single API instance the UI talks to. Supabase owns authentication when
 * configured; the existing HTTP/mock adapters remain responsible for the rest
 * of the Muse API until those backend endpoints are connected.
 */
const baseApi: MuseApi = mode === "http" ? httpApi : mockApi;

export const museApi: MuseApi = {
  ...baseApi,
  ...(supabaseAuthConfigured ? supabaseAuthApi : {}),
};

export const queryKeys = {
  currentUser: ["currentUser"] as const,
  documents: (query?: string) => ["documents", query ?? ""] as const,
  document: (id: string) => ["document", id] as const,
  dashboard: ["dashboard"] as const,
  processingJob: (id: string) => ["processingJob", id] as const,
  memorySearch: (query: string) => ["memorySearch", query] as const,
  memory: (id: string) => ["memory", id] as const,
  forgotten: ["forgotten"] as const,
  connections: (entityId?: string) => ["connections", entityId ?? "all"] as const,
  timeline: ["timeline"] as const,
  revivals: ["revivals"] as const,
  revival: (id: string) => ["revival", id] as const,
  provenance: (id: string) => ["provenance", id] as const,
  corrections: ["corrections"] as const,
  settings: ["settings"] as const,
};
