@echo off
echo ========================================
echo Aurora RAG Assistant - Backend Startup
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo.

REM Install dependencies
echo Installing dependencies...
pip install -r project\backend\requirements.txt
echo.

REM Check if Ollama is running
echo Checking Ollama server...
curl -s http://localhost:11434 >nul 2>&1
if errorlevel 1 (
    echo WARNING: Ollama server not detected!
    echo Please start Ollama with: ollama serve
    echo Then run the models:
    echo   ollama pull llama3.2
    echo   ollama pull bge-m3
    echo.
    pause
)

REM Start the backend server
echo Starting FastAPI backend on http://localhost:8000...
echo.
echo You can now open the frontend in a browser:
echo   file:///C:/Users/%USERNAME%/Downloads/RAG-Based-AI/project/frontend/index.html
echo.
echo Press Ctrl+C to stop the server.
echo.

cd c:\Users\Piyu\Downloads\RAG-Based-AI
python -m uvicorn project.backend.main:app --reload --port 8000 --host 0.0.0.0

pause
