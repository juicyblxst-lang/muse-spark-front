/**
 * Muse API contract — centralized types.
 *
 * Every type in this file describes a payload the UI exchanges with the Muse backend.
 */

export interface ApiError { code: string; message: string; details?: Record<string, unknown>; }
export interface Paginated<T> { items: T[]; total: number; page: number; pageSize: number; hasMore: boolean; }
export type IsoDateTime = string;
export interface User { id: string; email: string; displayName: string; avatarUrl: string | null; createdAt: IsoDateTime; }
export interface Session { token: string; expiresAt: IsoDateTime; user: User; }
export interface SignInRequest { email: string; password: string; }
export interface SignUpRequest { email: string; password: string; displayName: string; }

export type DocumentKind = "pdf" | "docx" | "txt" | "md";
export type DocumentStatus = "queued" | "processing" | "ready" | "failed" | "needs_review";
export interface DocumentSummary { id: string; title: string; kind: DocumentKind; status: DocumentStatus; sizeBytes: number; pageCount: number | null; uploadedAt: IsoDateTime; authoredAt: IsoDateTime | null; memoryCount: number; entityCount: number; tags: string[]; }
export interface DocumentDetail extends DocumentSummary { excerpt: string; language: string; memoryIds: string[]; entities: EntityRef[]; processing: ProcessingJob | null; }
export interface UploadTarget { documentId: string; uploadUrl?: string; jobId: string; storagePath: string; }
export interface CreateUploadRequest { file: File; fileName: string; kind: DocumentKind; sizeBytes: number; }

export type ProcessingStage = "uploading" | "parsing" | "extracting" | "resolving_entities" | "linking_relationships" | "temporal_analysis" | "indexing" | "complete";
export interface ProcessingStageState { stage: ProcessingStage; label: string; status: "pending" | "active" | "done" | "failed"; startedAt: IsoDateTime | null; completedAt: IsoDateTime | null; detail: string | null; }
export interface ProcessingJob { id: string; documentId: string; documentTitle: string; status: "queued" | "running" | "complete" | "failed"; progress: number; currentStage: ProcessingStage; stages: ProcessingStageState[]; startedAt: IsoDateTime; completedAt: IsoDateTime | null; error: ApiError | null; discovered: DiscoverySummary; }
export interface DiscoverySummary { memories: number; entities: number; relationships: number; timelineEvents: number; highlights: string[]; }

export type MemoryKind = "idea" | "note" | "decision" | "question" | "fragment" | "plan";
export interface MemorySummary { id: string; title: string; kind: MemoryKind; snippet: string; documentId: string; documentTitle: string; createdAt: IsoDateTime; occurredAt: IsoDateTime | null; confidence: number; dormancy: number; tags: string[]; entityIds: string[]; }
export interface MemoryDetail extends MemorySummary { body: string; entities: EntityRef[]; relationships: Relationship[]; sources: SourceReference[]; relatedMemoryIds: string[]; }
export interface MemorySearchRequest { query: string; kinds?: MemoryKind[]; tags?: string[]; from?: IsoDateTime; to?: IsoDateTime; page?: number; pageSize?: number; }
export interface MemorySearchResult { memory: MemorySummary; score: number; matchedTerms: string[]; reason: string; }
export interface MemorySearchResponse extends Paginated<MemorySearchResult> { query: string; suggestions: string[]; }
export type EntityType = "person" | "project" | "concept" | "place" | "organization" | "work";
export interface EntityRef { id: string; name: string; type: EntityType; }
export interface Entity extends EntityRef { aliases: string[]; description: string; mentionCount: number; firstSeenAt: IsoDateTime; lastSeenAt: IsoDateTime; memoryIds: string[]; }
export type RelationshipType = "influences" | "contradicts" | "continues" | "mentions" | "collaborates_with" | "derived_from";
export interface Relationship { id: string; type: RelationshipType; from: EntityRef; to: EntityRef; label: string; confidence: number; memoryIds: string[]; observedAt: IsoDateTime; }
export interface ConnectionGraph { entities: Entity[]; relationships: Relationship[]; }
export type TimelineEventKind = "created" | "abandoned" | "revisited" | "milestone" | "mention";
export interface TimelineEvent { id: string; title: string; description: string; kind: TimelineEventKind; occurredAt: IsoDateTime; memoryIds: string[]; documentIds: string[]; entities: EntityRef[]; }
export interface TimelineResponse { events: TimelineEvent[]; earliest: IsoDateTime; latest: IsoDateTime; gaps: Array<{ from: IsoDateTime; to: IsoDateTime; days: number }>; }
export interface RevivalRequest { memoryId: string; intent: "expand" | "reframe" | "combine" | "next_steps"; note?: string; }
export interface RevivalSuggestion { id: string; title: string; rationale: string; nextSteps: string[]; supportingMemoryIds: string[]; confidence: number; }
export interface RevivalResult { id: string; memoryId: string; memoryTitle: string; intent: RevivalRequest["intent"]; createdAt: IsoDateTime; summary: string; suggestions: RevivalSuggestion[]; sources: SourceReference[]; }
export interface SourceReference { id: string; documentId: string; documentTitle: string; kind: DocumentKind; page: number | null; charStart: number | null; charEnd: number | null; quote: string; }
export interface ProvenanceDetail { source: SourceReference; context: string; extractedAt: IsoDateTime; extractorVersion: string; derivedMemoryIds: string[]; confidence: number; }
export type CorrectionTargetType = "memory" | "entity" | "relationship" | "timeline_event";
export type CorrectionKind = "edit" | "merge" | "split" | "reject" | "retype";
export interface CorrectionRequest { targetType: CorrectionTargetType; targetId: string; kind: CorrectionKind; field?: string; value?: string; reason: string; }
export interface Correction extends CorrectionRequest { id: string; status: "pending" | "applied" | "rejected"; submittedAt: IsoDateTime; targetLabel: string; }
export interface DashboardOverview { stats: { documents: number; memories: number; entities: number; relationships: number; dormantMemories: number; }; activeJobs: ProcessingJob[]; recentDocuments: DocumentSummary[]; forgotten: MemorySummary[]; recentRevivals: RevivalResult[]; }
export interface Settings { profile: { displayName: string; email: string; }; memory: { dormancyThresholdDays: number; minConfidence: number; autoResurfaceEnabled: boolean; }; processing: { ocrEnabled: boolean; languageHint: string; retainOriginals: boolean; }; notifications: { processingComplete: boolean; weeklyResurfacing: boolean; }; }
export type SettingsUpdate = Partial<{ memory: Partial<Settings["memory"]>; processing: Partial<Settings["processing"]>; notifications: Partial<Settings["notifications"]>; profile: Partial<Settings["profile"]>; }>;

export interface MuseApi {
  signIn(input: SignInRequest): Promise<Session>; signUp(input: SignUpRequest): Promise<Session>; signOut(): Promise<void>; getCurrentUser(): Promise<User | null>;
  getDashboard(): Promise<DashboardOverview>;
  createUpload(input: CreateUploadRequest): Promise<UploadTarget>; listDocuments(params?: { query?: string; status?: DocumentStatus }): Promise<Paginated<DocumentSummary>>; getDocument(id: string): Promise<DocumentDetail>;
  getProcessingJob(jobId: string): Promise<ProcessingJob>;
  searchMemories(input: MemorySearchRequest): Promise<MemorySearchResponse>; getMemory(id: string): Promise<MemoryDetail>; getForgottenMemories(): Promise<MemorySummary[]>;
  getConnections(params?: { entityId?: string }): Promise<ConnectionGraph>; getTimeline(params?: { from?: IsoDateTime; to?: IsoDateTime }): Promise<TimelineResponse>;
  requestRevival(input: RevivalRequest): Promise<RevivalResult>; listRevivals(): Promise<RevivalResult[]>; getRevival(id: string): Promise<RevivalResult>;
  getProvenance(sourceId: string): Promise<ProvenanceDetail>;
  submitCorrection(input: CorrectionRequest): Promise<Correction>; listCorrections(): Promise<Correction[]>;
  getSettings(): Promise<Settings>; updateSettings(input: SettingsUpdate): Promise<Settings>;
}
