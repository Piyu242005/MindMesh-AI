# Deployment Guide

Deploying MindMesh AI is straightforward. Because the transcription (Whisper) and embedding processes happen locally on the server, you need an environment with adequate RAM (at least 2GB+ depending on the Whisper model used). 

## Required Environment Variables

Regardless of where you deploy, you must set these environment variables securely in your host's dashboard:

```env
GEMINI_API_KEY=your_gemini_key
GROQ_API_KEY=your_groq_key
QDRANT_URL=https://your-cluster-url.qdrant.io
QDRANT_API_KEY=your_qdrant_api_key
QDRANT_COLLECTION=mindmesh_courses
```

---

## ☁️ Option 1: Streamlit Community Cloud (Recommended for Demos)

Streamlit Community Cloud is free and seamlessly integrates with GitHub.

1. Push your code to a public GitHub repository.
2. Go to [share.streamlit.io](https://share.streamlit.io/) and log in.
3. Click **New app** and select your repository, branch, and `app.py` as the main file.
4. Before clicking Deploy, click **Advanced settings**.
5. Paste your Environment Variables (from above) into the Secrets block.
6. Click **Deploy**.

*Note: Streamlit Cloud restricts CPU and RAM. You should configure `faster-whisper` to use the `tiny` or `base` model in `pages/settings.py` to avoid memory limits.*

---

## 🚀 Option 2: Render (Recommended for Production)

Render provides a robust PaaS environment perfect for heavy Python applications.

1. Log in to [Render](https://render.com/).
2. Create a new **Web Service**.
3. Connect your GitHub repository.
4. Set the environment to `Python 3`.
5. Build Command: `pip install -r requirements.txt && apt-get update && apt-get install -y ffmpeg`
6. Start Command: `streamlit run app.py --server.port $PORT`
7. In the **Environment** tab, add all your required `Environment Variables`.
8. Select an instance tier (at least **Standard** 2GB RAM is recommended).
9. Click **Create Web Service**.

---

## 🚂 Option 3: Railway

Railway offers Docker-based and Nixpacks-based seamless deployments.

1. Log in to [Railway](https://railway.app/).
2. Click **New Project** -> **Deploy from GitHub repo**.
3. Once the repository is linked, go to the **Variables** tab and add your required keys.
4. Under the **Settings** tab -> **Build**, add a custom apt package for FFmpeg:
   - Create a file named `apt.txt` in your repo root containing `ffmpeg`.
5. Ensure the start command is `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`.
6. Deploy the project.
