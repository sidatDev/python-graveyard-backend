# Backend Dockerfile - FastAPI + SQLModel + uv
#
# Build (from the backend/ folder, next to pyproject.toml):
#   docker build -t graveyard-backend .
#
# Run (pass secrets at runtime - never baked into the image):
#   docker run -p 8000:8000 \
#     -e DATABASE_URL="postgresql://..." \
#     -e JWT_SECRET_KEY="..." \
#     graveyard-backend
#
# Adjust the python version below (python3.12) if your pyproject.toml
# pins a different one under [project] requires-python.

FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

# build-essential + libpq-dev cover psycopg2 whether you're on the
# plain psycopg2 package or psycopg2-binary - safe to include either way.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1

# Install dependencies first (separate layer) so code changes don't
# force a full dependency reinstall on every build.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Now copy the actual application code.
COPY . .
RUN uv sync --frozen --no-dev

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
