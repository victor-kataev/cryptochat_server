# ---- builder ----
FROM python:3.14-rc-slim AS builder

WORKDIR /app

RUN pip install uv --no-cache-dir

# gcc needed to compile C extensions (e.g. httptools) that lack Python 3.14 wheels
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# ---- runtime ----
FROM python:3.14-rc-slim

WORKDIR /app

# Copy only the finished venv — no gcc or build tools in the final image
COPY --from=builder /app/.venv ./.venv

COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini ./

ENV PATH="/app/.venv/bin:$PATH"

CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
