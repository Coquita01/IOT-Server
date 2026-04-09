import pytest
from fastapi.testclient import TestClient


class TestSessionManagement:

    def test_refresh_token_successful(
        self, client: TestClient, master_admin_account: dict
    ):
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": master_admin_account["email"],
                "password": master_admin_account["password"],
            },
        )
        assert login_response.status_code == 200
        login_data = login_response.json()
        refresh_token = login_data["refresh_token"]

        refresh_response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert refresh_response.status_code == 200
        refresh_data = refresh_response.json()
        
        assert "access_token" in refresh_data
        assert "refresh_token" in refresh_data
        assert refresh_data["account_type"] == "administrator"
        assert refresh_data["refresh_token"] != refresh_token

    def test_refresh_token_invalid(self, client: TestClient):
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "x" * 43},
        )
        assert response.status_code == 401
        assert "Invalid or expired refresh token" in response.json()["detail"]

    def test_logout_successful(
        self, client: TestClient, master_admin_account: dict
    ):
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": master_admin_account["email"],
                "password": master_admin_account["password"],
            },
        )
        assert login_response.status_code == 200
        access_token = login_response.json()["access_token"]

        logout_response = client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert logout_response.status_code == 200
        assert logout_response.json()["message"] == "Logout successful"

        devices_response = client.get(
            "/api/v1/devices",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert devices_response.status_code == 401

    def test_access_with_blacklisted_token(
        self, client: TestClient, master_admin_account: dict
    ):
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": master_admin_account["email"],
                "password": master_admin_account["password"],
            },
        )
        access_token = login_response.json()["access_token"]

        client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        response = client.get(
            "/api/v1/administrators",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 401
        assert "revoked" in response.json()["detail"].lower()

    def test_single_session_policy(
        self, client: TestClient, master_admin_account: dict
    ):
        first_login = client.post(
            "/api/v1/auth/login",
            json={
                "email": master_admin_account["email"],
                "password": master_admin_account["password"],
            },
        )
        first_token = first_login.json()["access_token"]

        second_login = client.post(
            "/api/v1/auth/login",
            json={
                "email": master_admin_account["email"],
                "password": master_admin_account["password"],
            },
        )
        second_token = second_login.json()["access_token"]

        first_request = client.get(
            "/api/v1/administrators",
            headers={"Authorization": f"Bearer {first_token}"},
        )
        assert first_request.status_code == 401

        second_request = client.get(
            "/api/v1/administrators",
            headers={"Authorization": f"Bearer {second_token}"},
        )
        assert second_request.status_code == 200

    def test_rate_limiting(self, client: TestClient):
        for i in range(4):
            response = client.post(
                "/api/v1/auth/login",
                json={
                    "email": "fake@test.com",
                    "password": "wrongpassword",
                },
            )
            if i < 3:
                assert response.status_code == 400
            else:
                assert response.status_code == 429
                assert "Too many login attempts" in response.json()["detail"]
