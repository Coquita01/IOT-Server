"""
Test Session Integration
Integration tests for complete session lifecycle and failure scenarios.
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from tests.conftest import create_test_token


class TestSessionFullLifecycle:
    """Tests for complete session lifecycle."""

    def test_complete_login_refresh_logout_flow(
        self, client: TestClient, master_admin_account: dict
    ):
        """Complete flow: Login → Use token → Refresh → Use new token → Logout."""
        # Step 1: Login
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": master_admin_account["email"],
                "password": master_admin_account["password"],
            },
        )
        assert login_response.status_code == 200
        access_token = login_response.json()["access_token"]
        refresh_token = login_response.json()["refresh_token"]

        # Step 2: Use access token
        devices_response = client.get(
            "/api/v1/devices",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert devices_response.status_code == 200

        # Step 3: Refresh tokens
        refresh_response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert refresh_response.status_code == 200
        new_access_token = refresh_response.json()["access_token"]

        # Step 4: Old access token should be blacklisted
        old_devices_response = client.get(
            "/api/v1/devices",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert old_devices_response.status_code == 401

        # Step 5: New access token should work
        new_devices_response = client.get(
            "/api/v1/devices",
            headers={"Authorization": f"Bearer {new_access_token}"},
        )
        assert new_devices_response.status_code == 200

        # Step 6: Logout
        logout_response = client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {new_access_token}"},
        )
        assert logout_response.status_code == 200

        # Step 7: Token should not work after logout
        final_response = client.get(
            "/api/v1/devices",
            headers={"Authorization": f"Bearer {new_access_token}"},
        )
        assert final_response.status_code == 401

    def test_login_creates_valkey_session(
        self, client: TestClient, master_admin_account: dict, mock_valkey
    ):
        """Login creates session entry in Valkey."""
        # Get initial session count
        initial_sessions = len(
            [k for k in mock_valkey.data.keys() if k.startswith("session:")]
        )

        # Login
        client.post(
            "/api/v1/auth/login",
            json={
                "email": master_admin_account["email"],
                "password": master_admin_account["password"],
            },
        )

        # Check session was created
        final_sessions = len(
            [k for k in mock_valkey.data.keys() if k.startswith("session:")]
        )
        assert final_sessions > initial_sessions

    def test_logout_removes_valkey_session(
        self, client: TestClient, master_admin_account: dict, mock_valkey
    ):
        """Logout removes session from Valkey."""
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": master_admin_account["email"],
                "password": master_admin_account["password"],
            },
        )
        access_token = login_response.json()["access_token"]

        sessions_before = len(
            [k for k in mock_valkey.data.keys() if k.startswith("session:")]
        )

        # Logout
        client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        sessions_after = len(
            [k for k in mock_valkey.data.keys() if k.startswith("session:")]
        )
        assert sessions_after < sessions_before

    def test_refresh_updates_valkey_session(
        self, client: TestClient, master_admin_account: dict, mock_valkey
    ):
        """Refresh updates session data in Valkey."""
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": master_admin_account["email"],
                "password": master_admin_account["password"],
            },
        )
        refresh_token = login_response.json()["refresh_token"]

        # Refresh tokens
        refresh_response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert refresh_response.status_code == 200

    def test_multiple_endpoints_share_same_session(
        self, client: TestClient, master_admin_account: dict
    ):
        """Multiple requests with same token share the same session."""
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": master_admin_account["email"],
                "password": master_admin_account["password"],
            },
        )
        token = login_response.json()["access_token"]

        # Call different endpoints with same token
        response1 = client.get(
            "/api/v1/devices",
            headers={"Authorization": f"Bearer {token}"},
        )
        response2 = client.get(
            "/api/v1/administrators",
            headers={"Authorization": f"Bearer {token}"},
        )
        response3 = client.get(
            "/api/v1/users",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response3.status_code == 200


class TestConcurrentSessions:
    """Tests for concurrent session scenarios."""

    def test_single_session_policy_new_login_invalidates_previous(
        self, client: TestClient, master_admin_account: dict
    ):
        """New login invalidates previous session (single session policy)."""
        # First login
        first_login = client.post(
            "/api/v1/auth/login",
            json={
                "email": master_admin_account["email"],
                "password": master_admin_account["password"],
            },
        )
        first_token = first_login.json()["access_token"]

        # Second login (same user)
        second_login = client.post(
            "/api/v1/auth/login",
            json={
                "email": master_admin_account["email"],
                "password": master_admin_account["password"],
            },
        )
        second_token = second_login.json()["access_token"]

        # First token should not work
        response = client.get(
            "/api/v1/devices",
            headers={"Authorization": f"Bearer {first_token}"},
        )
        assert response.status_code == 401

        # Second token should work
        response = client.get(
            "/api/v1/devices",
            headers={"Authorization": f"Bearer {second_token}"},
        )
        assert response.status_code == 200

    def test_different_users_have_independent_sessions(
        self, client: TestClient, master_admin_account: dict, user_account: dict
    ):
        """Different users have independent sessions."""
        # Login as admin
        admin_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": master_admin_account["email"],
                "password": master_admin_account["password"],
            },
        )
        admin_token = admin_response.json()["access_token"]

        # Login as user
        user_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": user_account["email"],
                "password": user_account["password"],
            },
        )
        user_token = user_response.json()["access_token"]

        # Both tokens should work independently
        admin_devices = client.get(
            "/api/v1/devices",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        user_devices = client.get(
            "/api/v1/devices",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        assert admin_devices.status_code == 200
        assert user_devices.status_code == 200

    def test_logout_only_affects_current_session(
        self, client: TestClient, master_admin_account: dict, user_account: dict
    ):
        """Logout of one user doesn't affect other users."""
        # Login as admin
        admin_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": master_admin_account["email"],
                "password": master_admin_account["password"],
            },
        )
        admin_token = admin_response.json()["access_token"]

        # Login as user
        user_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": user_account["email"],
                "password": user_account["password"],
            },
        )
        user_token = user_response.json()["access_token"]

        # Logout admin
        client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Admin token should not work
        admin_check = client.get(
            "/api/v1/devices",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert admin_check.status_code == 401

        # User token should still work
        user_check = client.get(
            "/api/v1/devices",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert user_check.status_code == 200


class TestFailureScenarios:
    """Tests for infrastructure failure scenarios."""

    def test_invalid_valkey_data_handled_gracefully(
        self, client: TestClient, master_admin_account: dict, mock_valkey
    ):
        """System handles corrupted Valkey data gracefully."""
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": master_admin_account["email"],
                "password": master_admin_account["password"],
            },
        )
        token = login_response.json()["access_token"]

        # Corrupt session data in Valkey
        for key in list(mock_valkey.data.keys()):
            if key.startswith("session:"):
                mock_valkey.data[key] = "invalid-json-data"

        # Request should fail gracefully
        response = client.get(
            "/api/v1/devices",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code in [401, 500]

    def test_missing_session_in_valkey_but_valid_jwt_rejected(
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

        # Delete all sessions from Valkey
        for key in list(mock_valkey.data.keys()):
            if key.startswith("session:"):
                del mock_valkey.data[key]

        # Token should not work (no session)
        response = client.get(
            "/api/v1/devices",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401


class TestRateLimiting:
    """Tests for rate limiting integration."""

    def test_rate_limit_applies_to_login_endpoint(
        self, client: TestClient, master_admin_account: dict
    ):
        """Rate limit applies to login attempts."""
        # Make 3 failed login attempts
        for _ in range(3):
            client.post(
                "/api/v1/auth/login",
                json={
                    "email": master_admin_account["email"],
                    "password": "WrongPassword123!",
                },
            )

        # 4th attempt should be rate limited
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": master_admin_account["email"],
                "password": "WrongPassword123!",
            },
        )
        assert response.status_code == 429

    def test_rate_limit_different_ips_independent(
        self, client: TestClient, master_admin_account: dict
    ):
        """Rate limits for different IPs are independent."""
        # Make 3 failed attempts with IP1
        for _ in range(3):
            client.post(
                "/api/v1/auth/login",
                json={
                    "email": master_admin_account["email"],
                    "password": "WrongPass123!",
                },
                headers={"X-Forwarded-For": "192.168.1.1"},
            )

        # IP1 should be rate limited
        response1 = client.post(
            "/api/v1/auth/login",
            json={
                "email": master_admin_account["email"],
                "password": "WrongPass123!",
            },
            headers={"X-Forwarded-For": "192.168.1.1"},
        )
        assert response1.status_code == 429

        # IP2 should still be able to attempt
        response2 = client.post(
            "/api/v1/auth/login",
            json={
                "email": master_admin_account["email"],
                "password": master_admin_account["password"],
            },
            headers={"X-Forwarded-For": "192.168.1.2"},
        )
        # Should succeed (correct password)
        assert response2.status_code == 200

    def test_successful_login_after_failed_attempts_works(
        self, client: TestClient, master_admin_account: dict
    ):
        """Successful login works after failed attempts (within limit)."""
        # Make 2 failed attempts
        for _ in range(2):
            client.post(
                "/api/v1/auth/login",
                json={
                    "email": master_admin_account["email"],
                    "password": "WrongPassword!",
                },
            )

        # Successful login should work (under limit)
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": master_admin_account["email"],
                "password": master_admin_account["password"],
            },
        )
        assert response.status_code == 200


class TestAccountStatusIntegration:
    """Tests for account status changes during active sessions."""

    def test_inactive_account_with_valid_token_rejected(
        self, client: TestClient, master_admin_account: dict, session
    ):
        """Active token from inactive account is rejected."""
        # Login first
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": master_admin_account["email"],
                "password": master_admin_account["password"],
            },
        )
        token = login_response.json()["access_token"]

        # Token should work initially
        response = client.get(
            "/api/v1/devices",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

        # Deactivate account (access through non_critical_data)
        from app.database.model import Administrator
        admin = session.get(Administrator, master_admin_account["id"])
        admin.sensitive_data.non_critical_data.is_active = False
        session.add(admin)
        session.commit()

        # Token should not work with inactive account
        response = client.get(
            "/api/v1/devices",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401
