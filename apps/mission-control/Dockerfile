# Mission Control: the sole UI. Loopback-published by compose, reached via
# Tailscale Serve. Talks to the dispatcher over csuite_net and reads Supabase.
FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir "fastapi>=0.110" "httpx>=0.27" "python-multipart>=0.0.9" "uvicorn>=0.29"
COPY src ./src
EXPOSE 3100
CMD ["uvicorn", "src.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "3100"]
