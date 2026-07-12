import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.append(str(Path(__file__).parent.parent))

from main import app
from routes import upload


client = TestClient(app)


def test_upload_rejects_unsupported_extensions():
    response = client.post(
        "/api/upload",
        data={"video_number": "1", "video_title": "Unsafe upload"},
        files={"file": ("../payload.txt", b"not a media file", "text/plain")},
    )

    assert response.status_code == 400
    assert "Unsupported file type" in response.text


def test_upload_enforces_size_while_streaming(monkeypatch):
    monkeypatch.setattr(upload, "MAX_UPLOAD_SIZE", 5)
    response = client.post(
        "/api/upload",
        data={"video_number": "1", "video_title": "Oversized upload"},
        files={"file": ("lesson.mp3", b"123456", "audio/mpeg")},
    )

    assert response.status_code == 400
    assert "File too large" in response.text


def test_telegram_webhook_rejects_invalid_secret(monkeypatch):
    monkeypatch.setenv("TELEGRAM_WEBHOOK_SECRET", "expected-secret")
    response = client.post("/api/telegram/webhook", json={"message": {}})

    assert response.status_code == 403
