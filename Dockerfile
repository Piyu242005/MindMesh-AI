FROM python:3.11-slim

# Prevent Python from writing .pyc files to disk and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies including ffmpeg for faster-whisper and curl for healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy the entire repository first
COPY . .

# Switch working directory to where the FastAPI app lives
WORKDIR /app/MindMesh-AI

# Install Python dependencies from the correct inner requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

# Add a non-root user for security and switch to it
RUN useradd -m appuser && chown -R appuser /app
USER appuser

# Healthcheck to ensure FastAPI is running properly
HEALTHCHECK CMD curl -f http://localhost:8000/health || exit 1

# Start the application with dynamic port injection for Render
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
