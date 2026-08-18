/**
 * Muse API contract — centralized types.
 *
 * Every type in this file describes a payload the future Muse backend will
 * provide over HTTP. The UI imports ONLY from here (never from mock files),
 * so swapping the mock adapter for a real fetch client requires no UI changes.
 */

/* ------------------------------------------------------------------ */
/* Shared envelopes                                                    */
/* ------------------------------------------------------------------ */

export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, unknown>;
}

export interface Paginated<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  hasMore: boolean;
}

/** ISO-8601 timestamp string, e.g. "2024-03-11T09:12:00Z". */
export type IsoDateTime = string;

/* ------------------------------------------------------------------ */
/* Auth                                                               */
/* ------------------------------------------------------------------ */

export interface User {
  id: string;
  email: string;
  displayName: string;
  avatarUrl: string | null;
  createdAt: IsoDateTime;
}

export interface Session {
  token: string;
  expiresAt: IsoDateTime;
  user: User;
}

export interface SignInRequest {
  email: string;
  password: string;
}

export interface SignUpRequest {
  email: string;
  password: string;
  displayName: string;
}

/* ------------------------------------------------------------------ */
/* Documents & uploads                                                */
/* ------------------------------------------------------------------ */

export type DocumentKind = "pdf" | "docx" | "txt" | "md";

export type DocumentStatus = "queued" | "processing" | "ready" | "failed" | "needs_review";

export interface DocumentSummary {
  id: string;
  title: string;
  kind: DocumentKind;
  status: DocumentStatus;
  sizeBytes: number;
  pageCount: number | null;
  uploadedAt: IsoDateTime;
  /** Original creation date of the material, when Muse could infer it. */
  authoredAt: IsoDateTime | null;
  memoryCount: number;
  entityCount: number;
  tags: string[];
}

export interface DocumentDetail extends DocumentSummary {
  excerpt: string;
  language: string;
  /** Ids of memories extracted from this document. */
  memoryIds: string[];
  entities: EntityRef[];
  processing: ProcessingJob | null;
}

export interface UploadTarget {
  documentId: string;
  /** Pre-signed destination the client PUTs the file to. */
  uploadUrl: string;
  jobId: string;
}

export interface CreateUploadRequest {
  fileName: string;
  kind: DocumentKind;
  sizeBytes: number;
}

/* ------------------------------------------------------------------ */
/* Processing                                                         */
/* ------------------------------------------------------------------ */

export type ProcessingStage =
  | "uploading"
  | "parsing"
  | "extracting"
  | "resolving_entities"
  | "linking_relationships"
  | "temporal_analysis"
  | "indexing"
  | "complete";

export interface ProcessingStageState {
  stage: ProcessingStage;
  label: string;
  status: "pending" | "active" | "done" | "failed";
  startedAt: IsoDateTime | null;
  completedAt: IsoDateTime | null;
  detail: string | null;
}

export interface ProcessingJob {
  id: string;
  documentId: string;
  documentTitle: string;
  status: "queued" | "running" | "complete" | "failed";
  progress: number;
  currentStage: ProcessingStage;
  stages: ProcessingStageState[];
  startedAt: IsoDateTime;
  completedAt: IsoDateTime | null;
  error: ApiError | null;
  /** What Muse found so far — populated as stages complete. */
  discovered: DiscoverySummary;
}

export interface DiscoverySummary {
  memories: number;
  entities: number;
  relationships: number;
  timelineEvents: number;
  highlights: string[];
}

/* ------------------------------------------------------------------ */
/* Memories                                                           */
/* ------------------------------------------------------------------ */

export type MemoryKind = "idea" | "note" | "decision" | "question" | "fragment" | "plan";

export interface MemorySummary {
  id: string;
  title: string;
  kind: MemoryKind;
  snippet: string;
  documentId: string;
  documentTitle: string;
  createdAt: IsoDateTime;
  /** Inferred date of the underlying material. */
  occurredAt: IsoDateTime | null;
  confidence: number;
  /** 0–1: how dormant this memory is (1 = long forgotten). */
  dormancy: number;
  tags: string[];
  entityIds: string[];
}

export interface MemoryDetail extends MemorySummary {
  body: string;
  entities: EntityRef[];
  relationships: Relationship[];
  sources: SourceReference[];
  relatedMemoryIds: string[];
}

export interface MemorySearchRequest {
  query: string;
  kinds?: MemoryKind[] | undefined;
  tags?: string[] | undefined;
  from?: IsoDateTime | undefined;
  to?: IsoDateTime | undefined;
  page?: number | undefined;
  pageSize?: number | undefined;
}

export interface MemorySearchResult {
  memory: MemorySummary;
  score: number;
  matchedTerms: string[];
  reason: string;
}

export interface MemorySearchResponse extends Paginated<MemorySearchResult> {
  query: string;
  suggestions: string[];
}

/* ------------------------------------------------------------------ */
/* Entities & relationships                                           */
/* ------------------------------------------------------------------ */

export type EntityType = "person" | "project" | "concept" | "place" | "organization" | "work";

export interface EntityRef {
  id: string;
  name: string;
  type: EntityType;
}

export interface Entity extends EntityRef {
  aliases: string[];
  description: string;
  mentionCount: number;
  firstSeenAt: IsoDateTime;
  lastSeenAt: IsoDateTime;
  memoryIds: string[];
}

export type RelationshipType =
  "influences" | "contradicts" | "continues" | "mentions" | "collaborates_with" | "derived_from";

export interface Relationship {
  id: string;
  type: RelationshipType;
  from: EntityRef;
  to: EntityRef;
  label: string;
  confidence: number;
  memoryIds: string[];
  observedAt: IsoDateTime;
}

export interface ConnectionGraph {
  entities: Entity[];
  relationships: Relationship[];
}

/* ------------------------------------------------------------------ */
/* Timeline                                                           */
/* ------------------------------------------------------------------ */

export type TimelineEventKind = "created" | "abandoned" | "revisited" | "milestone" | "mention";

export interface TimelineEvent {
  id: string;
  title: string;
  description: string;
  kind: TimelineEventKind;
  occurredAt: IsoDateTime;
  memoryIds: string[];
  documentIds: string[];
  entities: EntityRef[];
}

export interface TimelineResponse {
  events: TimelineEvent[];
  earliest: IsoDateTime;
  latest: IsoDateTime;
  /** Stretches of time with no recorded creative activity. */
  gaps: Array<{ from: IsoDateTime; to: IsoDateTime; days: number }>;
}

/* ------------------------------------------------------------------ */
/* Revival                                                            */
/* ------------------------------------------------------------------ */

export interface RevivalRequest {
  memoryId: string;
  intent: "expand" | "reframe" | "combine" | "next_steps";
  note?: string | undefined;
}

export interface RevivalSuggestion {
  id: string;
  title: string;
  rationale: string;
  nextSteps: string[];
  supportingMemoryIds: string[];
  confidence: number;
}

export interface RevivalResult {
  id: string;
  memoryId: string;
  memoryTitle: string;
  intent: RevivalRequest["intent"];
  createdAt: IsoDateTime;
  summary: string;
  suggestions: RevivalSuggestion[];
  sources: SourceReference[];
}

/* ------------------------------------------------------------------ */
/* Provenance                                                         */
/* ------------------------------------------------------------------ */

export interface SourceReference {
  id: string;
  documentId: string;
  documentTitle: string;
  kind: DocumentKind;
  page: number | null;
  charStart: number | null;
  charEnd: number | null;
  quote: string;
}

export interface ProvenanceDetail {
  source: SourceReference;
  /** Raw surrounding text as parsed from the original document. */
  context: string;
  extractedAt: IsoDateTime;
  extractorVersion: string;
  derivedMemoryIds: string[];
  confidence: number;
}

/* ------------------------------------------------------------------ */
/* Corrections                                                        */
/* ------------------------------------------------------------------ */

export type CorrectionTargetType = "memory" | "entity" | "relationship" | "timeline_event";

export type CorrectionKind = "edit" | "merge" | "split" | "reject" | "retype";

export interface CorrectionRequest {
  targetType: CorrectionTargetType;
  targetId: string;
  kind: CorrectionKind;
  field?: string | undefined;
  value?: string | undefined;
  reason: string;
}

export interface Correction extends CorrectionRequest {
  id: string;
  status: "pending" | "applied" | "rejected";
  submittedAt: IsoDateTime;
  targetLabel: string;
}

/* ------------------------------------------------------------------ */
/* Dashboard                                                          */
/* ------------------------------------------------------------------ */

export interface DashboardOverview {
  stats: {
    documents: number;
    memories: number;
    entities: number;
    relationships: number;
    dormantMemories: number;
  };
  activeJobs: ProcessingJob[];
  recentDocuments: DocumentSummary[];
  forgotten: MemorySummary[];
  recentRevivals: RevivalResult[];
}

/* ------------------------------------------------------------------ */
/* Settings                                                           */
/* ------------------------------------------------------------------ */

export interface Settings {
  profile: {
    displayName: string;
    email: string;
  };
  memory: {
    dormancyThresholdDays: number;
    minConfidence: number;
    autoResurfaceEnabled: boolean;
  };
  processing: {
    ocrEnabled: boolean;
    languageHint: string;
    retainOriginals: boolean;
  };
  notifications: {
    processingComplete: boolean;
    weeklyResurfacing: boolean;
  };
}

export type SettingsUpdate = Partial<{
  memory: Partial<Settings["memory"]>;
  processing: Partial<Settings["processing"]>;
  notifications: Partial<Settings["notifications"]>;
  profile: Partial<Settings["profile"]>;
}>;

/* ------------------------------------------------------------------ */
/* Client contract                                                    */
/* ------------------------------------------------------------------ */

/**
 * The complete surface the UI depends on. The mock adapter and the future
 * HTTP adapter both implement this interface — nothing else.
 */
export interface MuseApi {
  signIn(input: SignInRequest): Promise<Session>;
  signUp(input: SignUpRequest): Promise<Session>;
  signOut(): Promise<void>;
  getCurrentUser(): Promise<User | null>;

  getDashboard(): Promise<DashboardOverview>;

  createUpload(input: CreateUploadRequest): Promise<UploadTarget>;
  listDocuments(params?: {
    query?: string | undefined;
    status?: DocumentStatus | undefined;
  }): Promise<Paginated<DocumentSummary>>;
  getDocument(id: string): Promise<DocumentDetail>;

  getProcessingJob(jobId: string): Promise<ProcessingJob>;

  searchMemories(input: MemorySearchRequest): Promise<MemorySearchResponse>;
  getMemory(id: string): Promise<MemoryDetail>;
  getForgottenMemories(): Promise<MemorySummary[]>;

  getConnections(params?: { entityId?: string | undefined }): Promise<ConnectionGraph>;
  getTimeline(params?: {
    from?: IsoDateTime | undefined;
    to?: IsoDateTime | undefined;
  }): Promise<TimelineResponse>;

  requestRevival(input: RevivalRequest): Promise<RevivalResult>;
  listRevivals(): Promise<RevivalResult[]>;
  getRevival(id: string): Promise<RevivalResult>;

  getProvenance(sourceId: string): Promise<ProvenanceDetail>;

  submitCorrection(input: CorrectionRequest): Promise<Correction>;
  listCorrections(): Promise<Correction[]>;

  getSettings(): Promise<Settings>;
  updateSettings(input: SettingsUpdate): Promise<Settings>;
}
