# Muse API

FastAPI HTTP/API foundation for Muse.

## Local development

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Health checks:
- `GET /health`
- `GET /api/v1/health`
- OpenAPI docs: `/docs`

## Persistent Sibyl storage

Muse keeps long-term memory in Sibyl's file-backed SQLite database. Configure its location with `SIBYL_DB_PATH`.

For local development:

```bash
mkdir -p data/sibyl
export SIBYL_DB_PATH=./data/sibyl/muse.sqlite3
```

If Muse runs in Docker, mount the host directory or a named persistent volume at the directory containing the configured database path. Do not store the database only in the container's writable layer.

### Production requirement

The intelligence service **must** have persistent disk attached to the directory containing `SIBYL_DB_PATH`. Replacing/restarting the application container must not remove the SQLite database. Production should provide scheduled snapshots/backups of the database and a tested restore procedure.

Do not migrate Sibyl data into Postgres and do not replace Sibyl's SQLite memory engine.

### Readiness and tenant isolation

Muse verifies the memory-store directory is present and writable and attempts to open the configured Sibyl database during memory-service initialization/readiness checks. Failure to open the store must be treated as a readiness failure.

All memory operations go through Muse's `MemoryService` boundary. `SibylMemoryService` selects the Sibyl tenant from the authenticated Muse user ID before reads/writes. The rest of Muse must not import the Sibyl SDK directly.

### Backups

Back up the configured SQLite database file using the deployment's persistent-volume backup mechanism. Keep backups outside the application container/volume and periodically verify that a backup can be restored to a separate local Sibyl instance.

This layer intentionally keeps Sibyl as the memory engine; it does not implement a second database or vector store.
