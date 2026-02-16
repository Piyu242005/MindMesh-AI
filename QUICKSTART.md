# 🚀 Quick Start Guide

## Installation

### 1. Install Python Dependencies

```powershell
pip install -r requirements.txt
```

### 2. Configure Environment

```powershell
# Copy the environment template
Copy-Item .env.example .env

# Edit .env with your settings (optional - defaults work for local Ollama)
notepad .env
```

### 3. Install Ollama Models

```powershell
# Install embedding model
ollama pull bge-m3

# Install LLM (choose one or both)
ollama pull llama3.2
ollama pull deepseek-r1
```

### 4. Ensure FFmpeg is Installed

Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH.

---

## Usage

### Option 1: Run the Complete Pipeline

```powershell
# Run all stages (video → audio → transcription → embeddings → query)
python pipeline.py

# Run specific stages only
python pipeline.py --stages 3 4  # Only embedding + query

# Force re-processing of existing files
python pipeline.py --force
```

### Option 2: Run Individual Stages

```powershell
# Stage 1: Convert videos to MP3
python video_to_mp3_new.py

# Stage 2: Transcribe audio to JSON
python mp3_to_json_new.py

# Stage 3: Generate embeddings
python preprocess_json_new.py

# Stage 4: Interactive query mode
python process_incoming_new.py
```

### Option 3: Launch Web UI

```powershell
# Launch Streamlit web interface
python pipeline.py --ui

# Or directly
streamlit run app.py
```

---

## Command-Line Options

### Video to MP3
```powershell
python video_to_mp3_new.py --input videos --output Audios --force
```

### Transcription
```powershell
python mp3_to_json_new.py --model base --language hi --force
```

### Embedding Generation
```powershell
python preprocess_json_new.py --use-chromadb --window 30 --overlap 10
```

### Query Processing
```powershell
# Single query
python process_incoming_new.py --query "Where is HTML concluded?"

# Interactive mode with specific model
python process_incoming_new.py --model llama3.2 --top-k 5

# Disable reranking for faster results
python process_incoming_new.py --no-reranker
```

---

## Testing

### Run Unit Tests
```powershell
pytest tests/test_utils.py -v
```

### Run Evaluation
```powershell
python tests/evaluate.py
```

This will:
- Test retrieval quality on 20 predefined questions
- Generate metrics (Precision@5, keyword coverage)
- Save results to `eval_results.json`

---

## Project Structure

```
RAG-Based-AI/
├── config.py                 # Configuration management
├── utils.py                  # Shared utilities (embedding, inference, etc.)
├── chunking.py               # Sliding window chunking
├── search.py                 # Hybrid search engine
├── prompts.py                # Prompt templates
├── pipeline.py               # Unified pipeline runner
│
├── video_to_mp3_new.py       # Stage 1: Video → MP3
├── mp3_to_json_new.py        # Stage 2: Transcription
├── preprocess_json_new.py    # Stage 3: Embeddings
├── process_incoming_new.py   # Stage 4: Query processing
├── app.py                    # Streamlit web UI
│
├── tests/
│   ├── test_utils.py         # Unit tests
│   ├── eval_dataset.json     # Evaluation dataset
│   └── evaluate.py           # Evaluation script
│
├── requirements.txt          # Python dependencies
├── .env.example              # Environment template
└── .gitignore                # Git ignore rules
```

---

## New Features Implemented

✅ **Centralized Configuration** - All settings via environment variables  
✅ **Error Handling & Retries** - Robust API calls with exponential backoff  
✅ **Sliding Window Chunking** - Better context with overlapping chunks  
✅ **ChromaDB Integration** - Scalable vector database  
✅ **Hybrid Search** - Semantic (BGE-M3) + Keyword (BM25) with RRF fusion  
✅ **Cross-Encoder Reranking** - Improved result relevance  
✅ **Few-Shot Prompting** - Better LLM responses with examples  
✅ **Text Cleaning** - Remove filler words, normalize whitespace  
✅ **Deduplication** - Remove near-duplicate chunks  
✅ **Human-Readable Timestamps** - MM:SS format instead of seconds  
✅ **Streamlit Web UI** - User-friendly chat interface  
✅ **Conversation Memory** - Multi-turn conversations with context  
✅ **Unit Tests** - Automated testing for core functions  
✅ **Evaluation Framework** - Measure retrieval quality  
✅ **Logging** - Comprehensive logging to file and console  
✅ **Incremental Processing** - Skip already processed files  

---

## Troubleshooting

### Ollama not reachable
```powershell
# Start Ollama service
ollama serve
```

### FFmpeg not found
```powershell
# Check if FFmpeg is in PATH
ffmpeg -version

# If not, download from ffmpeg.org and add to PATH
```

### ChromaDB not installed
```powershell
pip install chromadb
```

### Missing dependencies
```powershell
pip install -r requirements.txt --upgrade
```

---

## Performance Tuning

### Speed up transcription (use smaller Whisper model)
Edit `.env`:
```
WHISPER_MODEL=base
```

### Use fewer results for faster queries
Edit `.env`:
```
TOP_K_RESULTS=3
RERANK_TOP_N=10
```

### Disable reranking for speed
```powershell
python process_incoming_new.py --no-reranker
```

---

## Migration from Old Version

The new files are named with `_new` suffix to preserve the originals:
- `video_to_mp3_new.py` (replaces `video_to_mp3.py`)
- `mp3_to_json_new.py` (replaces `mp3_to_json.py`)
- `preprocess_json_new.py` (replaces `preprocess_json.py`)
- `process_incoming_new.py` (replaces `process_incoming.py`)

To migrate:
1. Backup your existing `embeddings.joblib`
2. Use the new scripts (they'll create `chroma_db/` and `bm25_index.joblib`)
3. Test thoroughly
4. Once satisfied, you can remove the old scripts

---

## License

MIT License - see Readme.md for details
