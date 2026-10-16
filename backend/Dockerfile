# Build context: repository root (see docker-compose.yml)
FROM python:3.13.3-slim

ENV VIRTUAL_ENV=/opt/venv \
    PATH=/opt/venv/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    FREEDOM_NODES_YAML=/app/nodes.yaml

COPY backend/requirements.txt backend/requirements-docker.txt /tmp/
RUN python -m venv /opt/venv \
 && iconv -f UTF-16 -t UTF-8 /tmp/requirements.txt | tr -d '\r' > /tmp/requirements-utf8.txt \
 && pip install --no-cache-dir -r /tmp/requirements-utf8.txt -r /tmp/requirements-docker.txt

WORKDIR /app/backend
COPY backend/ /app/backend/
COPY nodes.yaml /app/nodes.yaml

EXPOSE 8080
# watchfiles restarts the backend when backend/src, backend/config or nodes.yaml change,
# so `create-node` / `create-task-block` / a nodes.yaml edit go live without a manual restart.
# ("launch" skips __main__.py's own restart loop; watchfiles is the supervisor here)
CMD ["watchfiles", "--sigint-timeout", "5", "python . docker launch", "/app/backend/src", "/app/backend/config", "/app/nodes.yaml"]
