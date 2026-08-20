import type {
  Correction,
  DashboardOverview,
  DocumentDetail,
  DocumentSummary,
  Entity,
  MemoryDetail,
  MemorySummary,
  ProcessingJob,
  ProvenanceDetail,
  Relationship,
  RevivalResult,
  Settings,
  SourceReference,
  TimelineResponse,
  User,
} from "@/types/api";

/**
 * Isolated demo fixtures for explicit VITE_MUSE_API_MODE=mock development only.
 * These values must never be enabled in a user-facing or production environment.
 * No inference, scoring or generation logic lives here.
 */

export const mockUser: User = {
  id: "usr_1",
  email: "you@muse.studio",
  displayName: "Ada Fenwick",
  avatarUrl: null,
  createdAt: "2023-11-02T10:00:00Z",
};

export const mockDocuments: DocumentSummary[] = [
  {
    id: "doc_1",
    title: "Nightjar — first treatment.pdf",
    kind: "pdf",
    status: "ready",
    sizeBytes: 1_842_000,
    pageCount: 24,
    uploadedAt: "2026-07-04T08:12:00Z",
    authoredAt: "2019-03-11T00:00:00Z",
    memoryCount: 14,
    entityCount: 9,
    tags: ["screenplay", "abandoned"],
  },
  {
    id: "doc_2",
    title: "Studio notebook 2020.md",
    kind: "md",
    status: "ready",
    sizeBytes: 96_400,
    pageCount: null,
    uploadedAt: "2026-07-09T15:41:00Z",
    authoredAt: "2020-01-18T00:00:00Z",
    memoryCount: 31,
    entityCount: 22,
    tags: ["notebook", "sketches"],
  },
  {
    id: "doc_3",
    title: "Grant application draft.docx",
    kind: "docx",
    status: "needs_review",
    sizeBytes: 412_800,
    pageCount: 11,
    uploadedAt: "2026-08-01T09:02:00Z",
    authoredAt: "2021-09-30T00:00:00Z",
    memoryCount: 8,
    entityCount: 12,
    tags: ["funding"],
  },
  {
    id: "doc_4",
    title: "Voice memo transcript.txt",
    kind: "txt",
    status: "processing",
    sizeBytes: 21_300,
    pageCount: null,
    uploadedAt: "2026-08-17T21:30:00Z",
    authoredAt: null,
    memoryCount: 0,
    entityCount: 0,
    tags: [],
  },
  {
    id: "doc_5",
    title: "Salt Chapel — installation plan.pdf",
    kind: "pdf",
    status: "failed",
    sizeBytes: 5_120_000,
    pageCount: 40,
    uploadedAt: "2026-06-22T11:15:00Z",
    authoredAt: "2018-05-02T00:00:00Z",
    memoryCount: 0,
    entityCount: 0,
    tags: ["installation"],
  },
];

export const mockEntities: Entity[] = [
  {
    id: "ent_nightjar",
    name: "Nightjar",
    type: "project",
    aliases: ["The Nightjar Film", "NJ"],
    description: "An unfinished film about a night-shift radio operator.",
    mentionCount: 42,
    firstSeenAt: "2019-03-11T00:00:00Z",
    lastSeenAt: "2021-09-30T00:00:00Z",
    memoryIds: ["mem_1", "mem_3", "mem_5"],
  },
  {
    id: "ent_saltchapel",
    name: "Salt Chapel",
    type: "work",
    aliases: ["Chapel of Salt"],
    description: "Salt-cast installation proposed for a decommissioned chapel.",
    mentionCount: 18,
    firstSeenAt: "2018-05-02T00:00:00Z",
    lastSeenAt: "2020-02-14T00:00:00Z",
    memoryIds: ["mem_2", "mem_4"],
  },
  {
    id: "ent_iris",
    name: "Iris Okonkwo",
    type: "person",
    aliases: ["Iris O."],
    description: "Sound designer and long-time collaborator.",
    mentionCount: 27,
    firstSeenAt: "2019-04-02T00:00:00Z",
    lastSeenAt: "2021-11-08T00:00:00Z",
    memoryIds: ["mem_1", "mem_5"],
  },
  {
    id: "ent_slowlight",
    name: "Slow light",
    type: "concept",
    aliases: ["latency of light"],
    description: "Recurring motif: images arriving later than their sound.",
    mentionCount: 33,
    firstSeenAt: "2019-03-11T00:00:00Z",
    lastSeenAt: "2022-01-04T00:00:00Z",
    memoryIds: ["mem_1", "mem_2", "mem_3"],
  },
  {
    id: "ent_harbour",
    name: "Harbour House Trust",
    type: "organization",
    aliases: [],
    description: "Funding body approached for the chapel installation.",
    mentionCount: 6,
    firstSeenAt: "2021-09-30T00:00:00Z",
    lastSeenAt: "2021-10-14T00:00:00Z",
    memoryIds: ["mem_4"],
  },
  {
    id: "ent_lisbon",
    name: "Lisbon",
    type: "place",
    aliases: [],
    description: "Residency location referenced across the 2020 notebook.",
    mentionCount: 11,
    firstSeenAt: "2020-01-18T00:00:00Z",
    lastSeenAt: "2020-03-06T00:00:00Z",
    memoryIds: ["mem_3"],
  },
];

export const mockRelationships: Relationship[] = [
  {
    id: "rel_1",
    type: "influences",
    from: { id: "ent_slowlight", name: "Slow light", type: "concept" },
    to: { id: "ent_nightjar", name: "Nightjar", type: "project" },
    label: "motif shapes the film's structure",
    confidence: 0.86,
    memoryIds: ["mem_1", "mem_3"],
    observedAt: "2019-03-11T00:00:00Z",
  },
  {
    id: "rel_2",
    type: "collaborates_with",
    from: { id: "ent_iris", name: "Iris Okonkwo", type: "person" },
    to: { id: "ent_nightjar", name: "Nightjar", type: "project" },
    label: "sound design partner",
    confidence: 0.93,
    memoryIds: ["mem_5"],
    observedAt: "2019-04-02T00:00:00Z",
  },
  {
    id: "rel_3",
    type: "derived_from",
    from: { id: "ent_saltchapel", name: "Salt Chapel", type: "work" },
    to: { id: "ent_slowlight", name: "Slow light", type: "concept" },
    label: "installation restates the motif spatially",
    confidence: 0.71,
    memoryIds: ["mem_2"],
    observedAt: "2018-05-02T00:00:00Z",
  },
  {
    id: "rel_4",
    type: "contradicts",
    from: { id: "ent_harbour", name: "Harbour House Trust", type: "organization" },
    to: { id: "ent_saltchapel", name: "Salt Chapel", type: "work" },
    label: "funding scope conflicts with the original scale",
    confidence: 0.64,
    memoryIds: ["mem_4"],
    observedAt: "2021-10-14T00:00:00Z",
  },
  {
    id: "rel_5",
    type: "continues",
    from: { id: "ent_nightjar", name: "Nightjar", type: "project" },
    to: { id: "ent_lisbon", name: "Lisbon", type: "place" },
    label: "residency notes resume the treatment",
    confidence: 0.58,
    memoryIds: ["mem_3"],
    observedAt: "2020-01-18T00:00:00Z",
  },
];

export const mockMemories: MemorySummary[] = [
  {
    id: "mem_1",
    title: "Radio operator hears tomorrow's weather",
    kind: "idea",
    snippet:
      "The night-shift operator picks up a forecast that hasn't happened yet. She starts writing it down instead of reporting it.",
    documentId: "doc_1",
    documentTitle: "Nightjar — first treatment.pdf",
    createdAt: "2026-07-04T08:20:00Z",
    occurredAt: "2019-03-11T00:00:00Z",
    confidence: 0.91,
    dormancy: 0.88,
    tags: ["screenplay", "premise"],
    entityIds: ["ent_nightjar", "ent_slowlight", "ent_iris"],
  },
  {
    id: "mem_2",
    title: "Cast the chapel pews in salt",
    kind: "plan",
    snippet:
      "Pews cast in compressed salt so the room slowly erodes under visitors' breath over the run of the show.",
    documentId: "doc_2",
    documentTitle: "Studio notebook 2020.md",
    createdAt: "2026-07-09T15:52:00Z",
    occurredAt: "2018-05-02T00:00:00Z",
    confidence: 0.78,
    dormancy: 0.94,
    tags: ["installation", "material"],
    entityIds: ["ent_saltchapel", "ent_slowlight"],
  },
  {
    id: "mem_3",
    title: "Lisbon: sound arrives before the image",
    kind: "note",
    snippet:
      "Whole week spent on delay. If the audio leads the picture by two frames the room feels haunted rather than broken.",
    documentId: "doc_2",
    documentTitle: "Studio notebook 2020.md",
    createdAt: "2026-07-09T15:58:00Z",
    occurredAt: "2020-01-18T00:00:00Z",
    confidence: 0.83,
    dormancy: 0.61,
    tags: ["craft", "residency"],
    entityIds: ["ent_lisbon", "ent_slowlight", "ent_nightjar"],
  },
  {
    id: "mem_4",
    title: "Should the chapel piece be smaller?",
    kind: "question",
    snippet:
      "Trust wants a touring version. A single pew and a recording might carry more than the full room.",
    documentId: "doc_3",
    documentTitle: "Grant application draft.docx",
    createdAt: "2026-08-01T09:14:00Z",
    occurredAt: "2021-09-30T00:00:00Z",
    confidence: 0.69,
    dormancy: 0.47,
    tags: ["funding", "scope"],
    entityIds: ["ent_harbour", "ent_saltchapel"],
  },
  {
    id: "mem_5",
    title: "Iris's tape-loop score for the third act",
    kind: "fragment",
    snippet:
      "Four loops of harbour noise, each a semitone apart, layered until the third act collapses into one tone.",
    documentId: "doc_1",
    documentTitle: "Nightjar — first treatment.pdf",
    createdAt: "2026-07-04T08:31:00Z",
    occurredAt: "2019-04-02T00:00:00Z",
    confidence: 0.74,
    dormancy: 0.72,
    tags: ["sound", "collaboration"],
    entityIds: ["ent_iris", "ent_nightjar"],
  },
  {
    id: "mem_6",
    title: "Drop the framing device entirely",
    kind: "decision",
    snippet:
      "The letters-to-a-brother frame is scaffolding. Removing it costs one scene and buys the whole second act.",
    documentId: "doc_1",
    documentTitle: "Nightjar — first treatment.pdf",
    createdAt: "2026-07-04T08:44:00Z",
    occurredAt: "2019-06-21T00:00:00Z",
    confidence: 0.88,
    dormancy: 0.35,
    tags: ["structure"],
    entityIds: ["ent_nightjar"],
  },
];

export const mockSources: SourceReference[] = [
  {
    id: "src_1",
    documentId: "doc_1",
    documentTitle: "Nightjar — first treatment.pdf",
    kind: "pdf",
    page: 3,
    charStart: 1420,
    charEnd: 1685,
    quote:
      "She writes the forecast down in the margin of the log book, and says nothing to the morning shift.",
  },
  {
    id: "src_2",
    documentId: "doc_2",
    documentTitle: "Studio notebook 2020.md",
    kind: "md",
    page: null,
    charStart: 8120,
    charEnd: 8390,
    quote: "salt pews — the room eats itself over eight weeks. breath as erosion.",
  },
  {
    id: "src_3",
    documentId: "doc_3",
    documentTitle: "Grant application draft.docx",
    kind: "docx",
    page: 6,
    charStart: 2210,
    charEnd: 2470,
    quote:
      "A touring configuration could reach four venues within the funding period at a reduced material cost.",
  },
];

export const mockMemoryDetails: Record<string, MemoryDetail> = Object.fromEntries(
  mockMemories.map((memory) => {
    const detail: MemoryDetail = {
      ...memory,
      body:
        memory.snippet +
        "\n\nRecovered from the original material during processing. Muse keeps the wording as written and links it back to the passage it came from, so nothing here is a paraphrase.",
      entities: mockEntities
        .filter((entity) => memory.entityIds.includes(entity.id))
        .map(({ id, name, type }) => ({ id, name, type })),
      relationships: mockRelationships.filter((rel) => rel.memoryIds.includes(memory.id)),
      sources: mockSources.filter((source) => source.documentId === memory.documentId),
      relatedMemoryIds: mockMemories
        .filter((other) => other.id !== memory.id && other.documentId === memory.documentId)
        .map((other) => other.id),
    };
    return [memory.id, detail];
  }),
);

export const mockProcessingJobs: Record<string, ProcessingJob> = {
  job_1: {
    id: "job_1",
    documentId: "doc_4",
    documentTitle: "Voice memo transcript.txt",
    status: "running",
    progress: 0.58,
    currentStage: "linking_relationships",
    startedAt: "2026-08-17T21:30:00Z",
    completedAt: null,
    error: null,
    stages: [
      {
        stage: "uploading",
        label: "Receiving file",
        status: "done",
        startedAt: "2026-08-17T21:30:00Z",
        completedAt: "2026-08-17T21:30:12Z",
        detail: "21.3 KB received",
      },
      {
        stage: "parsing",
        label: "Reading document",
        status: "done",
        startedAt: "2026-08-17T21:30:12Z",
        completedAt: "2026-08-17T21:30:40Z",
        detail: "Plain text, 3,940 words",
      },
      {
        stage: "extracting",
        label: "Extracting ideas",
        status: "done",
        startedAt: "2026-08-17T21:30:40Z",
        completedAt: "2026-08-17T21:31:26Z",
        detail: "7 candidate memories",
      },
      {
        stage: "resolving_entities",
        label: "Resolving entities",
        status: "done",
        startedAt: "2026-08-17T21:31:26Z",
        completedAt: "2026-08-17T21:31:58Z",
        detail: "4 matched to existing entities",
      },
      {
        stage: "linking_relationships",
        label: "Linking relationships",
        status: "active",
        startedAt: "2026-08-17T21:31:58Z",
        completedAt: null,
        detail: "Comparing against 5 known relationships",
      },
      {
        stage: "temporal_analysis",
        label: "Placing in time",
        status: "pending",
        startedAt: null,
        completedAt: null,
        detail: null,
      },
      {
        stage: "indexing",
        label: "Indexing for search",
        status: "pending",
        startedAt: null,
        completedAt: null,
        detail: null,
      },
      {
        stage: "complete",
        label: "Done",
        status: "pending",
        startedAt: null,
        completedAt: null,
        detail: null,
      },
    ],
    discovered: {
      memories: 7,
      entities: 4,
      relationships: 2,
      timelineEvents: 1,
      highlights: [
        "A second mention of the tape-loop score",
        "New person: “Marta at the harbour office”",
        "References the Nightjar treatment by name",
      ],
    },
  },
};

export const mockDocumentDetails: Record<string, DocumentDetail> = Object.fromEntries(
  mockDocuments.map((doc) => {
    const detail: DocumentDetail = {
      ...doc,
      excerpt:
        "…the operator keeps the log in pencil so it can be corrected later, which is how the forecast survives at all. Everything after page nine is written in a different hand.",
      language: "en",
      memoryIds: mockMemories.filter((m) => m.documentId === doc.id).map((m) => m.id),
      entities: mockEntities.slice(0, 3).map(({ id, name, type }) => ({ id, name, type })),
      processing: doc.status === "processing" ? mockProcessingJobs["job_1"]! : null,
    };
    return [doc.id, detail];
  }),
);

export const mockTimeline: TimelineResponse = {
  earliest: "2018-05-02T00:00:00Z",
  latest: "2022-01-04T00:00:00Z",
  gaps: [
    { from: "2020-03-06T00:00:00Z", to: "2021-09-30T00:00:00Z", days: 573 },
    { from: "2018-08-14T00:00:00Z", to: "2019-03-11T00:00:00Z", days: 209 },
  ],
  events: [
    {
      id: "evt_1",
      title: "Salt Chapel first sketched",
      description: "Material experiments recorded in the studio notebook.",
      kind: "created",
      occurredAt: "2018-05-02T00:00:00Z",
      memoryIds: ["mem_2"],
      documentIds: ["doc_2"],
      entities: [{ id: "ent_saltchapel", name: "Salt Chapel", type: "work" }],
    },
    {
      id: "evt_2",
      title: "Nightjar treatment written",
      description: "24-page first treatment, including the forecast premise.",
      kind: "milestone",
      occurredAt: "2019-03-11T00:00:00Z",
      memoryIds: ["mem_1", "mem_5"],
      documentIds: ["doc_1"],
      entities: [{ id: "ent_nightjar", name: "Nightjar", type: "project" }],
    },
    {
      id: "evt_3",
      title: "Framing device removed",
      description: "Structural decision recorded mid-draft.",
      kind: "revisited",
      occurredAt: "2019-06-21T00:00:00Z",
      memoryIds: ["mem_6"],
      documentIds: ["doc_1"],
      entities: [{ id: "ent_nightjar", name: "Nightjar", type: "project" }],
    },
    {
      id: "evt_4",
      title: "Lisbon residency notes",
      description: "Delay experiments between sound and image.",
      kind: "created",
      occurredAt: "2020-01-18T00:00:00Z",
      memoryIds: ["mem_3"],
      documentIds: ["doc_2"],
      entities: [{ id: "ent_lisbon", name: "Lisbon", type: "place" }],
    },
    {
      id: "evt_5",
      title: "Work stops after Lisbon",
      description: "No further material recorded for 19 months.",
      kind: "abandoned",
      occurredAt: "2020-03-06T00:00:00Z",
      memoryIds: ["mem_3"],
      documentIds: ["doc_2"],
      entities: [{ id: "ent_nightjar", name: "Nightjar", type: "project" }],
    },
    {
      id: "evt_6",
      title: "Grant application drafted",
      description: "Chapel piece reframed as a touring work.",
      kind: "revisited",
      occurredAt: "2021-09-30T00:00:00Z",
      memoryIds: ["mem_4"],
      documentIds: ["doc_3"],
      entities: [{ id: "ent_harbour", name: "Harbour House Trust", type: "organization" }],
    },
    {
      id: "evt_7",
      title: "Last mention of slow light",
      description: "Single line in the closing pages of the notebook.",
      kind: "mention",
      occurredAt: "2022-01-04T00:00:00Z",
      memoryIds: ["mem_3"],
      documentIds: ["doc_2"],
      entities: [{ id: "ent_slowlight", name: "Slow light", type: "concept" }],
    },
  ],
};

export const mockRevivals: RevivalResult[] = [
  {
    id: "rev_1",
    memoryId: "mem_1",
    memoryTitle: "Radio operator hears tomorrow's weather",
    intent: "next_steps",
    createdAt: "2026-08-12T18:20:00Z",
    summary:
      "This premise sat untouched for seven years but three later fragments still lean on it. The strongest route forward keeps the forecast and drops the frame.",
    sources: [mockSources[0]!],
    suggestions: [
      {
        id: "sug_1",
        title: "Rebuild the second act around the log book",
        rationale:
          "Your 2019 decision to remove the letters frame already pointed here, and the Lisbon delay notes give the scene its texture.",
        nextSteps: [
          "Reread pages 9–14 of the treatment",
          "Draft one scene using only log-book entries",
          "Send the tape-loop note to Iris",
        ],
        supportingMemoryIds: ["mem_6", "mem_3"],
        confidence: 0.81,
      },
      {
        id: "sug_2",
        title: "Fold the chapel's erosion idea into the ending",
        rationale:
          "Salt Chapel and Nightjar share the slow-light motif; the erosion image supplies a physical ending the treatment lacks.",
        nextSteps: ["Compare the two endings side by side", "Test a salt-room final image"],
        supportingMemoryIds: ["mem_2"],
        confidence: 0.63,
      },
    ],
  },
  {
    id: "rev_2",
    memoryId: "mem_2",
    memoryTitle: "Cast the chapel pews in salt",
    intent: "reframe",
    createdAt: "2026-08-15T10:05:00Z",
    summary:
      "The touring question from 2021 answers the scale problem this idea was abandoned over.",
    sources: [mockSources[1]!, mockSources[2]!],
    suggestions: [
      {
        id: "sug_3",
        title: "One pew, four venues",
        rationale:
          "A single cast pew keeps the erosion premise intact while matching the funder's touring requirement.",
        nextSteps: ["Cost a single cast", "Revisit the grant draft's budget page"],
        supportingMemoryIds: ["mem_4"],
        confidence: 0.77,
      },
    ],
  },
];

export const mockProvenance: Record<string, ProvenanceDetail> = Object.fromEntries(
  mockSources.map((source) => {
    const detail: ProvenanceDetail = {
      source,
      context:
        "…" +
        source.quote +
        " The passage continues for another two paragraphs in the original file, unchanged since upload. Muse stores the offsets so this view always shows the material exactly as it was parsed.",
      extractedAt: "2026-07-04T08:20:00Z",
      extractorVersion: "muse-extract/0.0.0-frontend-mock",
      derivedMemoryIds: mockMemories
        .filter((m) => m.documentId === source.documentId)
        .map((m) => m.id),
      confidence: 0.84,
    };
    return [source.id, detail];
  }),
);

export const mockCorrections: Correction[] = [
  {
    id: "cor_1",
    targetType: "entity",
    targetId: "ent_iris",
    targetLabel: "Iris Okonkwo",
    kind: "merge",
    field: "aliases",
    value: "Iris O.",
    reason: "“Iris O.” in the notebook is the same person.",
    status: "applied",
    submittedAt: "2026-08-10T12:00:00Z",
  },
  {
    id: "cor_2",
    targetType: "memory",
    targetId: "mem_4",
    targetLabel: "Should the chapel piece be smaller?",
    kind: "retype",
    field: "kind",
    value: "decision",
    reason: "This was settled, not open.",
    status: "pending",
    submittedAt: "2026-08-16T09:30:00Z",
  },
];

export const mockSettings: Settings = {
  profile: { displayName: mockUser.displayName, email: mockUser.email },
  memory: { dormancyThresholdDays: 180, minConfidence: 0.6, autoResurfaceEnabled: true },
  processing: { ocrEnabled: true, languageHint: "en", retainOriginals: true },
  notifications: { processingComplete: true, weeklyResurfacing: true },
};

export const mockDashboard: DashboardOverview = {
  stats: {
    documents: mockDocuments.length,
    memories: mockMemories.length,
    entities: mockEntities.length,
    relationships: mockRelationships.length,
    dormantMemories: 3,
  },
  activeJobs: [mockProcessingJobs["job_1"]!],
  recentDocuments: mockDocuments.slice(0, 3),
  forgotten: [mockMemories[1]!, mockMemories[0]!, mockMemories[4]!],
  recentRevivals: mockRevivals,
};
