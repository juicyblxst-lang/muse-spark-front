FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt requirements-ingestion.txt ./
RUN pip install --upgrade pip \
    && pip install -r requirements.txt -r requirements-ingestion.txt \
    && pip install "sibyl-memory-client>=0.6.1,<0.7"

COPY app ./app

RUN mkdir -p /var/data/sibyl

ENV SIBYL_DB_PATH=/var/data/sibyl/muse.sqlite3

EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
