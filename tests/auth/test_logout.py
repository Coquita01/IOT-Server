from fastapi.testclient import TestClient


class TestLogout:
    def test_logout_revokes_token(
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

        token = login_response.json()["access_token"]

        logout_response = client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert logout_response.status_code == 200
        assert logout_response.json()["message"] == "Logged out successfully"

        protected_response = client.get(
            "/api/v1/users",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert protected_response.status_code == 401