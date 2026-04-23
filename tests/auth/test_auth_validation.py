from fastapi.testclient import TestClient


class TestAuthValidation:
    def test_change_password_rejects_weak_new_password(
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

        response = client.patch(
            "/api/v1/auth/change-password",
            json={
                "current_password": master_admin_account["password"],
                "new_password": "12345678",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 422