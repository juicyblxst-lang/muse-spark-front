import type { MuseApi } from "@/types/api";
import { httpApi } from "./http-adapter";

export { endpoints, API_BASE_URL } from "./endpoints";



/**
 * The single API instance the UI talks to. The mock layer is an explicit opt-in for isolated UI development;
 * production and deployed environments use the real backend by default.
 */
export const museApi: MuseApi = httpApi;

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
