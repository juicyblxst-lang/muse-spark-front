/**
 * The documented Muse HTTP API contract.
 *
 * This is the ONLY place endpoint paths exist. No other endpoints may be
 * invented elsewhere in the frontend.
 */
export const API_BASE_URL = "/api/v1";

export const endpoints = {
  auth: {
    signIn: () => `/auth/sign-in`,
    signUp: () => `/auth/sign-up`,
    signOut: () => `/auth/sign-out`,
    me: () => `/auth/me`,
  },
  dashboard: {
    overview: () => `/dashboard`,
  },
  documents: {
    createUpload: () => `/uploads`,
    list: () => `/documents`,
    detail: (id: string) => `/documents/${id}`,
  },
  processing: {
    job: (jobId: string) => `/processing/${jobId}`,
  },
  memories: {
    search: () => `/memories/search`,
    detail: (id: string) => `/memories/${id}`,
    forgotten: () => `/memories/forgotten`,
  },
  graph: {
    connections: () => `/graph/connections`,
    timeline: () => `/graph/timeline`,
  },
  revival: {
    create: () => `/revivals`,
    list: () => `/revivals`,
    detail: (id: string) => `/revivals/${id}`,
  },
  provenance: {
    detail: (sourceId: string) => `/provenance/${sourceId}`,
  },
  corrections: {
    create: () => `/corrections`,
    list: () => `/corrections`,
  },
  settings: {
    get: () => `/settings`,
    update: () => `/settings`,
  },
} as const;
