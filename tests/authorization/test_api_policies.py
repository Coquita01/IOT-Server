import pytest
from fastapi.testclient import TestClient
from uuid import uuid4

from tests.conftest import create_test_token as create_token


class TestDevicePoliciesAPI:
    """Test OSO policies for Device endpoints at API level."""

    def test_manager_can_list_devices(
        self, client: TestClient, manager_account: dict
    ):
        """Manager should be able to list devices (read permission)."""
        token = create_token(manager_account)
        response = client.get(
            "/api/v1/devices",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    def test_manager_can_delete_devices(
        self, client: TestClient, manager_account: dict
    ):
        """Manager should be able to delete devices."""
        token = create_token(manager_account)
        fake_device_id = str(uuid4())
        response = client.delete(
            f"/api/v1/devices/{fake_device_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        # 404 because device doesn't exist, but passed authorization check
        assert response.status_code in [404, 422]

    def test_admin_can_delete_devices(
        self, client: TestClient, regular_admin_account: dict
    ):
        """Admin should be able to delete devices."""
        token = create_token(regular_admin_account)
        fake_device_id = str(uuid4())
        response = client.delete(
            f"/api/v1/devices/{fake_device_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        # 404 because device doesn't exist, but passed authorization check
        assert response.status_code in [404, 422]

    def test_user_can_read_devices(
        self, client: TestClient, user_account: dict
    ):
        """User should be able to read devices."""
        token = create_token(user_account)
        response = client.get(
            "/api/v1/devices",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    def test_user_cannot_create_devices(
        self, client: TestClient, user_account: dict
    ):
        """User should NOT be able to create devices."""
        token = create_token(user_account)
        response = client.post(
            "/api/v1/devices",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "Test Device",
                "description": "Test",
                "location": "Test Location",
            },
        )
        assert response.status_code == 403


class TestUserPoliciesAPI:
    """Test OSO policies for User endpoints at API level."""

    def test_manager_can_list_users(
        self, client: TestClient, manager_account: dict
    ):
        """Manager should be able to list users (read permission)."""
        token = create_token(manager_account)
        response = client.get(
            "/api/v1/users",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    def test_manager_cannot_delete_users(
        self, client: TestClient, manager_account: dict
    ):
        """Manager should NOT be able to delete users."""
        token = create_token(manager_account)
        fake_user_id = str(uuid4())
        response = client.delete(
            f"/api/v1/users/{fake_user_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403

    def test_admin_can_delete_users(
        self, client: TestClient, regular_admin_account: dict
    ):
        """Admin should be able to delete users."""
        token = create_token(regular_admin_account)
        fake_user_id = str(uuid4())
        response = client.delete(
            f"/api/v1/users/{fake_user_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        # 404 because user doesn't exist, but passed authorization check
        assert response.status_code in [404, 422]

    def test_regular_user_cannot_list_users(
        self, client: TestClient, user_account: dict
    ):
        """Regular user should NOT be able to list users."""
        token = create_token(user_account)
        response = client.get(
            "/api/v1/users",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403


class TestManagerPoliciesAPI:
    """Test OSO policies for Manager endpoints at API level."""

    def test_manager_can_list_managers(
        self, client: TestClient, manager_account: dict
    ):
        """Manager should be able to list managers (read permission)."""
        token = create_token(manager_account)
        response = client.get(
            "/api/v1/managers",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    def test_manager_cannot_delete_managers(
        self, client: TestClient, manager_account: dict
    ):
        """Manager should NOT be able to delete other managers."""
        token = create_token(manager_account)
        fake_manager_id = str(uuid4())
        response = client.delete(
            f"/api/v1/managers/{fake_manager_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403

    def test_admin_can_delete_managers(
        self, client: TestClient, regular_admin_account: dict
    ):
        """Admin should be able to delete managers."""
        token = create_token(regular_admin_account)
        fake_manager_id = str(uuid4())
        response = client.delete(
            f"/api/v1/managers/{fake_manager_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        # 404 because manager doesn't exist, but passed authorization check
        assert response.status_code in [404, 422]

    def test_user_cannot_list_managers(
        self, client: TestClient, user_account: dict
    ):
        """Regular user should NOT be able to list managers."""
        token = create_token(user_account)
        response = client.get(
            "/api/v1/managers",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403


class TestAdministratorPoliciesAPI:
    """Test OSO policies for Administrator endpoints at API level."""

    def test_regular_admin_can_read_administrators(
        self, client: TestClient, regular_admin_account: dict
    ):
        """Regular admin should be able to read administrators."""
        token = create_token(regular_admin_account)
        response = client.get(
            "/api/v1/administrators",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    def test_regular_admin_cannot_create_administrators(
        self, client: TestClient, regular_admin_account: dict
    ):
        """Regular admin should NOT be able to create administrators."""
        token = create_token(regular_admin_account)
        response = client.post(
            "/api/v1/administrators",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "first_name": "New",
                "last_name": "Admin",
                "email": "new_admin@test.com",
                "password": "Password123!",
            },
        )
        assert response.status_code == 403

    def test_regular_admin_cannot_delete_administrators(
        self, client: TestClient, regular_admin_account: dict
    ):
        """Regular admin should NOT be able to delete administrators."""
        token = create_token(regular_admin_account)
        fake_admin_id = str(uuid4())
        response = client.delete(
            f"/api/v1/administrators/{fake_admin_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403

    def test_master_admin_can_delete_administrators(
        self, client: TestClient, master_admin_account: dict
    ):
        """Master admin should be able to delete administrators."""
        token = create_token(master_admin_account)
        fake_admin_id = str(uuid4())
        response = client.delete(
            f"/api/v1/administrators/{fake_admin_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        # 404 because admin doesn't exist, but passed authorization check
        assert response.status_code in [404, 422]

    def test_manager_cannot_read_administrators(
        self, client: TestClient, manager_account: dict
    ):
        """Manager should NOT be able to read administrators."""
        token = create_token(manager_account)
        response = client.get(
            "/api/v1/administrators",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403

    def test_user_cannot_read_administrators(
        self, client: TestClient, user_account: dict
    ):
        """Regular user should NOT be able to read administrators."""
        token = create_token(user_account)
        response = client.get(
            "/api/v1/administrators",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403


class TestCrossResourcePolicies:
    """Test OSO policies across different resources to verify consistency."""

    def test_manager_write_permissions_consistent(
        self, client: TestClient, manager_account: dict
    ):
        """Manager should have consistent write permissions across resources."""
        token = create_token(manager_account)
        
        # Manager CAN create devices
        response = client.post(
            "/api/v1/devices",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "Test Device",
                "description": "Test",
                "location": "Test Location",
            },
        )
        assert response.status_code in [200, 201, 422]  # 422 if validation fails
        
        # Manager CAN create users
        response = client.post(
            "/api/v1/users",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "first_name": "Test",
                "last_name": "User",
                "email": "test@example.com",
                "password": "Password123!",
            },
        )
        assert response.status_code in [200, 201, 422]

    def test_manager_delete_permissions_consistent(
        self, client: TestClient, manager_account: dict
    ):
        """Manager should be able to delete devices but not users/managers."""
        token = create_token(manager_account)
        fake_id = str(uuid4())
        
        # Manager CAN delete devices
        response = client.delete(
            f"/api/v1/devices/{fake_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code in [404, 422]  # Passed auth, device not found
        
        # Manager CANNOT delete users
        response = client.delete(
            f"/api/v1/users/{fake_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403
        
        # Manager CANNOT delete managers
        response = client.delete(
            f"/api/v1/managers/{fake_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403

    def test_master_admin_universal_access(
        self, client: TestClient, master_admin_account: dict
    ):
        """Master admin should have access to all endpoints."""
        token = create_token(master_admin_account)
        
        # Can access devices
        response = client.get(
            "/api/v1/devices",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        
        # Can access users
        response = client.get(
            "/api/v1/users",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        
        # Can access managers
        response = client.get(
            "/api/v1/managers",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        
        # Can access administrators
        response = client.get(
            "/api/v1/administrators",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    def test_user_read_only_limited(
        self, client: TestClient, user_account: dict
    ):
        """User should only have read access to devices, nothing else."""
        token = create_token(user_account)
        
        # User CAN read devices
        response = client.get(
            "/api/v1/devices",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        
        # User CANNOT read users
        response = client.get(
            "/api/v1/users",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403
        
        # User CANNOT read managers
        response = client.get(
            "/api/v1/managers",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403
        
        # User CANNOT read administrators
        response = client.get(
            "/api/v1/administrators",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403
