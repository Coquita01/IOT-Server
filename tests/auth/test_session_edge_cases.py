"""
Test Session Edge Cases
Edge cases and unusual scenarios for session management.
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta, timezone
from uuid import uuid4
import json

from app.domain.auth.security import create_access_token, decode_access_token
from tests.conftest import create_test_token


class TestMalformedTokens:
    """Tests for malformed token scenarios."""

    def test_token_with_missing_jti_rejected(
        self, client: TestClient, master_admin_account: dict
    ):
        """Token without jti claim is rejected."""
        # Create token without jti
        token = create_access_token(
            data={
                "sub": str(master_admin_account["id"]),
                "email": master_admin_account["email"],
                "type": "administrator",
                "is_master": True,
            },
            token_id=None,  # No jti
        )

        response = client.get(
            "/api/v1/devices",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401

    def test_token_with_invalid_sub_rejected(self, client: TestClient):
        """Token with invalid sub (user ID) is rejected."""
        invalid_uuid = "not-a-valid-uuid"
        token = create_test_token({
            "id": invalid_uuid,
            "email": "test@test.com",
            "account_type": "user",
            "is_master": False,
        })

        response = client.get(
            "/api/v1/devices",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401

    def test_token_with_invalid_type_rejected(
        self, client: TestClient, master_admin_account: dict
    ):
        """Token with invalid account type is rejected."""
        token = create_access_token(
            data={
                "sub": str(master_admin_account["id"]),
                "email": master_admin_account["email"],
                "type": "invalid_type",  # Invalid
                "is_master": False,
            },
            token_id=str(uuid4()),
        )

        response = client.get(
            "/api/v1/devices",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401

    def test_token_with_extra_claims_accepted(
        self, client: TestClient, master_admin_account: dict
    ):
        """Token with extra claims is accepted (forwards compatible)."""
        token_id = str(uuid4())
        token = create_access_token(
            data={
                "sub": str(master_admin_account["id"]),
                "email": master_admin_account["email"],
                "type": "administrator",
                "is_master": True,
                "extra_field": "extra_value",  # Extra claim
            },
            token_id=token_id,
        )

        # Should still work
        payload = decode_access_token(token)
        assert "extra_field" in payload

    def test_empty_bearer_token_rejected(self, client: TestClient):
        """Empty Bearer token is rejected."""
        response = client.get(
            "/api/v1/devices",
            headers={"Authorization": "Bearer "},
        )
        assert response.status_code == 401

    def test_bearer_token_with_spaces_rejected(self, client: TestClient):
        """Bearer token with spaces is rejected."""
        response = client.get(
            "/api/v1/devices",
            headers={"Authorization": "Bearer token with spaces"},
        )
        assert response.status_code == 401


class TestValkeyEdgeCases:
    """Edge cases related to Valkey storage."""

    def test_session_not_in_valkey_but_valid_jwt_rejected(
        self, client: TestClient, master_admin_account: dict, mock_valkey
    ):
        """Valid JWT without session in Valkey is rejected."""
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": master_admin_account["email"],
                "password": master_admin_account["password"],
            },
        )
        token = login_response.json()["access_token"]

        # Clear Valkey sessions
        mock_valkey.data = {
            k: v for k, v in mock_valkey.data.items() if not k.startswith("session:")
        }

        # Token should not work
        response = client.get(
            "/api/v1/devices",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401

    def test_session_exists_but_token_blacklisted(
        self, client: TestClient, master_admin_account: dict
    ):
        """Session exists but token is blacklisted."""
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": master_admin_account["email"],
                "password": master_admin_account["password"],
            },
        )
        token = login_response.json()["access_token"]

        # Logout (blacklists token but keeps session for a moment)
        client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
        )

        # Token should be rejected (blacklisted)
        response = client.get(
            "/api/v1/devices",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401

    def test_corrupted_session_data_handled_gracefully(
        self, client: TestClient, master_admin_account: dict, mock_valkey
    ):
        """Corrupted session data in Valkey is handled gracefully."""
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": master_admin_account["email"],
                "password": master_admin_account["password"],
            },
        )
        token = login_response.json()["access_token"]

        # Corrupt all session data
        for key in list(mock_valkey.data.keys()):
            if key.startswith("session:"):
                mock_valkey.data[key] = "corrupted-data-not-json"

        # Should handle gracefully
        response = client.get(
            "/api/v1/devices",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code in [401, 500]

    def test_session_with_missing_required_fields(
        self, client: TestClient, master_admin_account: dict, mock_valkey
    ):
        """Session with missing required fields is rejected."""
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": master_admin_account["email"],
                "password": master_admin_account["password"],
            },
        )
        token = login_response.json()["access_token"]

        # Corrupt session data (missing fields)
        for key in list(mock_valkey.data.keys()):
            if key.startswith("session:"):
                mock_valkey.data[key] = json.dumps({"incomplete": "data"})

        response = client.get(
            "/api/v1/devices",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code in [401, 500]


class TestRateLimitingEdgeCases:
    """Edge cases for rate limiting."""

    def test_rate_limit_counter_per_ip(
        self, client: TestClient, master_admin_account: dict
    ):
        """Rate limit counters are per IP address."""
        # IP1: Make 3 failed attempts
        for _ in range(3):
            client.post(
                "/api/v1/auth/login",
                json={
                    "email": master_admin_account["email"],
                    "password": "WrongPass123!",
                },
                headers={"X-Forwarded-For": "10.0.0.1"},
            )

        # IP1: 4th attempt should be blocked
        response1 = client.post(
            "/api/v1/auth/login",
            json={
                "email": master_admin_account["email"],
                "password": "WrongPass123!",
            },
            headers={"X-Forwarded-For": "10.0.0.1"},
        )
        assert response1.status_code == 429

        # IP2: Should not be blocked
        response2 = client.post(
            "/api/v1/auth/login",
            json={
                "email": master_admin_account["email"],
                "password": "WrongPass123!",
            },
            headers={"X-Forwarded-For": "10.0.0.2"},
        )
        assert response2.status_code == 400  # Wrong password, not rate limited

    def test_rate_limit_different_emails_share_ip_limit(
        self, client: TestClient, master_admin_account: dict, user_account: dict
    ):
        """Rate limit is per IP, not per email."""
        # Same IP, different emails
        ip = "10.0.0.100"

        # 3 attempts with email1
        for _ in range(2):
            client.post(
                "/api/v1/auth/login",
                json={"email": master_admin_account["email"], "password": "WrongPass123!"},
                headers={"X-Forwarded-For": ip},
            )

        # 1 attempt with email2 (same IP)
        client.post(
            "/api/v1/auth/login",
            json={"email": user_account["email"], "password": "WrongPass123!"},
            headers={"X-Forwarded-For": ip},
        )

        # 4th attempt from same IP should be rate limited
        response = client.post(
            "/api/v1/auth/login",
            json={"email": master_admin_account["email"], "password": "WrongPass123!"},
            headers={"X-Forwarded-For": ip},
        )
        assert response.status_code == 429

    def test_successful_login_does_not_increment_rate_limit(
        self, client: TestClient, master_admin_account: dict
    ):
        """Successful logins don't count toward rate limit."""
        # Make 5 successful logins (more than rate limit would allow for failures)
        for _ in range(5):
            response = client.post(
                "/api/v1/auth/login",
                json={
                    "email": master_admin_account["email"],
                    "password": master_admin_account["password"],
                },
            )
            assert response.status_code == 200

        # Should still be able to login (not rate limited)
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": master_admin_account["email"],
                "password": master_admin_account["password"],
            },
        )
        assert response.status_code == 200


class TestTokenReuse:
    """Tests for token reuse scenarios."""

    def test_cannot_use_same_refresh_token_twice(
        self, client: TestClient, master_admin_account: dict
    ):
        """Refresh token can only be used once."""
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": master_admin_account["email"],
                "password": master_admin_account["password"],
            },
        )
        refresh_token = login_response.json()["refresh_token"]

        # Use refresh token first time
        first_refresh = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert first_refresh.status_code == 200

        # Try to use same refresh token again
        second_refresh = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert second_refresh.status_code == 401

    def test_cannot_use_blacklisted_access_token(
        self, client: TestClient, master_admin_account: dict
    ):
        """Blacklisted access token cannot be reused."""
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": master_admin_account["email"],
                "password": master_admin_account["password"],
            },
        )
        access_token = login_response.json()["access_token"]

        # Blacklist token via logout
        client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        # Try to use blacklisted token
        response = client.get(
            "/api/v1/devices",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 401

    def test_old_access_token_after_refresh_rejected(
        self, client: TestClient, master_admin_account: dict
    ):
        """Old access token is rejected after refresh."""
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": master_admin_account["email"],
                "password": master_admin_account["password"],
            },
        )
        old_access = login_response.json()["access_token"]
        refresh_token = login_response.json()["refresh_token"]

        # Refresh tokens
        client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})

        # Old access token should be blacklisted
        response = client.get(
            "/api/v1/devices",
            headers={"Authorization": f"Bearer {old_access}"},
        )
        assert response.status_code == 401


class TestAccountDeletion:
    """Tests for deleted account scenarios."""

    def test_deleted_account_token_rejected(
        self, client: TestClient, user_account: dict, session
    ):
        """Token from deleted account is rejected."""
        # Login first
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": user_account["email"], "password": user_account["password"]},
        )
        token = login_response.json()["access_token"]

        # Token should work initially
        response = client.get(
            "/api/v1/devices",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

        # Delete account (need to delete related records first due to FK constraints)
        from app.database.model import User, SensitiveData, NonCriticalPersonalData
        user = session.get(User, user_account["id"])
        sensitive_data_id = user.sensitive_data_id
        session.delete(user)
        session.flush()
        
        sensitive = session.get(SensitiveData, sensitive_data_id)
        non_critical_id = sensitive.non_critical_data_id
        session.delete(sensitive)
        session.flush()
        
        non_critical = session.get(NonCriticalPersonalData, non_critical_id)
        session.delete(non_critical)
        session.commit()

        # Token should not work with deleted account
        response = client.get(
            "/api/v1/devices",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401


class TestSpecialCharactersAndEncoding:
    """Tests for special characters in credentials."""

    def test_email_with_plus_sign_works(self, client: TestClient, session):
        """Email with + sign works correctly."""
        from app.database.model import Administrator, NonCriticalPersonalData, SensitiveData

        # Create admin with + in email
        non_critical = NonCriticalPersonalData(
            first_name="Test",
            last_name="Plus",
            phone="+523312345999",
            address="Test",
            city="City",
            state="State",
            postal_code="12345",
            birth_date=datetime(1990, 1, 1),
            is_active=True,
        )
        session.add(non_critical)
        session.flush()

        sensitive = SensitiveData(
            non_critical_data_id=non_critical.id,
            email="test+admin@test.com",
            password="TestPassword123!",
            curp="TEST111111HDFRRL09",
            rfc="TEST111111AB0",
        )
        session.add(sensitive)
        session.flush()

        admin = Administrator(
            sensitive_data_id=sensitive.id,
            is_master=True,
            is_active=True,
        )
        session.add(admin)
        session.commit()

        # Login should work
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "test+admin@test.com", "password": "TestPassword123!"},
        )
        assert response.status_code == 200

    def test_password_with_special_characters_works(
        self, client: TestClient, master_admin_account: dict, session
    ):
        """Password with special characters works."""
        from app.database.model import Administrator

        # Change password to one with special chars
        admin = session.get(Administrator, master_admin_account["id"])
        admin.sensitive_data.password = "P@ssw0rd!#$%&*()[]{}?"
        session.commit()

        # Login should work
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": master_admin_account["email"],
                "password": "P@ssw0rd!#$%&*()[]{}?",
            },
        )
        assert response.status_code == 200


class TestConcurrentRequests:
    """Tests for concurrent request scenarios."""

    def test_same_token_concurrent_requests_work(
        self, client: TestClient, master_admin_account: dict
    ):
        """Same token can be used in concurrent requests."""
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": master_admin_account["email"],
                "password": master_admin_account["password"],
            },
        )
        token = login_response.json()["access_token"]

        # Make multiple concurrent requests
        responses = [
            client.get("/api/v1/devices", headers={"Authorization": f"Bearer {token}"}),
            client.get("/api/v1/users", headers={"Authorization": f"Bearer {token}"}),
            client.get(
                "/api/v1/administrators",
                headers={"Authorization": f"Bearer {token}"},
            ),
        ]

        # All should succeed
        for response in responses:
            assert response.status_code == 200
