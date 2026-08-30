import io
import json
import os
import sys
import tempfile
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from database.db import init_db


@pytest.fixture
def client():
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    app = create_app("development")
    app.config["TESTING"] = True
    app.config["DATABASE_PATH"] = db_path
    app.config["STORAGE_PATH"] = tempfile.mkdtemp()

    with app.test_client() as client:
        with app.app_context():
            init_db()
        yield client

    os.close(db_fd)
    os.unlink(db_path)


class TestUpload:
    def test_upload_no_file(self, client):
        response = client.post("/api/upload")
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data

    def test_upload_empty_filename(self, client):
        data = {"encrypted_file": (io.BytesIO(b"test"), "")}
        response = client.post(
            "/api/upload",
            data=data,
            content_type="multipart/form-data",
        )
        assert response.status_code == 400

    def test_upload_valid_file(self, client):
        file_data = os.urandom(1024)
        data = {
            "encrypted_file": (io.BytesIO(file_data), "test.enc"),
            "expiry": "10",
            "max_downloads": "3",
        }
        response = client.post(
            "/api/upload",
            data=data,
            content_type="multipart/form-data",
        )
        assert response.status_code == 200
        result = response.get_json()
        assert result["success"] is True
        assert "share_token" in result
        assert "management_token" in result
        assert "qr_code" in result
        assert result["qr_code"].startswith("data:image/png;base64,")

    def test_upload_returns_share_url(self, client):
        file_data = os.urandom(512)
        data = {
            "encrypted_file": (io.BytesIO(file_data), "document.pdf.enc"),
            "expiry": "5",
            "max_downloads": "1",
        }
        response = client.post(
            "/api/upload",
            data=data,
            content_type="multipart/form-data",
        )
        result = response.get_json()
        assert "share_url" in result
        assert "/share/" in result["share_url"]

    def test_upload_blocked_extension(self, client):
        file_data = os.urandom(100)
        data = {
            "encrypted_file": (io.BytesIO(file_data), "malware.exe"),
            "expiry": "10",
            "max_downloads": "3",
        }
        response = client.post(
            "/api/upload",
            data=data,
            content_type="multipart/form-data",
        )
        assert response.status_code == 400

    def test_upload_invalid_expiry(self, client):
        file_data = os.urandom(100)
        data = {
            "encrypted_file": (io.BytesIO(file_data), "test.enc"),
            "expiry": "999",
            "max_downloads": "3",
        }
        response = client.post(
            "/api/upload",
            data=data,
            content_type="multipart/form-data",
        )
        assert response.status_code == 400

    def test_upload_invalid_downloads(self, client):
        file_data = os.urandom(100)
        data = {
            "encrypted_file": (io.BytesIO(file_data), "test.enc"),
            "expiry": "10",
            "max_downloads": "7",
        }
        response = client.post(
            "/api/upload",
            data=data,
            content_type="multipart/form-data",
        )
        assert response.status_code == 400
