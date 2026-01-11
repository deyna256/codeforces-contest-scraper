# Use a specialized uv image for building
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Do not install development dependencies
ENV UV_NO_DEV=1

# Copy from the cache instead of linking since it's a container
ENV UV_LINK_MODE=copy

WORKDIR /app

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*

# Install dependencies separately to leverage cache
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

# Copy source code
COPY src/ ./src/
COPY pyproject.toml uv.lock ./

# Install the project and install Playwright dependencies/browsers
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Install Playwright browsers (only Chromium)
RUN uv run playwright install chromium --with-deps

# Final stage - using uv image as in example
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

# Install runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Copy the virtual environment from the builder stage
COPY --from=builder /app/.venv /.venv

# Copy Playwright browsers from the builder stage
COPY --from=builder /root/.cache/ms-playwright /root/.cache/ms-playwright

# Environment variables from example
ENV PATH="/.venv/bin:$PATH" \
    VIRTUAL_ENV="/.venv" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    UV_NO_DEV=1

WORKDIR /app

# Copy necessary files
COPY src/ .
COPY entrypoints/ /entrypoints/
RUN chmod +x /entrypoints/*.sh

# Install Playwright system dependencies in the final image
RUN python3 -m playwright install-deps chromium

EXPOSE 8000

# Use the entrypoint script from example
CMD ["/entrypoints/run.sh"]
