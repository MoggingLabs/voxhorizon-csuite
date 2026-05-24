# csuite-ingest. Batch worker (cron / `docker compose run`), not a service.
# Pulls read-only from source SaaS and upserts normalized rows into the
# self-hosted Supabase via PostgREST (service role, server-side only).
FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir "httpx>=0.27"
COPY src ./src
# Default run does every connector; pass names to limit (e.g. "audit_feed").
ENTRYPOINT ["python", "-m", "src.runner"]
