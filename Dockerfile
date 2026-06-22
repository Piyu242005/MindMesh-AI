FROM python:3.11-slim

# Prevent Python from writing .pyc files to disk and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies including ffmpeg for faster-whisper and curl for healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy requirements file first for better layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose the Streamlit port
EXPOSE 8501

# Add a non-root user for security and switch to it
RUN useradd -m appuser && chown -R appuser /app
USER appuser

# Healthcheck to ensure Streamlit is running properly
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Entrypoint to run the Streamlit app
ENTRYPOINT ["streamlit", "run", "MindMesh AI/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
