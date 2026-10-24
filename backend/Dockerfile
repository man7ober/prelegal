FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

COPY backend/pyproject.toml backend/uv.lock ./
COPY backend/prelegal_api ./prelegal_api
COPY catalog.json ./catalog.json
COPY templates ./templates

RUN uv sync --locked --no-dev --no-cache

ENV PRELEGAL_DATABASE_PATH=/app/data/prelegal.db \
    PRELEGAL_PROJECT_ROOT=/app

EXPOSE 8000

CMD ["uv", "run", "--no-sync", "uvicorn", "prelegal_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
