<div align="center">

<img src="https://readme-typing-svg.demolab.com?font=Inter&weight=600&size=40&pause=1000&color=7F00FF&center=true&vCenter=true&width=800&lines=MINDMESH+AI;Enterprise+Video+RAG;Autonomous+Knowledge+Base" alt="Typing SVG" />

# MindMesh AI

**Enterprise Video RAG & Autonomous Knowledge Base Platform**

[![Typing SVG](https://readme-typing-svg.demolab.com?font=Inter&weight=600&size=20&pause=1000&color=8B5CF6&center=true&vCenter=true&width=800&lines=Transcribe+Videos+with+Faster-Whisper;Smart+Routing+Between+Top+LLMs;Production-Grade+AI+Architecture;Fast%2C+Accurate%2C+and+Cost-Effective)](https://git.io/typing-svg)

[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)
[![Qdrant](https://img.shields.io/badge/Qdrant-000000?style=for-the-badge&logo=qdrant&logoColor=white)](https://qdrant.tech/)
[![Gemini](https://img.shields.io/badge/Google%20Gemini-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev/)
[![Groq](https://img.shields.io/badge/Groq-F55036?style=for-the-badge&logo=groq&logoColor=white)](https://groq.com)
[![Hugging Face](https://img.shields.io/badge/Hugging_Face-FFD21E?style=for-the-badge&logo=huggingface&logoColor=black)](https://huggingface.co/)
<br>
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](https://opensource.org/licenses/MIT)
[![Stars](https://img.shields.io/github/stars/Piyu242005/MindMesh-AI?style=flat-square)](https://github.com/Piyu242005/MindMesh-AI/stargazers)
[![Forks](https://img.shields.io/github/forks/Piyu242005/MindMesh-AI?style=flat-square)](https://github.com/Piyu242005/MindMesh-AI/network/members)

</div>

<br/>

## 📝 Overview

**MindMesh AI** is a production-grade enterprise application that transforms raw educational videos and courses into a deeply searchable, interactive AI knowledge base. It leverages Faster-Whisper for high-speed offline transcription, SentenceTransformers for chunk embedding, and Qdrant Cloud for blazing-fast vector retrieval. 

By orchestrating intelligent routing between Google Gemini Flash and Groq's LLaMA 3.3, MindMesh AI delivers scalable, context-aware answers directly linked to exact video timestamps.

---

## ✨ Key Features

| Feature | Description |
| :--- | :--- |
| ⚡ **Faster-Whisper Transcription** | Transcribes video courses at incredible speeds with GPU acceleration via CTranslate2. |
| 🔀 **Multi-LLM Gateway** | Unified interface combining models from Google Gemini and Groq with seamless failover. |
| 🛡️ **Automatic Fallback System** | Seamlessly reroutes failed API requests (e.g., 429 Quota limits) to backup providers. |
| 🌐 **Qdrant Cloud Integration** | High-performance semantic vector search completely removing local memory bottlenecks. |
| ⏱️ **Timestamp Deep Linking** | AI answers include precise timestamps tracing back to the exact moment in the source video. |
| 📊 **Advanced Analytics Dashboard** | Real-time telemetry tracking total requests, token counts, and LLM latency. |
| 🎨 **Premium UI/UX** | Dark-mode Streamlit interface with responsive sidebars, custom styling, and live transcription progress. |

---

## 🏗️ Architecture

```mermaid
graph TD
    %% Styling
    classDef user fill:#6366f1,stroke:#4f46e5,stroke-width:2px,color:#fff,rx:8px,ry:8px;
    classDef media fill:#8b5cf6,stroke:#7c3aed,stroke-width:2px,color:#fff,rx:8px,ry:8px;
    classDef embed fill:#10b981,stroke:#059669,stroke-width:2px,color:#fff,rx:8px,ry:8px;
    classDef vector fill:#f59e0b,stroke:#d97706,stroke-width:2px,color:#fff,rx:8px,ry:8px;
    classDef llm fill:#3b82f6,stroke:#2563eb,stroke-width:2px,color:#fff,rx:8px,ry:8px;
    
    U(("👤 User Upload")):::user -->|"Uploads Video"| UI["🖥️ Streamlit Frontend"]:::user
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
```

---

## 💻 Tech Stack

<div align="center">

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | ![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat-square&logo=streamlit&logoColor=white) HTML5, CSS3 |
| **Backend** | ![Python](https://img.shields.io/badge/Python_3.11-3776AB?style=flat-square&logo=python&logoColor=white) |
| **AI Models** | ![Gemini](https://img.shields.io/badge/Gemini_2.5_Flash-4285F4?style=flat-square&logo=google&logoColor=white) ![Groq](https://img.shields.io/badge/Groq_LLaMA_3.3-F55036?style=flat-square&logo=groq&logoColor=white) |
| **Data & Vectors** | ![Qdrant](https://img.shields.io/badge/Qdrant_Cloud-000000?style=flat-square&logo=qdrant&logoColor=white) ![SentenceTransformers](https://img.shields.io/badge/Sentence_Transformers-FFD21E?style=flat-square) |
| **Audio Processing**| `Faster-Whisper`, `FFmpeg` |

</div>

---

## 📂 Project Structure

```bash
MindMesh-AI/
├── backend/                 # ⚡ Core backend services
│   ├── embeddings.py        # SentenceTransformers encoding
│   ├── llm_manager.py       # Gemini/Groq Fallback Router
│   ├── retrieval.py         # Search & QA pipeline
│   └── transcription.py     # Faster-Whisper pipeline
├── pages/                   # 🖥️ Streamlit Views
│   ├── ai_chat.py           # Conversational Interface
│   ├── dashboard.py         # Analytics Dashboard
│   ├── settings.py          # LLM & Whisper Config
│   └── upload_center.py     # Video processing hub
├── app.py                   # Main Streamlit Entrypoint
├── qdrant_helper.py         # Qdrant Database driver
├── benchmark_transcription.py # Faster-Whisper benchmarking
├── validate_llm.py          # API Gateway Validation
├── requirements.txt         # Dependencies
└── .env.example             # Environment Variable Template
```

---

## ⚙️ Installation & Usage

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
Create a `.env` file in the root directory and add your API keys:
```env
# Google Gemini API
GEMINI_API_KEY=your_gemini_key

# Groq API
GROQ_API_KEY=your_groq_key

# Qdrant Cloud
QDRANT_URL=your_qdrant_cluster_url
QDRANT_API_KEY=your_qdrant_api_key

# Default Providers
LLM_PROVIDER=gemini
GEMINI_MODEL=gemini-2.5-flash
GROQ_MODEL=llama-3.3-70b-versatile
```

### 6. Run the Application
```bash
streamlit run app.py
```

---

## 🚀 How It Works

1. **Upload Video**: User uploads an `.mp4` or `.mkv` file via the Streamlit Upload Center.
2. **Audio Extraction & Transcription**: FFmpeg extracts the audio, and **Faster-Whisper** streams the transcription in real-time, yielding word-level segments and timestamps.
3. **Chunking & Vectorization**: Transcriptions are chunked into logical JSON blocks and vectorized using `sentence-transformers (bge-small-en-v1.5)`.
4. **Cloud Storage**: The vectors and metadata (timestamps, title) are upserted into **Qdrant Cloud**.
5. **Ask Question**: User submits a query via the AI Chat page.
6. **Smart Routing**: The `LLM Manager` directs the query along with Qdrant's semantic context to the primary cloud provider (Gemini). If rate limits are hit, it instantly fails-over to Groq.
7. **Delivery**: The user receives a contextual answer complete with exact source video timestamps.

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
  <sub>Built with ❤️ using Python, Streamlit, and modern Generative AI.</sub>
</div>
