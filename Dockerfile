# Dockerfile (pyproject.toml + uv.lock, strict locked install)
# ---- Stage 1: Builder ----
FROM python:3.12-slim AS builder

# Copy uv binary from Astral's official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Create app directory
RUN mkdir /app
WORKDIR /app

# Environment optimizations
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install build dependencies (compilers, headers, pkg-config, MySQL client dev libs)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc pkg-config libmariadb-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files first (for caching)
COPY pyproject.toml uv.lock /app/

# Install dependencies only (no project code yet)
# Install dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project

# Copy project code
ADD . /app

# Sync the project
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked

# Precompile bytecode
ENV UV_COMPILE_BYTECODE=1

# ---- Stage 2: Runtime ----
FROM python:3.12-slim

# Create non-root user and app dir
RUN useradd -m -r appuser && \
    mkdir /app && \
    chown -R appuser /app

WORKDIR /app

# Copy app code + .venv together
COPY --from=builder --chown=appuser:appuser /app /app

# Install only runtime libraries (no compilers)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmariadb-dev \
    && rm -rf /var/lib/apt/lists/*

# Ensure .venv/bin is first on PATH
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Switch to non-root user
RUN chown -R appuser:appuser /app
USER appuser

# Expose the application port
EXPOSE 8000

# Copy uv binary from Astral's official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Start the application using Gunicorn
# Force uv run for manage.py and Gunicorn
CMD ["uv", "run", "gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "alx_travel_app.wsgi:application"]
