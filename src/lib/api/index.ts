import type { MuseApi } from "@/types/api";
import { httpApi } from "./http-adapter";
import { mockApi } from "./mock-adapter";

export { endpoints, API_BASE_URL } from "./endpoints";

const mode = import.meta.env["VITE_MUSE_API_MODE"] ?? "mock";

/**
 * The single API instance the UI talks to. Swapping the mock layer for the
 * real backend is a one-line environment change.
 */
export const museApi: MuseApi = mode === "http" ? httpApi : mockApi;

export const queryKeys = {
  currentUser: ["currentUser"] as const,
  dashboard: ["dashboard"] as const,
  documents: (query?: string) => ["documents", query ?? ""] as const,
  document: (id: string) => ["document", id] as const,
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
