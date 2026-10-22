# Lönekrav in one image: the page, /api/v1, /mcp and /a2a on one port (Feature 004 research R10).
# Build from the repository root after `lonekrav-etl index`: docker compose up --build

# 1. The page
FROM node:22-slim AS page
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json frontend/.npmrc ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

# 2. The server, its models and the index
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.9.9 /uv /bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never \
    HF_HOME=/models PATH=/app/.venv/bin:$PATH
WORKDIR /app
# Milvus Lite writes a lock and its log beside the index, so the app user owns data/.
RUN useradd --create-home app && install -d -o app /app/data
COPY pyproject.toml uv.lock ./
# uv's download cache stays in a build cache, not in the image (it was 1.5 GB).
RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen --no-dev --no-install-project
COPY src/ src/
RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen --no-dev
# The pinned models, downloaded once here; the container then never goes to the network for them.
RUN lonekrav-etl fetch-models
COPY --chown=app data/processed/ data/processed/
COPY --chown=app data/lonekrav_milvus.db/ data/lonekrav_milvus.db/
COPY --chown=app data/lonekrav_milvus.db.vocab.json data/
COPY --from=page /frontend/dist/ frontend/dist/
USER app
ENV HF_HUB_OFFLINE=1 HOST=0.0.0.0 PORT=8000 PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["lonekrav-serve"]
