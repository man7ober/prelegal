FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

COPY pyproject.toml uv.lock ./
COPY prelegal_api ./prelegal_api

RUN uv sync --locked --no-dev --no-cache

ENV PRELEGAL_DATABASE_PATH=/app/data/prelegal.db

EXPOSE 8000

CMD ["uv", "run", "--no-sync", "uvicorn", "prelegal_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
