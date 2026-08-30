import io
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


def create_share(client):
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
    return response.get_json()


class TestAccessControl:
    def test_valid_token_access(self, client):
        result = create_share(client)
        token = result["share_token"]
        response = client.get(f"/share/{token}")
        assert response.status_code == 200

    def test_invalid_token_access(self, client):
        response = client.get("/share/invalid_token_12345")
        assert response.status_code == 404

    def test_status_valid_token(self, client):
        result = create_share(client)
        token = result["share_token"]
        response = client.get(f"/api/share/{token}/status")
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "active"
        assert data["download_count"] == 0
        assert data["max_downloads"] == 3

    def test_status_invalid_token(self, client):
        response = client.get("/api/share/nonexistent/status")
        assert response.status_code == 404

    def test_authorize_valid_token(self, client):
        result = create_share(client)
        token = result["share_token"]
        response = client.post(
            f"/api/share/{token}/authorize",
            json={},
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["authorized"] is True

    def test_authorize_invalid_token(self, client):
        response = client.post(
            "/api/share/bad_token/authorize",
            json={},
            content_type="application/json",
        )
        assert response.status_code == 404

    def test_management_token_required_for_revoke(self, client):
        result = create_share(client)
        token = result["share_token"]
        response = client.post(
            f"/api/share/{token}/revoke",
            json={},
            content_type="application/json",
        )
        assert response.status_code in [401, 404]

    def test_revoke_share(self, client):
        result = create_share(client)
        token = result["share_token"]
        mgmt = result["management_token"]
        response = client.post(
            f"/api/manage/{mgmt}/revoke",
            json={},
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True

        status_resp = client.get(f"/api/share/{token}/status")
        status_data = status_resp.get_json()
        assert status_data["revoked"] is True

    def test_download_revoked_share(self, client):
        result = create_share(client)
        token = result["share_token"]
        mgmt = result["management_token"]
        client.post(
            f"/api/manage/{mgmt}/revoke",
            json={},
            content_type="application/json",
        )
        response = client.post(
            f"/api/share/{token}/authorize",
            json={},
            content_type="application/json",
        )
        assert response.status_code == 403

    def test_delete_share(self, client):
        result = create_share(client)
        token = result["share_token"]
        mgmt = result["management_token"]
        response = client.delete(
            f"/api/manage/{mgmt}",
            json={},
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
