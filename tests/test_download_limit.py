import io
import os
import sys
import tempfile
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from database.db import init_db, get_db


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


def create_share_with_limit(client, limit=1):
    file_data = os.urandom(1024)
    data = {
        "encrypted_file": (io.BytesIO(file_data), "test.enc"),
        "expiry": "60",
        "max_downloads": str(limit),
    }
    response = client.post(
        "/api/upload",
        data=data,
        content_type="multipart/form-data",
    )
    return response.get_json()


class TestDownloadLimit:
    def test_download_within_limit(self, client):
        result = create_share_with_limit(client, limit=3)
        token = result["share_token"]

        for i in range(3):
            auth = client.post(
                f"/api/share/{token}/authorize",
                json={},
                content_type="application/json",
            )
            assert auth.status_code == 200

            dl = client.get(f"/api/share/{token}/download")
            assert dl.status_code == 200

    def test_download_exceeds_limit(self, client):
        result = create_share_with_limit(client, limit=1)
        token = result["share_token"]

        auth1 = client.post(
            f"/api/share/{token}/authorize",
            json={},
            content_type="application/json",
        )
        assert auth1.status_code == 200

        dl1 = client.get(f"/api/share/{token}/download")
        assert dl1.status_code == 200

        auth2 = client.post(
            f"/api/share/{token}/authorize",
            json={},
            content_type="application/json",
        )
        assert auth2.status_code == 403

    def test_status_reflects_downloads(self, client):
        result = create_share_with_limit(client, limit=3)
        token = result["share_token"]

        status = client.get(f"/api/share/{token}/status").get_json()
        assert status["download_count"] == 0

        client.post(f"/api/share/{token}/authorize", json={})
        client.get(f"/api/share/{token}/download")

        status = client.get(f"/api/share/{token}/status").get_json()
        assert status["download_count"] == 1

    def test_limit_reached_status(self, client):
        result = create_share_with_limit(client, limit=1)
        token = result["share_token"]

        client.post(f"/api/share/{token}/authorize", json={})
        client.get(f"/api/share/{token}/download")

        status = client.get(f"/api/share/{token}/status").get_json()
        assert status["status"] == "limit_reached"
