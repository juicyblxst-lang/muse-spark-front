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

This layer intentionally contains no Sibyl/memory intelligence implementation yet.
