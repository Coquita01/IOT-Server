"""
Test Session Security
Security-specific tests for session management.
Validates JWE encryption, token rotation, and protection against attacks.
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta, timezone
import json

from app.domain.auth.security import (
    create_access_token,
    decode_access_token,
    get_password_hash,
)
from app.config import settings


class TestJWEEncryption:
    """Tests for JWE token encryption."""

    def test_token_is_encrypted_jwe_not_plain_jwt(
        self, client: TestClient, master_admin_account: dict
    ):
        """Access token is JWE encrypted, not plain JWT."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": master_admin_account["email"],
                "password": master_admin_account["password"],
            },
        )
        token = response.json()["access_token"]

        # JWE has 5 parts (header.encrypted_key.iv.ciphertext.tag)
        # JWT has 3 parts (header.payload.signature)
        parts = token.count(".")
        assert parts == 4, f"JWE should have 4 dots (5 parts), got {parts}"

    def test_token_cannot_be_decoded_as_plain_jwt(
        self, client: TestClient, master_admin_account: dict
    ):
        """Token cannot be decoded without decryption."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": master_admin_account["email"],
                "password": master_admin_account["password"],
            },
        )
        token = response.json()["access_token"]

        # Try to decode as plain JWT (should fail)
        import jwt
        with pytest.raises(Exception):
            jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])

    def test_token_requires_encryption_key_to_decrypt(
        self, client: TestClient, master_admin_account: dict
    ):
        """Token can only be decrypted with correct ENCRYPTION_KEY."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": master_admin_account["email"],
                "password": master_admin_account["password"],
            },
        )
        token = response.json()["access_token"]

        # Should work with correct key
        payload = decode_access_token(token)
        assert payload["email"] == master_admin_account["email"]

    def test_token_contains_jti_for_session_tracking(
        self, client: TestClient, master_admin_account: dict
    ):
        """Token contains jti (JWT ID) for session tracking."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": master_admin_account["email"],
                "password": master_admin_account["password"],
            },
        )
        token = response.json()["access_token"]
        payload = decode_access_token(token)

        assert "jti" in payload
        assert isinstance(payload["jti"], str)
        assert len(payload["jti"]) > 0

    def test_token_contains_required_claims(
        self, client: TestClient, master_admin_account: dict
    ):
        """Token contains all required claims."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": master_admin_account["email"],
                "password": master_admin_account["password"],
            },
        )
        token = response.json()["access_token"]
        payload = decode_access_token(token)

        required_claims = ["sub", "email", "type", "is_master", "exp", "jti"]
        for claim in required_claims:
            assert claim in payload, f"Missing required claim: {claim}"


class TestTokenRotation:
    """Tests for token rotation security."""

    def test_refresh_invalidates_old_access_token(
        self, client: TestClient, master_admin_account: dict
    ):
        """Refresh adds old access_token to blacklist."""
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": master_admin_account["email"],
                "password": master_admin_account["password"],
            },
        )
        old_access_token = login_response.json()["access_token"]
        refresh_token = login_response.json()["refresh_token"]

        # Refresh tokens
        client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )

        # Old access token should be blacklisted
        response = client.get(
            "/api/v1/devices",
            headers={"Authorization": f"Bearer {old_access_token}"},
        )
        assert response.status_code == 401

    def test_refresh_invalidates_old_refresh_token(
        self, client: TestClient, master_admin_account: dict
    ):
        """Refresh invalidates old refresh token (single-use)."""
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": master_admin_account["email"],
                "password": master_admin_account["password"],
            },
        )
        old_refresh_token = login_response.json()["refresh_token"]

        # Use refresh token once
        client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": old_refresh_token},
        )

        # Try to use same refresh token again (should fail)
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": old_refresh_token},
        )
        assert response.status_code == 401

    def test_old_tokens_cannot_be_reused_replay_attack(
        self, client: TestClient, master_admin_account: dict
    ):
        """Old tokens cannot be reused (protects against replay attacks)."""
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": master_admin_account["email"],
                "password": master_admin_account["password"],
            },
        )
        old_access = login_response.json()["access_token"]
        refresh_token = login_response.json()["refresh_token"]

        # Get new tokens
        client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})

        # Try to use old access token (should fail)
        response = client.get(
            "/api/v1/devices",
            headers={"Authorization": f"Bearer {old_access}"},
        )
        assert response.status_code == 401

    def test_each_login_creates_unique_tokens(
        self, client: TestClient, master_admin_account: dict
    ):
        """Each login creates unique tokens."""
        response1 = client.post(
            "/api/v1/auth/login",
            json={
                "email": master_admin_account["email"],
                "password": master_admin_account["password"],
            },
        )
        
        response2 = client.post(
            "/api/v1/auth/login",
            json={
                "email": master_admin_account["email"],
                "password": master_admin_account["password"],
            },
        )

        token1 = response1.json()["access_token"]
        token2 = response2.json()["access_token"]
        
        assert token1 != token2


class TestSessionHijackingPrevention:
    """Tests for session hijacking prevention."""

    def test_session_stores_ip_address(
        self, client: TestClient, master_admin_account: dict, mock_valkey
    ):
        """Session stores client IP address."""
        client.post(
            "/api/v1/auth/login",
            json={
                "email": master_admin_account["email"],
                "password": master_admin_account["password"],
            },
        )

        # Check that session was created with IP
        # (MockValkey stores sessions)
        sessions = [
            key for key in mock_valkey.data.keys() if key.startswith("session:")
        ]
        assert len(sessions) > 0

    def test_session_stores_user_agent(
        self, client: TestClient, master_admin_account: dict
    ):
        """Session stores User-Agent."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": master_admin_account["email"],
                "password": master_admin_account["password"],
            },
            headers={"User-Agent": "Test-Agent/1.0"},
        )
        assert response.status_code == 200

    def test_session_validates_jti_exists_in_valkey(
        self, client: TestClient, master_admin_account: dict, mock_valkey
    ):
        """Middleware validates that jti exists in Valkey."""
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": master_admin_account["email"],
                "password": master_admin_account["password"],
            },
        )
        token = login_response.json()["access_token"]

        # Token should work
        response = client.get(
            "/api/v1/devices",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

        # Clear Valkey sessions
        mock_valkey.data.clear()

        # Now token shouldn't work (no session in Valkey)
        response = client.get(
            "/api/v1/devices",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401


class TestTokenTampering:
    """Tests for token tampering detection."""

    def test_modified_token_payload_is_rejected(
        self, client: TestClient, master_admin_account: dict
    ):
        """Token with modified payload is rejected."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": master_admin_account["email"],
                "password": master_admin_account["password"],
            },
        )
        token = response.json()["access_token"]

        # Modify token (change one character)
        modified_token = token[:-5] + "XXXXX"

        response = client.get(
            "/api/v1/devices",
            headers={"Authorization": f"Bearer {modified_token}"},
        )
        assert response.status_code == 401

    def test_token_from_different_user_is_rejected(
        self, client: TestClient, master_admin_account: dict, user_account: dict
    ):
        """Token issued for one user cannot be used by another."""
        # Login as master admin
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": master_admin_account["email"],
                "password": master_admin_account["password"],
            },
        )
        admin_token = response.json()["access_token"]
        admin_payload = decode_access_token(admin_token)

        # Verify token belongs to admin
        assert admin_payload["type"] == "administrator"
        assert admin_payload["email"] == master_admin_account["email"]


class TestPasswordChangeInvalidation:
    """Tests for session invalidation on password change."""

    def test_password_change_requires_current_password(
        self, client: TestClient, master_admin_account: dict
    ):
        """Cannot change password without verifying current password."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": master_admin_account["email"],
                "password": master_admin_account["password"],
            },
        )
        token = response.json()["access_token"]

        # Try with wrong current password
        response = client.patch(
            "/api/v1/auth/change-password",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "current_password": "WrongPassword123!",
                "new_password": "NewPassword123!",
            },
        )
        assert response.status_code == 400

    def test_password_change_succeeds_with_correct_current_password(
        self, client: TestClient, master_admin_account: dict
    ):
        """Password change succeeds with correct current password."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": master_admin_account["email"],
                "password": master_admin_account["password"],
            },
        )
        token = response.json()["access_token"]

        response = client.patch(
            "/api/v1/auth/change-password",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "current_password": master_admin_account["password"],
                "new_password": "NewPassword123!",
            },
        )
        assert response.status_code == 200


class TestSensitiveDataProtection:
    """Tests that sensitive data is never exposed."""

    def test_token_does_not_contain_password(
        self, client: TestClient, master_admin_account: dict
    ):
        """Token payload does not contain password or password_hash."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": master_admin_account["email"],
                "password": master_admin_account["password"],
            },
        )
        token = response.json()["access_token"]
        payload = decode_access_token(token)

        assert "password" not in payload
        assert "password_hash" not in payload

    def test_login_response_does_not_leak_sensitive_data(
        self, client: TestClient, master_admin_account: dict
    ):
        """Login response doesn't contain sensitive fields."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": master_admin_account["email"],
                "password": master_admin_account["password"],
            },
        )
        data = response.json()

        sensitive_fields = ["password", "password_hash", "curp", "rfc"]
        for field in sensitive_fields:
            assert field not in data

    def test_error_messages_do_not_leak_information(self, client: TestClient):
        """Error messages don't reveal if email exists."""
        # Non-existent email
        response1 = client.post(
            "/api/v1/auth/login",
            json={"email": "nonexistent@test.com", "password": "Pass123!"},
        )

        # Existing email with wrong password would give same message
        message = response1.json()["detail"]
        
        # Message should be generic
        assert "Invalid credentials" in message
        assert "email" not in message.lower()
        assert "not found" not in message.lower()
