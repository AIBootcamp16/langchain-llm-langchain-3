FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# :white_check_mark: Install uv
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir uv

# Copy dependency files
COPY requirements.txt ./

# :white_check_mark: Create venv + install deps into /app/.venv
ENV UV_PROJECT_ENVIRONMENT=/app/.venv
RUN uv venv && uv pip install -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY scripts/ ./scripts/

# Path
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV PORT=8000
ENV PATH="/app/.venv/bin:$PATH"

# Healthcheck (using curl)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# :white_check_mark: run directly (PATH points to venv)
CMD ["uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "8000"]

