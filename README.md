# Muse

Muse is a creative memory canvas. The web application lets an authenticated user upload source material, inspect processing status, search memories, trace provenance, and request revivals through a stable HTTP API boundary.

## Architecture

The frontend is intentionally transport-only. UI routes call the centralized MuseApi interface in src/lib/api; the HTTP adapter talks to the intelligence service at /api/v1. Document parsing, extraction, entity and relationship resolution, temporal analysis, provenance, retrieval, and revival remain backend responsibilities. The MemoryService/Sibyl and OpenClaw boundaries are not implemented in the frontend.

The repository currently contains the frontend and a small intelligence pipeline scaffold under apps/intelligence. Do not treat the scaffold as a completed production backend.

## Configuration

Required for a connected deployment:

- VITE_MUSE_API_MODE=http (the default; keep this explicit in deployment configuration)
- VITE_MUSE_API_URL (optional origin; omit when the API is served by the same origin)

For isolated UI development only, set VITE_MUSE_API_MODE=mock. Mock fixtures are demo data and must never be enabled in a user-facing or production environment.

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
