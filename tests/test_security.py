import os
import sys
import tempfile
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from security.tokens import generate_share_token, hash_token, generate_management_token
from security.validation import (
    sanitize_filename,
    validate_file_extension,
    validate_file_size,
    safe_path,
)


class TestTokenSecurity:
    def test_generate_share_token_is_unique(self):
        tokens = {generate_share_token() for _ in range(100)}
        assert len(tokens) == 100

    def test_generate_management_token_is_unique(self):
        tokens = {generate_management_token() for _ in range(100)}
        assert len(tokens) == 100

    def test_token_hash_deterministic(self):
        token = generate_share_token()
        h1 = hash_token(token)
        h2 = hash_token(token)
        assert h1 == h2

    def test_different_tokens_different_hashes(self):
        t1 = generate_share_token()
        t2 = generate_share_token()
        assert hash_token(t1) != hash_token(t2)

    def test_token_length(self):
        token = generate_share_token()
        assert len(token) >= 32


class TestFilenameSanitization:
    def test_normal_filename(self):
        assert sanitize_filename("document.pdf") == "document.pdf"

    def test_path_traversal(self):
        result = sanitize_filename("../../etc/passwd")
        assert ".." not in result
        assert "/" not in result

    def test_empty_filename(self):
        assert sanitize_filename("") == "unnamed_file"
        assert sanitize_filename(None) == "unnamed_file"

    def test_special_characters(self):
        result = sanitize_filename("file<script>alert(1)</script>.pdf")
        assert "<" not in result
        assert ">" not in result

    def test_long_filename(self):
        long_name = "a" * 300 + ".pdf"
        result = sanitize_filename(long_name)
        assert len(result) <= 255

    def test_dots_only(self):
        result = sanitize_filename("...")
        assert result != ""
        assert result is not None


class TestFileValidation:
    def test_valid_extension(self):
        valid, _ = validate_file_extension("document.pdf")
        assert valid is True

    def test_blocked_exe(self):
        valid, error = validate_file_extension("malware.exe")
        assert valid is False
        assert "not allowed" in error

    def test_blocked_bat(self):
        valid, error = validate_file_extension("script.bat")
        assert valid is False

    def test_file_size_within_limit(self):
        valid, _ = validate_file_size(1024, 1024 * 1024)
        assert valid is True

    def test_file_size_exceeds_limit(self):
        valid, error = validate_file_size(2 * 1024 * 1024, 1024 * 1024)
        assert valid is False
        assert "exceeds" in error

    def test_empty_file(self):
        valid, error = validate_file_size(0, 1024)
        assert valid is False
        assert "empty" in error


class TestSafePath:
    def test_safe_path_within_base(self):
        base = tempfile.mkdtemp()
        result = safe_path(base, "test.enc")
        assert result is not None

    def test_unsafe_path_traversal(self):
        base = tempfile.mkdtemp()
        result = safe_path(base, "../../etc/passwd")
        assert result is None


class TestSecurityHeaders:
    def test_security_headers_present(self, client):
        response = client.get("/")
        assert response.headers.get("X-Content-Type-Options") == "nosniff"
        assert response.headers.get("X-Frame-Options") == "DENY"
        assert response.headers.get("X-XSS-Protection") == "1; mode=block"
        assert "Content-Security-Policy" in response.headers
        assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
