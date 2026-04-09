"""
Test Session API Policies
Tests HTTP/API level policies for session management endpoints.
Similar to test_api_policies.py for OSO authorization.
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timezone

from tests.conftest import create_test_token


class TestLoginHTTPPolicies:
    """HTTP/API level tests for login endpoint."""

    def test_login_returns_200_on_success(
        self, client: TestClient, master_admin_account: dict
    ):
        """Login with valid credentials returns 200 OK."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": master_admin_account["email"],
                "password": master_admin_account["password"],
            },
        )
        assert response.status_code == 200

    def test_login_returns_400_on_invalid_credentials(self, client: TestClient):
        """Login with invalid credentials returns 400 Bad Request."""
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "nonexistent@test.com", "password": "WrongPass123!"},
        )
        assert response.status_code == 400
        assert "Invalid credentials" in response.json()["detail"]

    def test_login_returns_422_on_malformed_email(self, client: TestClient):
        """Login with malformed email returns 422 Unprocessable Entity."""
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "not-an-email", "password": "Password123!"},
        )
        assert response.status_code == 422

    def test_login_returns_422_on_short_password(self, client: TestClient):
        """Login with short password returns 422."""
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "user@test.com", "password": "short"},
        )
        assert response.status_code == 422

    def test_login_returns_422_on_missing_email(self, client: TestClient):
        """Login without email field returns 422."""
        response = client.post(
            "/api/v1/auth/login",
            json={"password": "Password123!"},
        )
        assert response.status_code == 422

    def test_login_returns_422_on_missing_password(self, client: TestClient):
        """Login without password field returns 422."""
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "user@test.com"},
        )
        assert response.status_code == 422

    def test_login_response_has_correct_structure(
        self, client: TestClient, master_admin_account: dict
    ):
        """Login response has all required fields."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": master_admin_account["email"],
                "password": master_admin_account["password"],
            },
        )
        data = response.json()
        
        assert "access_token" in data
        assert "refresh_token" in data
        assert "token_type" in data
        assert "account_type" in data
        assert "is_master" in data
        assert data["token_type"] == "bearer"

    def test_login_response_has_correct_content_type(
        self, client: TestClient, master_admin_account: dict
    ):
        """Login response has application/json content type."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": master_admin_account["email"],
                "password": master_admin_account["password"],
            },
        )
        assert "application/json" in response.headers["content-type"]


class TestRefreshHTTPPolicies:
    """HTTP/API level tests for refresh token endpoint."""

    def test_refresh_returns_200_on_success(
        self, client: TestClient, master_admin_account: dict
    ):
        """Refresh with valid token returns 200 OK."""
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": master_admin_account["email"],
                "password": master_admin_account["password"],
            },
        )
        refresh_token = login_response.json()["refresh_token"]

        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert response.status_code == 200

    def test_refresh_returns_401_on_invalid_token(self, client: TestClient):
        """Refresh with invalid token returns 401 Unauthorized."""
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "x" * 43},
        )
        assert response.status_code == 401

    def test_refresh_returns_422_on_missing_token(self, client: TestClient):
        """Refresh without token field returns 422."""
        response = client.post("/api/v1/auth/refresh", json={})
        assert response.status_code == 422

    def test_refresh_returns_422_on_short_token(self, client: TestClient):
        """Refresh with short token returns 422."""
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "short"},
        )
        assert response.status_code == 422

    def test_refresh_rotates_both_tokens(
        self, client: TestClient, master_admin_account: dict
    ):
        """Refresh returns different access_token and refresh_token."""
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": master_admin_account["email"],
                "password": master_admin_account["password"],
            },
        )
        old_access = login_response.json()["access_token"]
        old_refresh = login_response.json()["refresh_token"]

        refresh_response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": old_refresh},
        )
        new_access = refresh_response.json()["access_token"]
        new_refresh = refresh_response.json()["refresh_token"]

        assert new_access != old_access
        assert new_refresh != old_refresh

    def test_refresh_response_has_correct_structure(
        self, client: TestClient, master_admin_account: dict
    ):
        """Refresh response has all required fields."""
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": master_admin_account["email"],
                "password": master_admin_account["password"],
            },
        )
        refresh_token = login_response.json()["refresh_token"]

        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        data = response.json()

        assert "access_token" in data
        assert "refresh_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"


class TestLogoutHTTPPolicies:
    """HTTP/API level tests for logout endpoint."""

    def test_logout_returns_200_on_success(
        self, client: TestClient, master_admin_account: dict
    ):
        """Logout with valid token returns 200 OK."""
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": master_admin_account["email"],
                "password": master_admin_account["password"],
            },
        )
        access_token = login_response.json()["access_token"]

        response = client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200

    def test_logout_requires_bearer_token(self, client: TestClient):
        """Logout without Bearer token returns 401."""
        response = client.post("/api/v1/auth/logout")
        assert response.status_code == 401

    def test_logout_with_malformed_header_returns_401(self, client: TestClient):
        """Logout with malformed Authorization header returns 401."""
        response = client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": "NotBearer token"},
        )
        assert response.status_code == 401

    def test_logout_with_invalid_token_returns_401(self, client: TestClient):
        """Logout with invalid token returns 401."""
        response = client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert response.status_code == 401

    def test_logout_response_has_message(
        self, client: TestClient, master_admin_account: dict
    ):
        """Logout response contains success message."""
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": master_admin_account["email"],
                "password": master_admin_account["password"],
            },
        )
        access_token = login_response.json()["access_token"]

        response = client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert "message" in response.json()
        assert "Logout successful" in response.json()["message"]


class TestSessionValidationPolicies:
    """HTTP/API level tests for session validation in middleware."""

    def test_blacklisted_token_returns_401(
        self, client: TestClient, master_admin_account: dict
    ):
        """Blacklisted token returns 401 Unauthorized."""
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": master_admin_account["email"],
                "password": master_admin_account["password"],
            },
        )
        access_token = login_response.json()["access_token"]

        # Logout blacklists the token
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
        assert "revoked" in response.json()["detail"].lower()

    def test_token_without_bearer_prefix_returns_401(
        self, client: TestClient, master_admin_account: dict
    ):
        """Token without 'Bearer' prefix returns 401."""
        token = create_test_token(master_admin_account)
        
        response = client.get(
            "/api/v1/devices",
            headers={"Authorization": token},
        )
        assert response.status_code == 401

    def test_missing_authorization_header_allows_public_paths(
        self, client: TestClient
    ):
        """Missing Authorization header is allowed for public paths."""
        # /docs and /api/v1/auth/login are public
        response = client.get("/docs")
        # Docs might redirect, but shouldn't be 401
        assert response.status_code != 401


class TestErrorResponseConsistency:
    """Tests that all error responses follow consistent format."""

    def test_all_auth_errors_return_json(self, client: TestClient):
        """All authentication errors return JSON responses."""
        # Invalid login
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "bad@test.com", "password": "WrongPass123!"},
        )
        assert response.headers["content-type"] == "application/json"
        assert "detail" in response.json()

    def test_error_messages_are_generic_for_security(
        self, client: TestClient, master_admin_account: dict
    ):
        """Error messages don't leak information."""
        # Wrong email
        response1 = client.post(
            "/api/v1/auth/login",
            json={"email": "nonexistent@test.com", "password": "Pass123!"},
        )
        
        # Wrong password
        response2 = client.post(
            "/api/v1/auth/login",
            json={
                "email": master_admin_account["email"],
                "password": "WrongPassword123!",
            },
        )

        # Both should return same generic message
        assert response1.json()["detail"] == response2.json()["detail"]
        assert "Invalid credentials" in response1.json()["detail"]

    def test_401_responses_have_consistent_structure(self, client: TestClient):
        """All 401 responses have 'detail' field."""
        # Invalid token
        response = client.get(
            "/api/v1/devices",
            headers={"Authorization": "Bearer invalid"},
        )
        assert response.status_code == 401
        assert "detail" in response.json()
        assert isinstance(response.json()["detail"], str)

    def test_422_responses_have_error_details(self, client: TestClient):
        """422 responses include validation error details."""
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "invalid", "password": "short"},
        )
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        # FastAPI validation error format
        assert isinstance(data["detail"], list)
