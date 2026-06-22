import os
import sys
import pytest
from fastapi.testclient import TestClient
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from main import app

client = TestClient(app)

def test_startup_and_dashboard():
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert b"MindMesh AI" in response.content

def test_upload_page():
    response = client.get("/upload")
    assert response.status_code == 200
    assert b"Upload" in response.content

def test_chat_page():
    response = client.get("/chat")
    assert response.status_code == 200
    assert b"Chat" in response.content

def test_settings_page():
    response = client.get("/settings")
    assert response.status_code == 200
    assert b"Settings" in response.content

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
