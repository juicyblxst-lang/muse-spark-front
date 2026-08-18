import { API_BASE_URL, endpoints } from "./endpoints";
import type {
  ConnectionGraph,
  Correction,
  CorrectionRequest,
  CreateUploadRequest,
  DashboardOverview,
  DocumentDetail,
  DocumentStatus,
  DocumentSummary,
  IsoDateTime,
  MemoryDetail,
  MemorySearchRequest,
  MemorySearchResponse,
  MemorySummary,
  MuseApi,
  Paginated,
  ProcessingJob,
  ProvenanceDetail,
  RevivalRequest,
  RevivalResult,
  Session,
  Settings,
  SettingsUpdate,
  SignInRequest,
  SignUpRequest,
  TimelineResponse,
  UploadTarget,
  User,
} from "@/types/api";

/**
 * Real HTTP implementation of the Muse API contract.
 *
 * Nothing in the UI needs to change when this replaces the mock adapter —
 * flip `VITE_MUSE_API_MODE=http` once the backend exists.
 */

async function request<T>(
  path: string,
  init?: { method?: string; body?: unknown; query?: Record<string, string | undefined> },
): Promise<T> {
  const url = new URL(`${API_BASE_URL}${path}`, "http://local");
  for (const [key, value] of Object.entries(init?.query ?? {})) {
    if (value !== undefined) url.searchParams.set(key, value);
  }

  const response = await fetch(`${url.pathname}${url.search}`, {
    method: init?.method ?? "GET",
    headers: { "content-type": "application/json" },
    body: init?.body === undefined ? null : JSON.stringify(init.body),
  });

  if (!response.ok) {
    throw Object.assign(new Error(`Muse API ${response.status}`), {
      code: String(response.status),
    });
  }

  return (await response.json()) as T;
}

export const httpApi: MuseApi = {
  signIn: (input: SignInRequest) =>
    request<Session>(endpoints.auth.signIn(), { method: "POST", body: input }),
  signUp: (input: SignUpRequest) =>
    request<Session>(endpoints.auth.signUp(), { method: "POST", body: input }),
  signOut: () => request<void>(endpoints.auth.signOut(), { method: "POST" }),
  getCurrentUser: () => request<User | null>(endpoints.auth.me()),

  getDashboard: () => request<DashboardOverview>(endpoints.dashboard.overview()),

  createUpload: (input: CreateUploadRequest) =>
    request<UploadTarget>(endpoints.documents.createUpload(), { method: "POST", body: input }),
  listDocuments: (params?: { query?: string | undefined; status?: DocumentStatus | undefined }) =>
    request<Paginated<DocumentSummary>>(endpoints.documents.list(), {
      query: { query: params?.query, status: params?.status },
    }),
  getDocument: (id: string) => request<DocumentDetail>(endpoints.documents.detail(id)),

  getProcessingJob: (jobId: string) => request<ProcessingJob>(endpoints.processing.job(jobId)),

  searchMemories: (input: MemorySearchRequest) =>
    request<MemorySearchResponse>(endpoints.memories.search(), { method: "POST", body: input }),
  getMemory: (id: string) => request<MemoryDetail>(endpoints.memories.detail(id)),
  getForgottenMemories: () => request<MemorySummary[]>(endpoints.memories.forgotten()),

  getConnections: (params?: { entityId?: string | undefined }) =>
    request<ConnectionGraph>(endpoints.graph.connections(), {
      query: { entityId: params?.entityId },
    }),
  getTimeline: (params?: { from?: IsoDateTime | undefined; to?: IsoDateTime | undefined }) =>
    request<TimelineResponse>(endpoints.graph.timeline(), {
      query: { from: params?.from, to: params?.to },
    }),

  requestRevival: (input: RevivalRequest) =>
    request<RevivalResult>(endpoints.revival.create(), { method: "POST", body: input }),
  listRevivals: () => request<RevivalResult[]>(endpoints.revival.list()),
  getRevival: (id: string) => request<RevivalResult>(endpoints.revival.detail(id)),

  getProvenance: (sourceId: string) =>
    request<ProvenanceDetail>(endpoints.provenance.detail(sourceId)),

  submitCorrection: (input: CorrectionRequest) =>
    request<Correction>(endpoints.corrections.create(), { method: "POST", body: input }),
  listCorrections: () => request<Correction[]>(endpoints.corrections.list()),

  getSettings: () => request<Settings>(endpoints.settings.get()),
  updateSettings: (input: SettingsUpdate) =>
    request<Settings>(endpoints.settings.update(), { method: "PATCH", body: input }),
};
