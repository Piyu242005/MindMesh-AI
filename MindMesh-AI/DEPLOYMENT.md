# Deployment Guide

This guide covers deploying MindMesh-AI across various environments.

## Local Development

1. **Clone the repository:**
   ```bash
   git clone <repo-url>
   cd MindMesh-AI
   ```
2. **Install dependencies:**
   Make sure you have Python 3.11 installed. Also, install `ffmpeg` on your system.
   ```bash
   pip install -r requirements.txt
   ```
3. **Set up Environment Variables:**
   Copy `.env.example` to `.env` and fill in your keys (Qdrant, Gemini, Groq).
   ```bash
   cp .env.example .env
   ```
4. **Run the App:**
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

## Docker Deployment

This repository includes a multi-stage `Dockerfile` optimized for production.

1. **Build the image:**
   ```bash
   docker build -t mindmesh-ai .
   ```
2. **Run the container:**
   ```bash
   docker run -p 8000:8000 --env-file .env mindmesh-ai
   ```

## Docker Compose

We provide a `docker-compose.yml` to run the web application easily. Qdrant is hosted on Qdrant Cloud.

```bash
docker-compose up -d --build
```

## Deploying to Render

1. Create a new **Web Service** on Render.
2. Connect your GitHub repository.
3. Select the **Docker** runtime.
4. Render will automatically detect the `Dockerfile` and build it.
5. In the **Environment Variables** section, add all your variables from `.env`.
6. Click **Deploy**.

## Deploying to Railway

1. Create a new Project on Railway.
2. Choose **Deploy from GitHub repo**.
3. Railway will auto-detect the `Dockerfile`.
4. Add your Environment Variables in the **Variables** tab.
5. Railway will provision a public URL automatically.
