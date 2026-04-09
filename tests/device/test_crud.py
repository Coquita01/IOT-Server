import pytest
from fastapi.testclient import TestClient
from uuid import uuid4

from tests.conftest import create_test_token as create_token


class TestDeviceList:
    """Test GET /devices endpoint."""

    def test_list_devices_as_master_admin(
        self, client: TestClient, master_admin_account: dict
    ):
        """Test listing devices as master admin."""
        token = create_token(master_admin_account)
        response = client.get(
            "/api/v1/devices",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "data" in data
        assert isinstance(data["data"], list)

    def test_list_devices_as_regular_admin(
        self, client: TestClient, regular_admin_account: dict
    ):
        """Test listing devices as regular admin."""
        token = create_token(regular_admin_account)
        response = client.get(
            "/api/v1/devices",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "data" in data

    def test_list_devices_as_manager(
        self, client: TestClient, manager_account: dict
    ):
        """Test listing devices as manager."""
        token = create_token(manager_account)
        response = client.get(
            "/api/v1/devices",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "data" in data

    def test_list_devices_as_user(
        self, client: TestClient, user_account: dict
    ):
        """Test listing devices as regular user."""
        token = create_token(user_account)
        response = client.get(
            "/api/v1/devices",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "data" in data

    def test_list_devices_without_token(self, client: TestClient):
        """Test listing devices without authentication."""
        response = client.get("/api/v1/devices")
        assert response.status_code == 401

    def test_list_devices_pagination(
        self, client: TestClient, master_admin_account: dict
    ):
        """Test listing devices with pagination parameters."""
        token = create_token(master_admin_account)
        response = client.get(
            "/api/v1/devices?offset=0&limit=10",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 10
        assert data["offset"] == 0


class TestDeviceRetrieve:
    """Test GET /devices/{id} endpoint."""

    def test_retrieve_device_as_master_admin(
        self, client: TestClient, master_admin_account: dict
    ):
        """Test retrieving a device as master admin."""
        token = create_token(master_admin_account)
        
        # First create a device
        device_data = {
            "name": "Test Device",
            "brand": "TestBrand",
            "model": "TestModel",
            "serial_number": "SN123456789",
            "ip": "192.168.1.100",
            "mac": "00:11:22:33:44:55"
        }
        create_response = client.post(
            "/api/v1/devices",
            json=device_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert create_response.status_code == 201
        device_id = create_response.json()["id"]
        
        # Then retrieve it
        response = client.get(
            f"/api/v1/devices/{device_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Device"
        assert data["is_active"] is True

    def test_retrieve_device_not_found(
        self, client: TestClient, master_admin_account: dict
    ):
        """Test retrieving a non-existent device."""
        token = create_token(master_admin_account)
        response = client.get(
            f"/api/v1/devices/{uuid4()}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404

    def test_retrieve_device_invalid_uuid(
        self, client: TestClient, master_admin_account: dict
    ):
        """Test retrieving device with invalid UUID."""
        token = create_token(master_admin_account)
        response = client.get(
            "/api/v1/devices/not-a-uuid",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    def test_retrieve_device_as_user(
        self, client: TestClient, user_account: dict, master_admin_account: dict
    ):
        """Test retrieving device as regular user."""
        # Create device as admin
        admin_token = create_token(master_admin_account)
        device_data = {
            "name": "User Device",
            "brand": "TestBrand",
            "model": "TestModel",
            "serial_number": "SN987654321",
            "ip": "192.168.1.101",
            "mac": "00:11:22:33:44:66"
        }
        create_response = client.post(
            "/api/v1/devices",
            json=device_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        device_id = create_response.json()["id"]
        
        # Retrieve as user
        user_token = create_token(user_account)
        response = client.get(
            f"/api/v1/devices/{device_id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 200


class TestDeviceCreate:
    """Test POST /devices endpoint."""

    def test_create_device_as_master_admin(
        self, client: TestClient, master_admin_account: dict
    ):
        """Test creating a new device as master admin."""
        token = create_token(master_admin_account)
        device_data = {
            "name": "New Device",
            "brand": "BrandX",
            "model": "ModelY",
            "serial_number": "SN111222333",
            "ip": "192.168.1.102",
            "mac": "AA:BB:CC:DD:EE:FF"
        }

        response = client.post(
            "/api/v1/devices",
            json=device_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Device"
        assert data["is_active"] is True

    def test_create_device_as_admin(
        self, client: TestClient, regular_admin_account: dict
    ):
        """Test creating device as regular admin."""
        token = create_token(regular_admin_account)
        device_data = {
            "name": "Admin Device",
            "brand": "BrandX",
            "model": "ModelY",
            "serial_number": "SN444555666",
            "ip": "192.168.1.103",
            "mac": "11:22:33:44:55:66"
        }

        response = client.post(
            "/api/v1/devices",
            json=device_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 201

    def test_create_device_as_manager(
        self, client: TestClient, manager_account: dict
    ):
        """Test creating device as manager."""
        token = create_token(manager_account)
        device_data = {
            "name": "Manager Device",
            "brand": "BrandX",
            "model": "ModelY",
            "serial_number": "SN777888999",
            "ip": "192.168.1.104",
            "mac": "22:33:44:55:66:77"
        }

        response = client.post(
            "/api/v1/devices",
            json=device_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 201

    def test_create_device_as_user_forbidden(
        self, client: TestClient, user_account: dict
    ):
        """Test creating device as user (should be forbidden)."""
        token = create_token(user_account)
        device_data = {
            "name": "User Device",
            "brand": "BrandX",
            "model": "ModelY",
            "serial_number": "SN000111222",
            "ip": "192.168.1.105",
            "mac": "33:44:55:66:77:88"
        }

        response = client.post(
            "/api/v1/devices",
            json=device_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403

    def test_create_device_missing_required_field(
        self, client: TestClient, master_admin_account: dict
    ):
        """Test creating device with missing required field."""
        token = create_token(master_admin_account)
        device_data = {
            "brand": "BrandX",
            "model": "ModelY",
            "serial_number": "SN333444555",
            "ip": "192.168.1.106",
            "mac": "44:55:66:77:88:99"
        }

        response = client.post(
            "/api/v1/devices",
            json=device_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    def test_create_device_duplicate_serial_number(
        self, client: TestClient, master_admin_account: dict
    ):
        """Test creating device with duplicate serial number."""
        token = create_token(master_admin_account)
        device_data = {
            "name": "Device 1",
            "brand": "BrandX",
            "model": "ModelY",
            "serial_number": "SN_DUPLICATE",
            "ip": "192.168.1.107",
            "mac": "55:66:77:88:99:AA"
        }

        # Create first device
        response1 = client.post(
            "/api/v1/devices",
            json=device_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response1.status_code == 201

        # Try to create duplicate
        device_data["name"] = "Device 2"
        device_data["mac"] = "66:77:88:99:AA:BB"
        response2 = client.post(
            "/api/v1/devices",
            json=device_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response2.status_code == 500

    def test_create_device_duplicate_mac(
        self, client: TestClient, master_admin_account: dict
    ):
        """Test creating device with duplicate MAC address."""
        token = create_token(master_admin_account)
        device_data = {
            "name": "Device 3",
            "brand": "BrandX",
            "model": "ModelY",
            "serial_number": "SN_UNIQUE1",
            "ip": "192.168.1.108",
            "mac": "MAC_DUPLICATE"
        }

        # Create first device
        response1 = client.post(
            "/api/v1/devices",
            json=device_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response1.status_code == 201

        # Try to create duplicate
        device_data["name"] = "Device 4"
        device_data["serial_number"] = "SN_UNIQUE2"
        response2 = client.post(
            "/api/v1/devices",
            json=device_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response2.status_code == 500


class TestDeviceUpdate:
    """Test PATCH /devices/{id} endpoint."""

    def test_update_device_partial_as_admin(
        self, client: TestClient, master_admin_account: dict
    ):
        """Test updating device with partial fields."""
        token = create_token(master_admin_account)

        # Create device
        device_data = {
            "name": "Original Device",
            "brand": "BrandX",
            "model": "ModelY",
            "serial_number": "SN_UPDATE1",
            "ip": "192.168.1.109",
            "mac": "77:88:99:AA:BB:CC"
        }
        create_response = client.post(
            "/api/v1/devices",
            json=device_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        device_id = create_response.json()["id"]

        # Update partial
        response = client.patch(
            f"/api/v1/devices/{device_id}",
            json={"name": "Updated Device"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

        # Verify
        get_response = client.get(
            f"/api/v1/devices/{device_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert get_response.json()["name"] == "Updated Device"

    def test_update_device_full_as_manager(
        self, client: TestClient, manager_account: dict, master_admin_account: dict
    ):
        """Test updating multiple device fields as manager."""
        # Create device as admin
        admin_token = create_token(master_admin_account)
        device_data = {
            "name": "Manager Update Device",
            "brand": "BrandX",
            "model": "ModelY",
            "serial_number": "SN_UPDATE2",
            "ip": "192.168.1.110",
            "mac": "88:99:AA:BB:CC:DD"
        }
        create_response = client.post(
            "/api/v1/devices",
            json=device_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        device_id = create_response.json()["id"]

        # Update as manager
        manager_token = create_token(manager_account)
        response = client.patch(
            f"/api/v1/devices/{device_id}",
            json={
                "name": "Manager Updated",
                "brand": "NewBrand",
                "ip": "192.168.1.200"
            },
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert response.status_code == 200

        # Verify
        get_response = client.get(
            f"/api/v1/devices/{device_id}",
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        data = get_response.json()
        assert data["name"] == "Manager Updated"
        assert data["brand"] == "NewBrand"

    def test_update_device_deactivate(
        self, client: TestClient, master_admin_account: dict
    ):
        """Test deactivating a device."""
        token = create_token(master_admin_account)

        # Create device
        device_data = {
            "name": "Deactivate Device",
            "brand": "BrandX",
            "model": "ModelY",
            "serial_number": "SN_DEACTIVATE",
            "ip": "192.168.1.111",
            "mac": "99:AA:BB:CC:DD:EE"
        }
        create_response = client.post(
            "/api/v1/devices",
            json=device_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        device_id = create_response.json()["id"]

        # Deactivate
        response = client.patch(
            f"/api/v1/devices/{device_id}",
            json={"is_active": False},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

        # Verify
        get_response = client.get(
            f"/api/v1/devices/{device_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert get_response.json()["is_active"] is False

    def test_update_device_as_user_forbidden(
        self, client: TestClient, user_account: dict, master_admin_account: dict
    ):
        """Test updating device as user (forbidden)."""
        # Create device as admin
        admin_token = create_token(master_admin_account)
        device_data = {
            "name": "User Update Device",
            "brand": "BrandX",
            "model": "ModelY",
            "serial_number": "SN_USER_UPDATE",
            "ip": "192.168.1.112",
            "mac": "AA:BB:CC:DD:EE:FF"
        }
        create_response = client.post(
            "/api/v1/devices",
            json=device_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        device_id = create_response.json()["id"]

        # Try to update as user
        user_token = create_token(user_account)
        response = client.patch(
            f"/api/v1/devices/{device_id}",
            json={"name": "Forbidden Update"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 403

    def test_update_device_not_found(
        self, client: TestClient, master_admin_account: dict
    ):
        """Test updating non-existent device."""
        token = create_token(master_admin_account)
        response = client.patch(
            f"/api/v1/devices/{uuid4()}",
            json={"name": "Not Found"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404


class TestDeviceDelete:
    """Test DELETE /devices/{id} endpoint."""

    def test_delete_device_as_master_admin(
        self, client: TestClient, master_admin_account: dict
    ):
        """Test deleting device as master admin."""
        token = create_token(master_admin_account)

        # Create device
        device_data = {
            "name": "Delete Device",
            "brand": "BrandX",
            "model": "ModelY",
            "serial_number": "SN_DELETE1",
            "ip": "192.168.1.113",
            "mac": "BB:CC:DD:EE:FF:00"
        }
        create_response = client.post(
            "/api/v1/devices",
            json=device_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        device_id = create_response.json()["id"]

        # Delete
        response = client.delete(
            f"/api/v1/devices/{device_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 204

        # Verify deletion
        get_response = client.get(
            f"/api/v1/devices/{device_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert get_response.status_code == 404

    def test_delete_device_as_admin(
        self, client: TestClient, regular_admin_account: dict
    ):
        """Test deleting device as regular admin."""
        token = create_token(regular_admin_account)

        # Create device
        device_data = {
            "name": "Admin Delete Device",
            "brand": "BrandX",
            "model": "ModelY",
            "serial_number": "SN_DELETE2",
            "ip": "192.168.1.114",
            "mac": "CC:DD:EE:FF:00:11"
        }
        create_response = client.post(
            "/api/v1/devices",
            json=device_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        device_id = create_response.json()["id"]

        # Delete
        response = client.delete(
            f"/api/v1/devices/{device_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 204

    def test_delete_device_as_manager(
        self, client: TestClient, manager_account: dict, master_admin_account: dict
    ):
        """Test deleting device as manager (allowed per permission matrix)."""
        # Create device as admin
        admin_token = create_token(master_admin_account)
        device_data = {
            "name": "Manager Delete Device",
            "brand": "BrandX",
            "model": "ModelY",
            "serial_number": "SN_DELETE3",
            "ip": "192.168.1.115",
            "mac": "DD:EE:FF:00:11:22"
        }
        create_response = client.post(
            "/api/v1/devices",
            json=device_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        device_id = create_response.json()["id"]

        # Delete as manager
        manager_token = create_token(manager_account)
        response = client.delete(
            f"/api/v1/devices/{device_id}",
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert response.status_code == 204

    def test_delete_device_as_user_forbidden(
        self, client: TestClient, user_account: dict, master_admin_account: dict
    ):
        """Test deleting device as user (forbidden)."""
        # Create device as admin
        admin_token = create_token(master_admin_account)
        device_data = {
            "name": "User Delete Device",
            "brand": "BrandX",
            "model": "ModelY",
            "serial_number": "SN_DELETE4",
            "ip": "192.168.1.116",
            "mac": "EE:FF:00:11:22:33"
        }
        create_response = client.post(
            "/api/v1/devices",
            json=device_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        device_id = create_response.json()["id"]

        # Try to delete as user
        user_token = create_token(user_account)
        response = client.delete(
            f"/api/v1/devices/{device_id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 403

    def test_delete_device_not_found(
        self, client: TestClient, master_admin_account: dict
    ):
        """Test deleting non-existent device."""
        token = create_token(master_admin_account)
        response = client.delete(
            f"/api/v1/devices/{uuid4()}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404
