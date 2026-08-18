import type {
  ConnectionGraph,
  Correction,
  CorrectionRequest,
  CreateUploadRequest,
  DashboardOverview,
  DocumentDetail,
  DocumentStatus,
  DocumentSummary,
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
  User,
} from "@/types/api";
import {
  mockCorrections,
  mockDashboard,
  mockDocumentDetails,
  mockDocuments,
  mockEntities,
  mockMemories,
  mockMemoryDetails,
  mockProcessingJobs,
  mockProvenance,
  mockRelationships,
  mockRevivals,
  mockSettings,
  mockUser,
} from "./mock-data";

/**
 * Mock implementation of the Muse API contract.
 *
 * It only filters and returns fixtures — no parsing, extraction, scoring or
 * any other backend behaviour is simulated here.
 */

const delay = (ms = 220) => new Promise<void>((resolve) => setTimeout(resolve, ms));

function notFound(what: string): never {
  throw Object.assign(new Error(`${what} not found`), { code: "not_found" });
}

let currentUser: User | null = mockUser;
let settings: Settings = mockSettings;
let corrections: Correction[] = [...mockCorrections];

function session(user: User): Session {
  return {
    token: "mock-session-token",
    expiresAt: new Date(Date.now() + 86_400_000).toISOString(),
    user,
  };
}

export const mockApi: MuseApi = {
  async signIn(input: SignInRequest) {
    await delay();
    currentUser = { ...mockUser, email: input.email };
    return session(currentUser);
  },

  async signUp(input: SignUpRequest) {
    await delay();
    currentUser = { ...mockUser, email: input.email, displayName: input.displayName };
    return session(currentUser);
  },

  async signOut() {
    await delay(80);
    currentUser = null;
  },

  async getCurrentUser() {
    await delay(60);
    return currentUser;
  },

  async getDashboard(): Promise<DashboardOverview> {
    await delay();
    return mockDashboard;
  },

  async createUpload(input: CreateUploadRequest) {
    await delay(160);
    return {
      documentId: `doc_${input.fileName.length}_${Math.random().toString(36).slice(2, 8)}`,
      uploadUrl: "mock://upload",
      jobId: "job_1",
    };
  },

  async listDocuments(params?: {
    query?: string | undefined;
    status?: DocumentStatus | undefined;
  }): Promise<Paginated<DocumentSummary>> {
    await delay();
    const query = params?.query?.trim().toLowerCase() ?? "";
    const items = mockDocuments.filter((doc) => {
      const matchesQuery = query
        ? doc.title.toLowerCase().includes(query) ||
          doc.tags.some((tag) => tag.toLowerCase().includes(query))
        : true;
      const matchesStatus = params?.status ? doc.status === params.status : true;
      return matchesQuery && matchesStatus;
    });
    return { items, total: items.length, page: 1, pageSize: items.length, hasMore: false };
  },

  async getDocument(id: string): Promise<DocumentDetail> {
    await delay();
    return mockDocumentDetails[id] ?? notFound("Document");
  },

  async getProcessingJob(jobId: string): Promise<ProcessingJob> {
    await delay();
    return mockProcessingJobs[jobId] ?? notFound("Processing job");
  },

  async searchMemories(input: MemorySearchRequest): Promise<MemorySearchResponse> {
    await delay();
    const query = input.query.trim().toLowerCase();
    const filtered = mockMemories.filter((memory) => {
      const matchesQuery = query
        ? [memory.title, memory.snippet, ...memory.tags].join(" ").toLowerCase().includes(query)
        : true;
      const matchesKind = input.kinds?.length ? input.kinds.includes(memory.kind) : true;
      const matchesTags = input.tags?.length
        ? input.tags.some((tag) => memory.tags.includes(tag))
        : true;
      return matchesQuery && matchesKind && matchesTags;
    });

    const items = filtered.map((memory) => ({
      memory,
      score: memory.confidence,
      matchedTerms: query ? [query] : [],
      reason: query
        ? `Mentions “${query}” in ${memory.documentTitle}`
        : `Recorded from ${memory.documentTitle}`,
    }));

    return {
      items,
      total: items.length,
      page: input.page ?? 1,
      pageSize: input.pageSize ?? items.length,
      hasMore: false,
      query: input.query,
      suggestions: ["slow light", "salt", "Nightjar", "Iris", "abandoned"],
    };
  },

  async getMemory(id: string): Promise<MemoryDetail> {
    await delay();
    return mockMemoryDetails[id] ?? notFound("Memory");
  },

  async getForgottenMemories(): Promise<MemorySummary[]> {
    await delay();
    return mockDashboard.forgotten;
  },

  async getConnections(params?: { entityId?: string | undefined }): Promise<ConnectionGraph> {
    await delay();
    if (!params?.entityId) {
      return { entities: mockEntities, relationships: mockRelationships };
    }
    const relationships = mockRelationships.filter(
      (rel) => rel.from.id === params.entityId || rel.to.id === params.entityId,
    );
    const ids = new Set(relationships.flatMap((rel) => [rel.from.id, rel.to.id]));
    return {
      entities: mockEntities.filter((entity) => ids.has(entity.id)),
      relationships,
    };
  },

  async getTimeline(): Promise<TimelineResponse> {
    await delay();
    const { mockTimeline } = await import("./mock-data");
    return mockTimeline;
  },

  async requestRevival(input: RevivalRequest): Promise<RevivalResult> {
    await delay(400);
    const existing = mockRevivals.find((revival) => revival.memoryId === input.memoryId);
    const base = existing ?? mockRevivals[0]!;
    return { ...base, intent: input.intent, createdAt: new Date().toISOString() };
  },

  async listRevivals(): Promise<RevivalResult[]> {
    await delay();
    return mockRevivals;
  },

  async getRevival(id: string): Promise<RevivalResult> {
    await delay();
    return mockRevivals.find((revival) => revival.id === id) ?? notFound("Revival");
  },

  async getProvenance(sourceId: string): Promise<ProvenanceDetail> {
    await delay();
    return mockProvenance[sourceId] ?? notFound("Source");
  },

  async submitCorrection(input: CorrectionRequest): Promise<Correction> {
    await delay(260);
    const correction: Correction = {
      ...input,
      id: `cor_${Math.random().toString(36).slice(2, 8)}`,
      status: "pending",
      submittedAt: new Date().toISOString(),
      targetLabel: input.targetId,
    };
    corrections = [correction, ...corrections];
    return correction;
  },

  async listCorrections(): Promise<Correction[]> {
    await delay();
    return corrections;
  },

  async getSettings(): Promise<Settings> {
    await delay();
    return settings;
  },

  async updateSettings(input: SettingsUpdate): Promise<Settings> {
    await delay(200);
    settings = {
      profile: { ...settings.profile, ...input.profile },
      memory: { ...settings.memory, ...input.memory },
      processing: { ...settings.processing, ...input.processing },
      notifications: { ...settings.notifications, ...input.notifications },
    };
    return settings;
  },
};
