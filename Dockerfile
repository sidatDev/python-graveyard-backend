FROM python:3.13-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy dependency files first so Docker can cache this layer
# (uv.lock* means: copy it if it exists, skip silently if it doesn't)
COPY pyproject.toml ./
COPY uv.lock* ./

# Install dependencies into a virtual environment at /app/.venv
RUN uv sync --no-dev

# Copy the rest of the app
COPY . .

# Use the venv's Python/uvicorn directly
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

# Render injects $PORT at runtime — fall back to 8000 for local testing
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]