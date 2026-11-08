FROM python:3.13-slim@sha256:e48f59cdba69a3cbd9ed2cf0f348d90d45a8d350d98134cf1070bc106ee9ed90

# Set working directory
WORKDIR /app

# Copy pyproject.toml and install the package
COPY pyproject.toml .
COPY src/ src/
COPY README.md .

# Install the package in editable mode
RUN --mount=type=cache,mode=777,id=pip_cache,target=/var/cache/pip \
    pip install --cache-dir=/var/cache/pip -e .

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app && chown -R app:app /app
USER app

# Set default environment variables for serve command
ENV MYPVELWAEXPORTER_SERVE_URL=""
ENV MYPVELWAEXPORTER_SERVE_PORT="8000"
ENV MYPVELWAEXPORTER_SERVE_LOG_LEVEL="INFO"

# Default command using the installed console script
# Environment variables will be automatically picked up by typer
CMD ["mypv-elwa-prometheus-exporter", "serve"]