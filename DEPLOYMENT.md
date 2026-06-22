# MindMesh AI Deployment Guide

This guide provides instructions for deploying MindMesh AI locally and preparing it for cloud deployment (e.g., Render, Streamlit Community Cloud). 

MindMesh AI uses Docker for containerization, ensuring a consistent environment that properly includes dependencies like `ffmpeg` (required for Faster-Whisper).

## 1. Local Deployment with Docker

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/) installed.
- Your `.env` file created in the root directory with the necessary API keys (`GEMINI_API_KEY`, `GROQ_API_KEY`, `QDRANT_API_KEY`, `QDRANT_URL`).

### Using Docker Compose (Recommended)
Docker Compose automatically loads your `.env` file and maps your local directory for easy testing.

```bash
# Build and start the container
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop the container
docker-compose down
```
Access the app at: **http://localhost:8501**

### Using standard Docker commands
If you prefer not to use Compose:

```bash
# Build the image
docker build -t mindmesh-ai .

# Run the container (pass your .env file)
docker run -p 8501:8501 --env-file .env mindmesh-ai
```

---

## 2. GitHub Actions CI

This repository contains a GitHub Actions workflow (`.github/workflows/docker-build.yml`) that automatically verifies your code can be successfully containerized.

- **Trigger:** Pushes and Pull Requests to the `main` branch.
- **Action:** Checks out the code and runs a `docker build`.
- **Value:** Guarantees that the repository is always in a deployable state.

---

## 3. Production Deployment (Render / Streamlit Cloud)

Because MindMesh AI requires `ffmpeg` for audio processing via Faster-Whisper, a Docker-based deployment platform is highly recommended.

### Option A: Render (Recommended)
Render natively supports deploying from Dockerfiles and will automatically handle `ffmpeg`.
1. Go to [Render](https://render.com/).
2. Create a **New Web Service**.
3. Connect this GitHub repository.
4. Select **Docker** as the Runtime environment.
5. Add your Environment Variables (API Keys).
6. Click **Deploy Web Service**.

### Option B: Streamlit Community Cloud
If you prefer Streamlit Community Cloud, you will need to add a `packages.txt` file to your repository root containing `ffmpeg` to ensure the system dependency is installed alongside your Python `requirements.txt`.
