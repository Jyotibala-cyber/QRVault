import io
import os
import sys
import tempfile
from datetime import datetime, timezone, timedelta
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


def create_share(client):
    file_data = os.urandom(1024)
    data = {
        "encrypted_file": (io.BytesIO(file_data), "test.enc"),
        "expiry": "5",
        "max_downloads": "3",
    }
    response = client.post(
        "/api/upload",
        data=data,
        content_type="multipart/form-data",
    )
    return response.get_json()


class TestExpiry:
    def test_share_not_expired_initially(self, client):
        result = create_share(client)
        token = result["share_token"]
        response = client.get(f"/api/share/{token}/status")
        data = response.get_json()
        assert data["status"] == "active"
        assert data["remaining_seconds"] > 0

    def test_expired_share_detected(self, client):
        result = create_share(client)
        token = result["share_token"]

        db = get_db()
        now = datetime.now(timezone.utc) - timedelta(minutes=10)
        db.execute(
            "UPDATE shares SET expires_at = ? WHERE token_hash = ?",
            (now.isoformat(), result["share_token"]),
        )
        db.commit()
        db.close()

        import hashlib
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        db = get_db()
        db.execute(
            "UPDATE shares SET expires_at = ? WHERE token_hash = ?",
            (now.isoformat(), token_hash),
        )
        db.commit()
        db.close()

        response = client.get(f"/share/{token}")
        assert response.status_code == 410

    def test_expired_share_authorize_fails(self, client):
        result = create_share(client)
        token = result["share_token"]

        import hashlib
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        now = datetime.now(timezone.utc) - timedelta(minutes=10)
        db = get_db()
        db.execute(
            "UPDATE shares SET expires_at = ? WHERE token_hash = ?",
            (now.isoformat(), token_hash),
        )
        db.commit()
        db.close()

        response = client.post(
            f"/api/share/{token}/authorize",
            json={},
            content_type="application/json",
        )
        assert response.status_code == 410
