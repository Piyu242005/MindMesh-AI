# 🎓 RAG-Based AI Course Assistant

**Author: Piyush Ramteke**

A **Retrieval-Augmented Generation (RAG)** system that transforms video course content into an intelligent, searchable knowledge base. This project enables users to ask natural language questions about video content and receive contextual answers with precise timestamps.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Pipeline Workflow](#pipeline-workflow)
- [Technologies Used](#technologies-used)
- [Installation](#installation)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Use Cases](#use-cases)
- [How It Works](#how-it-works)
- [Configuration](#configuration)
- [Future Improvements](#future-improvements)
- [Contributing](#contributing)
- [License](#license)

---

## 🌟 Overview

This RAG-based AI system processes video tutorials (specifically the **Sigma Web Development Course**) and creates a semantic search engine that allows learners to:

- Ask questions in natural language
- Get answers with specific video references
- Navigate directly to relevant timestamps in videos
- Search across multiple video lectures simultaneously

The system leverages **OpenAI Whisper** for speech-to-text transcription, **BGE-M3 embeddings** for semantic understanding, and **Ollama LLMs** (like Llama 3.2) for generating human-like responses.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🎬 **Video to Audio Conversion** | Automatically extracts audio from video files using FFmpeg |
| 🗣️ **Speech-to-Text Transcription** | Uses Whisper large-v2 model with Hindi-to-English translation |
| 📝 **Chunk-based Processing** | Splits transcriptions into timestamped segments for precise retrieval |
| 🔍 **Semantic Search** | Uses BGE-M3 embeddings for meaning-based search (not just keywords) |
| 🤖 **AI-Powered Responses** | Generates contextual answers using local LLMs via Ollama |
| ⏱️ **Timestamp Navigation** | Provides exact timestamps for relevant content |
| 💾 **Persistent Storage** | Saves embeddings using joblib for fast subsequent queries |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         RAG PIPELINE                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐      │
│  │  Videos  │───►│  Audio   │───►│  JSON    │───►│Embeddings│      │
│  │  (.mp4)  │    │  (.mp3)  │    │(transcr.)│    │  (.joblib)│     │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘      │
│       │               │               │               │             │
│       ▼               ▼               ▼               ▼             │
│    FFmpeg         Whisper        Chunking      BGE-M3 Model        │
│                   large-v2                                          │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                        QUERY PIPELINE                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐      │
│  │  User    │───►│  Query   │───►│ Cosine   │───►│   LLM    │      │
│  │  Query   │    │ Embedding│    │Similarity│    │ Response │      │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘      │
│       │               │               │               │             │
│       ▼               ▼               ▼               ▼             │
│  Natural Lang     BGE-M3         Top-5 Chunks    Llama 3.2         │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Pipeline Workflow

### Stage 1: Video to Audio Conversion
```python
# video_to_mp3.py
FFmpeg extracts audio → Creates .mp3 files with structured naming
```

### Stage 2: Audio Transcription
```python
# mp3_to_json.py
Whisper model → Transcribes audio → Generates timestamped JSON chunks
```

### Stage 3: Embedding Generation
```python
# preprocess_json.py
BGE-M3 model → Creates embeddings → Stores in embeddings.joblib
```

### Stage 4: Query Processing
```python
# process_incoming.py
User query → Semantic search → LLM generates contextual response
```

---

## 🛠️ Technologies Used

| Category | Technology |
|----------|------------|
| **Speech Recognition** | OpenAI Whisper (large-v2) |
| **Embeddings** | BGE-M3 (via Ollama) |
| **LLM** | Llama 3.2 / DeepSeek-R1 (via Ollama) |
| **Audio Processing** | FFmpeg |
| **Data Processing** | Pandas, NumPy, Scikit-learn |
| **Storage** | Joblib |
| **API Server** | Ollama (localhost:11434) |
| **Language** | Python 3.x |

---

## 📦 Installation

### Prerequisites

1. **Python 3.8+** installed
2. **FFmpeg** installed and in PATH
3. **Ollama** installed and running

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd "Rag Based AI"
```

### Step 2: Install Python Dependencies

```bash
pip install whisper pandas numpy scikit-learn joblib requests
```

### Step 3: Install Ollama Models

```bash
# Install embedding model
ollama pull bge-m3

# Install LLM (choose one)
ollama pull llama3.2
# or
ollama pull deepseek-r1
```

### Step 4: Install Whisper

```bash
cd whisper
pip install -e .
```

---

## 🚀 Usage

### 1. Convert Videos to Audio

Place your video files in the `videos/` folder and run:

```bash
python video_to_mp3.py
```

### 2. Transcribe Audio Files

```bash
python mp3_to_json.py
```

This creates JSON files with timestamped transcriptions in the `jsons/` folder.

### 3. Generate Embeddings

```bash
python preprocess_json.py
```

This creates `embeddings.joblib` containing all chunk embeddings.

### 4. Ask Questions

```bash
python process_incoming.py
```

Example interaction:
```
Ask a Question: Where is HTML concluded in this course?

Response: HTML is concluded in Video 13 titled "Entities, Code tag and more on HTML". 
You can find the conclusion at around 8:40 (520 seconds). The instructor also 
mentions in Video 14 "Introduction to CSS" at the beginning (around 0:05) that 
HTML has been completed. I recommend watching Video 13 from timestamp 8:40 onwards 
for the HTML conclusion!
```

---

## 📁 Project Structure

```
Rag Based AI/
│
├── video_to_mp3.py        # Converts videos to MP3 audio files
├── mp3_to_json.py         # Transcribes audio using Whisper
├── preprocess_json.py     # Creates embeddings from transcriptions
├── process_incoming.py    # Main query processing script
│
├── embeddings.joblib      # Stored embeddings database
├── prompt.txt             # Last generated prompt (for debugging)
├── response.txt           # Last LLM response (for debugging)
│
├── Audios/                # Converted audio files (.mp3)
├── jsons/                 # Transcription JSON files
│   ├── 01_Installing VS Code & How Websites Work.mp3.json
│   ├── 02_Your First HTML Website.mp3.json
│   ├── ... (18 video transcriptions)
│
├── whisper/               # OpenAI Whisper submodule
│   ├── whisper/           # Core Whisper library
│   ├── tests/             # Test files
│   └── notebooks/         # Jupyter notebooks
│
└── README.md              # This file
```

---

## 💡 Use Cases

### 🎓 Educational Platforms

| Use Case | Description |
|----------|-------------|
| **Course Navigation** | Help students find specific topics in lengthy video courses |
| **Study Assistant** | Answer questions about course content with precise references |
| **Revision Helper** | Quickly locate topics for exam preparation |
| **Content Discovery** | Search across multiple lectures simultaneously |

### 🏢 Enterprise Applications

| Use Case | Description |
|----------|-------------|
| **Training Videos** | Make corporate training searchable |
| **Meeting Recordings** | Find specific discussions in recorded meetings |
| **Webinar Archives** | Search through past webinars efficiently |
| **Knowledge Base** | Create searchable video documentation |

### 📺 Content Creators

| Use Case | Description |
|----------|-------------|
| **Viewer Support** | Help viewers find specific content |
| **Content Indexing** | Automatic chapter generation for videos |
| **FAQ Automation** | Auto-answer common viewer questions |
| **Accessibility** | Make video content accessible via text search |

### 🔬 Research Applications

| Use Case | Description |
|----------|-------------|
| **Lecture Archives** | Search through academic lecture recordings |
| **Interview Analysis** | Find specific quotes in recorded interviews |
| **Conference Videos** | Navigate through conference presentations |
| **Podcast Search** | Make podcast episodes searchable |

---

## ⚙️ How It Works

### 1. Transcription Process

The Whisper model processes audio files and generates timestamped segments:

```json
{
    "number": "1",
    "title": "Installing VS Code & How Websites Work",
    "start": 0.0,
    "end": 3.5,
    "text": "From today's video, we will start the Sigma Web Development course."
}
```

### 2. Embedding Generation

Each text chunk is converted to a 1024-dimensional vector using BGE-M3:

```python
embedding = create_embedding([chunk_text])  # Returns [1024] vector
```

### 3. Semantic Search

User queries are embedded and compared using cosine similarity:

```python
similarities = cosine_similarity(all_embeddings, [query_embedding])
top_5_chunks = get_top_n(similarities, n=5)
```

### 4. Response Generation

Top chunks are formatted into a prompt and sent to the LLM:

```python
prompt = f"""
Here are video subtitle chunks: {relevant_chunks}
User question: {user_query}
Answer with video references and timestamps...
"""
response = llm.generate(prompt)
```

---

## ⚙️ Configuration

### Change Embedding Model

In `preprocess_json.py` and `process_incoming.py`:

```python
"model": "bge-m3"  # Change to preferred embedding model
```

### Change LLM Model

In `process_incoming.py`:

```python
"model": "llama3.2"  # Options: llama3.2, deepseek-r1, mistral, etc.
```

### Adjust Number of Retrieved Chunks

In `process_incoming.py`:

```python
top_results = 5  # Increase for more context, decrease for speed
```

### Change Whisper Model

In `mp3_to_json.py`:

```python
model = whisper.load_model("large-v2")  # Options: tiny, base, small, medium, large, large-v2
```

---

## 🔮 Future Improvements

- [ ] **Web Interface** - Create a Streamlit/Gradio UI for easier interaction
- [ ] **Multi-language Support** - Extend beyond Hindi-English translation
- [ ] **Real-time Processing** - Process videos as they're uploaded
- [ ] **GPU Acceleration** - Optimize for faster embedding generation
- [ ] **Vector Database** - Replace joblib with Chroma/Pinecone for scalability
- [ ] **Caching Layer** - Cache common queries for faster responses
- [ ] **API Endpoints** - Create REST API for integration with other systems
- [ ] **Video Player Integration** - Direct links to video timestamps
- [ ] **Batch Processing** - Handle multiple queries simultaneously
- [ ] **Fine-tuning** - Custom model training on domain-specific content

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

Please read [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) for guidelines.

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🙏 Acknowledgments

- **OpenAI Whisper** - For the excellent speech recognition model
- **Ollama** - For making local LLM deployment easy
- **BGE-M3** - For the powerful multilingual embedding model
- **Sigma Web Development Course** - The course content used for demonstration

---

## 📞 Contact

For questions or support, please open an issue in the repository.

---

<p align="center">
  Made with ❤️ by <strong>Piyush Ramteke</strong> for better learning experiences
</p>
