<div align="center">
  <img src="LOGO.png" width="180">

  <h1>MindMesh AI</h1>

  <p>
    Transform Video Courses into Intelligent Knowledge Networks
  </p>
</div>

**Enterprise Video RAG & Autonomous Knowledge Base Platform**

[![Typing SVG](https://readme-typing-svg.demolab.com?font=Inter&weight=600&size=20&pause=1000&color=8B5CF6&center=true&vCenter=true&width=800&lines=Transcribe+Videos+with+Faster-Whisper;Smart+Routing+Between+Top+LLMs;Production-Grade+AI+Architecture;Fast%2C+Accurate%2C+and+Cost-Effective)](https://git.io/typing-svg)

[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Qdrant](https://img.shields.io/badge/Qdrant-000000?style=for-the-badge&logo=qdrant&logoColor=white)](https://qdrant.tech/)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-326CE5?style=for-the-badge&logo=kubernetes&logoColor=white)](https://kubernetes.io)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)
[![Gemini](https://img.shields.io/badge/Google%20Gemini-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev/)
[![Groq](https://img.shields.io/badge/Groq-F55036?style=for-the-badge&logo=groq&logoColor=white)](https://groq.com)
<br>
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](https://opensource.org/licenses/MIT)
[![Stars](https://img.shields.io/github/stars/Piyu242005/MindMesh-AI?style=flat-square)](https://github.com/Piyu242005/MindMesh-AI/stargazers)
[![Forks](https://img.shields.io/github/forks/Piyu242005/MindMesh-AI?style=flat-square)](https://github.com/Piyu242005/MindMesh-AI/network/members)

</div>

<br/>

## 📝 Overview

**MindMesh AI** is a production-grade enterprise application that transforms raw educational videos and courses into a deeply searchable, interactive AI knowledge base. Rebuilt from the ground up on **FastAPI**, **HTMX**, and **Tailwind CSS**, it brings bleeding-edge responsiveness while dropping frontend bloat.

By orchestrating intelligent routing between Google Gemini 2.5 Flash and Groq's LLaMA 3.3, coupled with **Qdrant Cloud** and **Faster-Whisper** offline transcription, MindMesh AI delivers highly scalable, context-aware answers directly linked to exact video timestamps. The system is hardened for production with **Docker**, **Kubernetes (K8s)** manifests, and a fully integrated **Telegram Ecosystem** for active system monitoring.

---

## 📸 Screenshots

*(Add screenshots of the Modern Dashboard, Chat Interface, and Onboarding Modal here)*

---

## 🌐 Live Demo

*(Insert Live URL Here once deployed)*

---

## ✨ Features

| Feature | Description |
| :--- | :--- |
| ⚡ **Faster-Whisper Transcription** | Transcribes video courses at incredible speeds with GPU acceleration via CTranslate2. |
| 🔀 **Multi-LLM Gateway** | Unified interface combining models from Google Gemini and Groq with seamless failover. |
| 🛡️ **Automatic Fallback System** | Seamlessly reroutes failed API requests (e.g., 429 Quota limits) to backup providers. |
| 📱 **Telegram Ecosystem** | Real-time alerts for server health, application errors, daily analytics, and CI/CD deployment status pushed directly to your phone. |
| 🌐 **Qdrant Cloud Integration** | High-performance semantic vector search completely removing local memory bottlenecks. |
| ⏱️ **Timestamp Deep Linking** | AI answers include precise timestamps tracing back to the exact moment in the source video. |
| 📊 **Advanced Analytics Dashboard** | Real-time telemetry tracking total requests, uploads, Qdrant vectors, and System Health. |
| 🎨 **Premium UI/UX** | Glassmorphism styling, dark-mode, first-time user onboarding modal, and snappy HTMX interactions. |

---

## 🏗️ Architecture Diagram

```mermaid
graph TD
    %% Styling
    classDef user fill:#6366f1,stroke:#4f46e5,stroke-width:2px,color:#fff,rx:8px,ry:8px;
    classDef media fill:#8b5cf6,stroke:#7c3aed,stroke-width:2px,color:#fff,rx:8px,ry:8px;
    classDef embed fill:#10b981,stroke:#059669,stroke-width:2px,color:#fff,rx:8px,ry:8px;
    classDef vector fill:#f59e0b,stroke:#d97706,stroke-width:2px,color:#fff,rx:8px,ry:8px;
    classDef llm fill:#3b82f6,stroke:#2563eb,stroke-width:2px,color:#fff,rx:8px,ry:8px;
    classDef devops fill:#e11d48,stroke:#be123c,stroke-width:2px,color:#fff,rx:8px,ry:8px;
    
    U(("👤 User Upload")):::user -->|"Uploads Video"| UI["🖥️ FastAPI + HTMX"]:::user
    UI -->|"FFmpeg Audio Extraction"| EXT["🎵 MP3 Extractor"]:::media
    EXT -->|"Faster-Whisper (CTranslate2)"| TX["🗣️ Transcription Engine"]:::media
    
    TX -->|"Chunking JSON"| C["📄 Data Chunker"]:::media
    C -->|"SentenceTransformers (BGE-Small)"| EMB["💡 Embedding Generation"]:::embed
    
    EMB -->|"Upsert Vectors"| Q["☁️ Qdrant Cloud Cluster"]:::vector
    
    UI -->|"User Chat Query"| QRY["❓ User Query"]:::user
    QRY -->|"Semantic Search"| Q
    
    Q -->|"Retrieved Context"| LLMG["⚡ LLM Manager Gateway"]:::llm
    
    LLMG -.->|"Primary"| GEM["🔵 Gemini 2.5 Flash"]:::llm
    LLMG -.->|"Fallback"| GRQ["🟠 Groq LLaMA 3.3"]:::llm
    
    Health["⏱️ APScheduler"]:::devops -->|"System Monitors"| TG["📱 Telegram Ecosystem"]:::devops
    LLMG -->|"Query Analytics"| TG
```

---

## 💻 Tech Stack

<div align="center">

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | ![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white) `HTMX`, `Tailwind CSS`, `Jinja2` |
| **Backend Core** | ![Python](https://img.shields.io/badge/Python_3.11-3776AB?style=flat-square&logo=python&logoColor=white) `APScheduler`, `python-telegram-bot` |
| **AI Models** | ![Gemini](https://img.shields.io/badge/Gemini_2.5_Flash-4285F4?style=flat-square&logo=google&logoColor=white) ![Groq](https://img.shields.io/badge/Groq_LLaMA_3.3-F55036?style=flat-square&logo=groq&logoColor=white) |
| **Data & Vectors** | ![Qdrant](https://img.shields.io/badge/Qdrant_Cloud-000000?style=flat-square&logo=qdrant&logoColor=white) ![SentenceTransformers](https://img.shields.io/badge/Sentence_Transformers-FFD21E?style=flat-square) |
| **DevOps & Infra**| ![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white) ![Kubernetes](https://img.shields.io/badge/Kubernetes-326CE5?style=flat-square&logo=kubernetes&logoColor=white) `GitHub Actions` |

</div>

---

## 🗺️ Roadmap

- [x] Streamlit to FastAPI + HTMX Migration
- [x] Containerize Application (Docker multi-stage build)
- [x] Integrate Kubernetes Manifests for Production K8s Deployment
- [x] Telegram Operations & Alerts Ecosystem
- [x] Implement First-time User Onboarding
- [ ] Add User Authentication (OAuth/JWT)
- [ ] Setup Persistent Database for user profiles
- [ ] YouTube Video URL Parsing & Downloading

---

## 🚀 Deployment

MindMesh AI is fully containerized and production-ready for Kubernetes. 

See the dedicated documentation for detailed deployment instructions:
- [Docker Deployment Guide](DEPLOYMENT.md)
- [Kubernetes Setup Guide](KUBERNETES.md)
- [Telegram Ecosystem Setup](TELEGRAM_SETUP.md)

### Quick Docker Run
```bash
docker build -t mindmesh-ai .
docker run -d -p 8000:8000 --env-file .env mindmesh-ai
```

---

## ⚙️ Local Installation & Usage

### 1. Clone the Repository
```bash
git clone https://github.com/Piyu242005/MindMesh-AI.git
cd MindMesh-AI
```

### 2. Set up a Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install System Dependencies
Install [FFmpeg](https://ffmpeg.org/download.html) and ensure it is added to your system `PATH`.

### 4. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables
Create a `.env` file in the root directory (using `.env.example` as a template):
```env
# Google Gemini API
GEMINI_API_KEY=your_gemini_key

# Groq API
GROQ_API_KEY=your_groq_key

# Qdrant Cloud
QDRANT_URL=your_qdrant_cluster_url
QDRANT_API_KEY=your_qdrant_api_key

# Telegram Setup
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_ADMIN_CHAT_ID=your_chat_id
```

### 6. Run the Application
```bash
python main.py
```
Access the application at `http://localhost:8000`.

---

## 👨‍💻 Author

### **Piyush Ramteke**
**Data Scientist | AI Engineer | Python Developer**

*Passionate about building scalable AI systems, Generative AI applications, and elegant data solutions.*

[![GitHub](https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/Piyu242005)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white)](https://linkedin.com/in/piyush-ramteke)
[![Hugging Face](https://img.shields.io/badge/Hugging_Face-FFD21E?style=for-the-badge&logo=huggingface&logoColor=black)](https://huggingface.co/Piyu242005)
[![Portfolio](https://img.shields.io/badge/Portfolio-8B5CF6?style=for-the-badge&logo=vercel&logoColor=white)](https://piyushramteke.dev)

---

<div align="center">
  <sub>Built with ❤️ using FastAPI, HTMX, and modern Generative AI.</sub>
</div>
