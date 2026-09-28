FROM python:3.12-slim AS base

# uv, statically, straight from its official image -- no pip bootstrap needed
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Install deps first (separate layer, cached across builds that only change
# application code) using the lockfile for reproducibility.
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-install-project --no-dev

# Now the actual application code.
COPY app ./app

RUN uv sync --locked --no-dev

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=3)" || exit 1

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
