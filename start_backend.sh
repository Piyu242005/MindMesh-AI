#!/bin/bash

echo "========================================"
echo "Aurora RAG Assistant - Backend Startup"
echo "========================================"
echo

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo

# Install dependencies
echo "Installing dependencies..."
pip install -r project/backend/requirements.txt
echo

# Check if Ollama is running
echo "Checking Ollama server..."
if ! curl -s http://localhost:11434 > /dev/null 2>&1; then
    echo "WARNING: Ollama server not detected!"
    echo "Please start Ollama with: ollama serve"
    echo "Then run the models:"
    echo "  ollama pull llama3.2"
    echo "  ollama pull bge-m3"
    echo
    read -p "Press Enter to continue..."
fi

# Start the backend server
echo "Starting FastAPI backend on http://localhost:8000..."
echo
echo "You can now open the frontend in a browser:"
echo "  file://$(pwd)/project/frontend/index.html"
echo
echo "Press Ctrl+C to stop the server."
echo

cd "$(dirname "$0")"
python3 -m uvicorn project.backend.main:app --reload --port 8000 --host 0.0.0.0
