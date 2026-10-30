# Stage 1: Build dependencies and wheels
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip wheel --no-cache-dir --no-deps --wheel-dir /build/wheels -r requirements.txt

# Stage 2: Final lightweight runtime container
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Install runtime system dependencies (curl for health check, ffmpeg for audio processing)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies from builder
COPY requirements.txt /app/
COPY --from=builder /build/wheels /wheels
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir /wheels/* && \
    rm -rf /wheels

# Copy application source
COPY . /app/

# Create non-root system user and secure runtime directories
RUN useradd -u 1000 -m -s /bin/bash krishiuser && \
    mkdir -p /app/.runtime/audio && \
    chown -R krishiuser:krishiuser /app

USER krishiuser

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/live || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
