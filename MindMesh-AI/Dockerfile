# Builder stage
FROM python:3.11-slim as builder

WORKDIR /app
COPY requirements.txt .

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends gcc build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# Final stage
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (ffmpeg for whisper, curl for healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg curl \
    && rm -rf /var/lib/apt/lists/*

# Copy wheels and install
COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .
RUN pip install --no-cache /wheels/*

# Create non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Copy app code
COPY . .

# Expose port
EXPOSE 8000

# Healthcheck
HEALTHCHECK CMD curl -f http://localhost:8000/health || exit 1

# Start the application
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
