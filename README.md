# Muse

Muse is a creative memory canvas. The web application lets an authenticated user upload source material, inspect processing status, search memories, trace provenance, and request revivals through a stable HTTP API boundary.

## Architecture

The frontend is intentionally transport-only. UI routes call the centralized MuseApi interface in src/lib/api; the HTTP adapter talks to the intelligence service at /api/v1. Document parsing, extraction, entity and relationship resolution, temporal analysis, provenance, retrieval, and revival remain backend responsibilities. The MemoryService/Sibyl and OpenClaw boundaries are not implemented in the frontend.

The repository currently contains the frontend and a small intelligence pipeline scaffold under apps/intelligence. Do not treat the scaffold as a completed production backend.

## Configuration

Required for a connected deployment:

- VITE_MUSE_API_URL (optional origin; omit when the API is served by the same origin)

## Development

npm install
npm run dev

Checks:

npm run build
npm run lint

## Deployment notes

The frontend must be deployed with the API origin and authentication/CORS configuration supplied by the backend host. Do not commit credentials or .env files. A deployment is not end-to-end ready until the backend implements the documented routes in src/lib/api/endpoints.ts and the connected flow has been tested with real authentication and user-scoped data.


## Intelligence service

The backend boundary can be run with `uvicorn app.main:app --app-dir apps/intelligence --port 8000` or built from `apps/intelligence/Dockerfile`. `GET /health` is the only operational endpoint currently verified by source inspection. Product routes intentionally return controlled `401` or `501` responses until authentication, persistence, and external intelligence configuration are supplied; they do not return fabricated user data.


## Remaining production configuration

The following values must be supplied by the deployment owner before private routes can be enabled:

- An authentication provider adapter that verifies the deployment's session or bearer token and returns the authenticated user id.
- A durable upload/object-storage implementation for document bytes.
- `MUSE_DATABASE_PATH` pointing at persistent storage; the Render configuration uses `/var/data/muse.sqlite3`.
- `MUSE_CORS_ORIGINS` set to the exact published frontend origin(s).
- The configured LLM provider, model, and credential for extraction, relationship, and temporal analysis.
- The external MemoryService/Sibyl and OpenClaw runtime configuration, when those boundaries are ready.

No default user, token, document, memory, LLM response, or external runtime is fabricated by the service.
