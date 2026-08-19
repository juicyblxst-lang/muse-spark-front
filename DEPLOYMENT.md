# Muse deployment

## Architecture

- Frontend: Next.js deployed to Vercel.
- Intelligence service: FastAPI/Python in the `backend/` Docker image.
- Database: Supabase Postgres.
- Files: private Supabase Storage bucket.
- Long-term memory: Sibyl SQLite on persistent backend disk.

## Backend deployment target

The backend deployment target is **Render Web Service with a persistent disk**.

This is an architectural requirement, not a free-tier choice. Muse cannot place Sibyl's SQLite database on ephemeral container storage because the memory database must survive restarts and redeploys.

Render's service configuration in `backend/render.yaml` mounts `/var/data` and places the Sibyl database at `/var/data/sibyl/muse.sqlite3`. The backend image installs the application, Docling ingestion dependencies, and the official Sibyl client during build, then starts FastAPI with Uvicorn automatically.

### Free-tier decision

Do not deploy the production intelligence service on a provider whose free plan has only ephemeral storage. A free compute tier is not sufficient if it cannot provide persistent disk. If a provider requires a paid plan for persistent disks, that cost is an explicit consequence of Sibyl's architecture rather than a reason to move SQLite into Postgres.

Render was selected for the deployment blueprint because its Web Service model supports a Python/Docker runtime, health checks, environment variables, and persistent disks. Verify current plan availability/pricing before production purchase; do not assume persistent disks are included in a free plan.

## Required environment

Production secrets are configured in the backend host, never in the frontend:

- `SUPABASE_URL`
- `SUPABASE_PUBLISHABLE_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`
- `LLM_API_KEY`
- `LLM_MODEL`
- `OPENCLAW_API_KEY`
- `CORS_ORIGINS`
- `SIBYL_DB_PATH=/var/data/sibyl/muse.sqlite3`

## Health/readiness

- `GET /health` is the liveness endpoint and must not depend on external services.
- `GET /ready` verifies required dependencies and returns `503` when the service cannot safely accept traffic.

Configure the platform health check against `/health`.

## Persistent data

Only the persistent disk contains the Sibyl SQLite database and local application data. Supabase remains the system of record for relational application data and uploaded files.

Backups/export of the Sibyl database must be part of the production operational procedure.

## HTTPS and CORS

The frontend and backend use HTTPS in deployment. CORS is explicitly configured with the deployed frontend origin; do not use `*` for an authenticated production API.

## Deployment verification

Before calling deployment complete:

1. Build the backend image from a clean checkout.
2. Start it with a mounted persistent directory.
3. Verify `/health` and `/ready`.
4. Write a test Sibyl memory.
5. Restart/redeploy the service with the same disk.
6. Verify the memory is still present.
7. Verify frontend requests use the backend HTTPS origin and no private secret appears in browser configuration.
8. Verify the persistent disk is backed up/exportable.
