# csuite-dispatcher. Reaches Docker only through the scope-limited socket proxy
# (DOCKER_HOST); never mounts the raw socket. Loopback-published by compose.
FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir "fastapi>=0.110" "httpx>=0.27" "uvicorn>=0.29" "docker>=7.0"
COPY src ./src
EXPOSE 8200
CMD ["uvicorn", "src.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8200"]
