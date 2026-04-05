# ---- Base Stage ----
FROM python:3.13-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# ---- Builder Stage ----
# Compiles and isolates dependencies without bloating the final image
FROM base AS builder

# Install uv using standard pip as requested
RUN pip install --no-cache-dir uv

WORKDIR /app

# Copy dependency files *first* to maximize Docker layer caching
COPY pyproject.toml uv.lock ./

# Install production dependencies into a virtual environment in /app/.venv
RUN uv sync --frozen --no-dev --no-install-project

# ---- Final Runtime Stage ----
# This image contains ONLY the app and its dependencies—no build tools, pip, or uv.
FROM base AS final

# Create a non-root group and user (Security Sandbox Best Practice)
RUN groupadd -r djangouser && useradd -r -m -g djangouser djangouser

WORKDIR /app

# Copy the pre-built virtual environment from the builder
COPY --from=builder --chown=djangouser:djangouser /app/.venv /app/.venv

# Update PATH so the python runtime prioritizes the virtual environment packages seamlessly
ENV PATH="/app/.venv/bin:$PATH"

# Copy the actual application code into the container
COPY --chown=djangouser:djangouser . .

# Switch to the non-root user before running the application
USER djangouser

# Expose Render's default routing port
EXPOSE 8000

# Run the app with Gunicorn dynamically calculating worker counts and binding to $PORT
CMD gunicorn config.wsgi:application --bind "0.0.0.0:${PORT:-8000}" --workers "$((2 * $(nproc) + 1))" --worker-tmp-dir /dev/shm --timeout 120