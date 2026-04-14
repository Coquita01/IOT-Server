import pytest
from fastapi.testclient import TestClient
import jwt
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.config import settings


def create_token(account_data: dict) -> str:
    """Create a valid JWT token for testing."""
    to_encode = {
        "sub": str(account_data["id"]),
        "email": account_data["email"],
        "type": account_data["account_type"],
        "is_master": account_data["is_master"],
    }
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expire})
    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


class TestManagerList:
    """Test GET /managers endpoint."""

    def test_list_managers_as_master_admin(
        self, client: TestClient, master_admin_account: dict
    ):
        """Test listing managers as master admin."""
        token = create_token(master_admin_account)
        response = client.get(
            "/api/v1/managers",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "data" in data
        assert isinstance(data["data"], list)

    def test_list_managers_as_regular_admin(
        self, client: TestClient, regular_admin_account: dict
    ):
        """Test listing managers as regular admin."""
        token = create_token(regular_admin_account)
        response = client.get(
            "/api/v1/managers",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "data" in data

    def test_list_managers_as_manager(
        self, client: TestClient, manager_account: dict
    ):
        """Test listing managers as manager."""
        token = create_token(manager_account)
        response = client.get(
            "/api/v1/managers",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "data" in data

    def test_list_managers_as_user_forbidden(
        self, client: TestClient, user_account: dict
    ):
        """Test listing managers as user (forbidden)."""
        token = create_token(user_account)
        response = client.get(
            "/api/v1/managers",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403

    def test_list_managers_without_token(self, client: TestClient):
        """Test listing managers without authentication."""
        response = client.get("/api/v1/managers")
        assert response.status_code == 401

    def test_list_managers_pagination(
        self, client: TestClient, master_admin_account: dict
    ):
        """Test listing managers with pagination parameters."""
        token = create_token(master_admin_account)
        response = client.get(
            "/api/v1/managers?offset=0&limit=10",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 10
        assert data["offset"] == 0


class TestManagerRetrieve:
    """Test GET /managers/{id} endpoint."""

    def test_retrieve_manager_as_master_admin(
        self, client: TestClient, master_admin_account: dict, manager_account: dict
    ):
        """Test retrieving a manager as master admin."""
        token = create_token(master_admin_account)
        response = client.get(
            f"/api/v1/managers/{manager_account['id']}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "Jane"  # From fixture
        assert data["is_active"] is True

    def test_retrieve_manager_not_found(
        self, client: TestClient, master_admin_account: dict
    ):
        """Test retrieving a non-existent manager."""
        token = create_token(master_admin_account)
        response = client.get(
            f"/api/v1/managers/{uuid4()}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404

    def test_retrieve_manager_invalid_uuid(
        self, client: TestClient, master_admin_account: dict
    ):
        """Test retrieving manager with invalid UUID."""
        token = create_token(master_admin_account)
        response = client.get(
            "/api/v1/managers/not-a-uuid",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    def test_retrieve_manager_as_manager(
        self, client: TestClient, manager_account: dict
    ):
        """Test retrieving manager as manager (read-only)."""
        token = create_token(manager_account)
        response = client.get(
            f"/api/v1/managers/{manager_account['id']}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    def test_retrieve_manager_as_user_forbidden(
        self, client: TestClient, user_account: dict, manager_account: dict
    ):
        """Test retrieving manager as user (forbidden)."""
        token = create_token(user_account)
        response = client.get(
            f"/api/v1/managers/{manager_account['id']}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403


class TestManagerCreate:
    """Test POST /managers endpoint."""

    def test_create_manager_as_master_admin(
        self, client: TestClient, master_admin_account: dict
    ):
        """Test creating a new manager as master admin."""
        token = create_token(master_admin_account)
        manager_data = {
            "first_name": "Test",
            "last_name": "Manager",
            "second_last_name": "Name",
            "phone": "+523312345701",
            "address": "123 Test St",
            "city": "Mexico City",
            "state": "Mexico",
            "postal_code": "06500",
            "birth_date": datetime(1990, 6, 15).isoformat(),
            "email": "new_manager@test.com",
            "password": "TestPass123!",
            "curp": "TMAN111111HDFRRL09",
            "rfc": "TMAN111111AB0",
        }

        response = client.post(
            "/api/v1/managers",
            json=manager_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["first_name"] == "Test"
        assert data["is_active"] is True

    def test_create_manager_as_admin(
        self, client: TestClient, regular_admin_account: dict
    ):
        """Test creating manager as regular admin."""
        token = create_token(regular_admin_account)
        manager_data = {
            "first_name": "Admin",
            "last_name": "Manager",
            "second_last_name": "Name",
            "phone": "+523312345702",
            "address": "123 Test St",
            "city": "Mexico City",
            "state": "Mexico",
            "postal_code": "06500",
            "birth_date": datetime(1990, 6, 15).isoformat(),
            "email": "admin_manager@test.com",
            "password": "TestPass123!",
            "curp": "AMAN111111HDFRRL09",
            "rfc": "AMAN111111AB0",
        }

        response = client.post(
            "/api/v1/managers",
            json=manager_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 201

    def test_create_manager_as_manager_forbidden(
        self, client: TestClient, manager_account: dict
    ):
        """Test creating manager as manager (forbidden - read-only)."""
        token = create_token(manager_account)
        manager_data = {
            "first_name": "Forbidden",
            "last_name": "Manager",
            "second_last_name": "Name",
            "phone": "+523312345703",
            "address": "123 Test St",
            "city": "Mexico City",
            "state": "Mexico",
            "postal_code": "06500",
            "birth_date": datetime(1990, 6, 15).isoformat(),
            "email": "forbidden_manager@test.com",
            "password": "TestPass123!",
            "curp": "FMAN111111HDFRRL09",
            "rfc": "FMAN111111AB0",
        }

        response = client.post(
            "/api/v1/managers",
            json=manager_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403

    def test_create_manager_as_user_forbidden(
        self, client: TestClient, user_account: dict
    ):
        """Test creating manager as user (forbidden)."""
        token = create_token(user_account)
        manager_data = {
            "first_name": "User",
            "last_name": "Manager",
            "second_last_name": "Name",
            "phone": "+523312345704",
            "address": "123 Test St",
            "city": "Mexico City",
            "state": "Mexico",
            "postal_code": "06500",
            "birth_date": datetime(1990, 6, 15).isoformat(),
            "email": "user_manager@test.com",
            "password": "TestPass123!",
            "curp": "UMAN111111HDFRRL09",
            "rfc": "UMAN111111AB0",
        }

        response = client.post(
            "/api/v1/managers",
            json=manager_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403

    def test_create_manager_duplicate_email(
        self, client: TestClient, master_admin_account: dict, manager_account: dict
    ):
        """Test creating manager with duplicate email."""
        token = create_token(master_admin_account)
        manager_data = {
            "first_name": "Duplicate",
            "last_name": "Manager",
            "second_last_name": "Name",
            "phone": "+523312345705",
            "address": "123 Test St",
            "city": "Mexico City",
            "state": "Mexico",
            "postal_code": "06500",
            "birth_date": datetime(1990, 6, 15).isoformat(),
            "email": manager_account["email"],
            "password": "TestPass123!",
            "curp": "DMAN111111HDFRRL09",
            "rfc": "DMAN111111AB0",
        }

        response = client.post(
            "/api/v1/managers",
            json=manager_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 500

    def test_create_manager_missing_required_field(
        self, client: TestClient, master_admin_account: dict
    ):
        """Test creating manager with missing required field."""
        token = create_token(master_admin_account)
        manager_data = {
            "last_name": "Manager",
            "second_last_name": "Name",
            "phone": "+523312345706",
            "address": "123 Test St",
            "city": "Mexico City",
            "state": "Mexico",
            "postal_code": "06500",
            "birth_date": datetime(1990, 6, 15).isoformat(),
            "email": "missing@test.com",
            "password": "TestPass123!",
            "curp": "MMAN111111HDFRRL09",
            "rfc": "MMAN111111AB0",
        }

        response = client.post(
            "/api/v1/managers",
            json=manager_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    def test_create_manager_invalid_phone(
        self, client: TestClient, master_admin_account: dict
    ):
        """Test creating manager with invalid phone format."""
        token = create_token(master_admin_account)
        manager_data = {
            "first_name": "Phone",
            "last_name": "Manager",
            "second_last_name": "Name",
            "phone": "ABC123",
            "address": "123 Test St",
            "city": "Mexico City",
            "state": "Mexico",
            "postal_code": "06500",
            "birth_date": datetime(1990, 6, 15).isoformat(),
            "email": "phone_manager@test.com",
            "password": "TestPass123!",
            "curp": "PMAN111111HDFRRL09",
            "rfc": "PMAN111111AB0",
        }

        response = client.post(
            "/api/v1/managers",
            json=manager_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    def test_create_manager_invalid_curp(
        self, client: TestClient, master_admin_account: dict
    ):
        """Test creating manager with invalid CURP."""
        token = create_token(master_admin_account)
        manager_data = {
            "first_name": "Curp",
            "last_name": "Manager",
            "second_last_name": "Name",
            "phone": "+523312345707",
            "address": "123 Test St",
            "city": "Mexico City",
            "state": "Mexico",
            "postal_code": "06500",
            "birth_date": datetime(1990, 6, 15).isoformat(),
            "email": "curp_manager@test.com",
            "password": "TestPass123!",
            "curp": "INVALID",
            "rfc": "CMAN111111AB0",
        }

        response = client.post(
            "/api/v1/managers",
            json=manager_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422


class TestManagerUpdate:
    """Test PATCH /managers/{id} endpoint."""

    def test_update_manager_partial_as_master_admin(
        self, client: TestClient, master_admin_account: dict, manager_account: dict
    ):
        """Test updating manager with partial fields as master admin."""
        token = create_token(master_admin_account)

        response = client.patch(
            f"/api/v1/managers/{manager_account['id']}",
            json={"first_name": "PartialUpdate"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

        # Verify
        get_response = client.get(
            f"/api/v1/managers/{manager_account['id']}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert get_response.status_code == 200
        assert get_response.json()["first_name"] == "PartialUpdate"

    def test_update_manager_full_as_admin(
        self, client: TestClient, regular_admin_account: dict, manager_account: dict
    ):
        """Test updating multiple manager fields as admin."""
        token = create_token(regular_admin_account)

        response = client.patch(
            f"/api/v1/managers/{manager_account['id']}",
            json={
                "first_name": "UpdatedName",
                "last_name": "UpdatedLast",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

        # Verify
        get_response = client.get(
            f"/api/v1/managers/{manager_account['id']}",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = get_response.json()
        assert data["first_name"] == "UpdatedName"
        assert data["last_name"] == "UpdatedLast"

    def test_update_manager_deactivate(
        self, client: TestClient, master_admin_account: dict, manager_account: dict
    ):
        """Test deactivating a manager."""
        token = create_token(master_admin_account)

        response = client.patch(
            f"/api/v1/managers/{manager_account['id']}",
            json={"is_active": False},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

        # Verify
        get_response = client.get(
            f"/api/v1/managers/{manager_account['id']}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert get_response.json()["is_active"] is False

        # Reactivate for other tests
        client.patch(
            f"/api/v1/managers/{manager_account['id']}",
            json={"is_active": True},
            headers={"Authorization": f"Bearer {token}"},
        )

    def test_update_manager_as_manager_forbidden(
        self, client: TestClient, manager_account: dict, master_admin_account: dict
    ):
        """Test updating manager as manager (forbidden - read-only)."""
        # Create another manager to update
        admin_token = create_token(master_admin_account)
        manager_data = {
            "first_name": "Target",
            "last_name": "Manager",
            "second_last_name": "Name",
            "phone": "+523312345708",
            "address": "123 Test St",
            "city": "Mexico City",
            "state": "Mexico",
            "postal_code": "06500",
            "birth_date": datetime(1990, 6, 15).isoformat(),
            "email": "target_manager@test.com",
            "password": "TestPass123!",
            "curp": "TRGT111111HDFRRL09",
            "rfc": "TRGT111111AB0",
        }
        create_response = client.post(
            "/api/v1/managers",
            json=manager_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        target_id = create_response.json()["id"]

        # Try to update as manager
        manager_token = create_token(manager_account)
        response = client.patch(
            f"/api/v1/managers/{target_id}",
            json={"first_name": "Forbidden"},
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert response.status_code == 403

    def test_update_manager_as_user_forbidden(
        self, client: TestClient, user_account: dict, manager_account: dict
    ):
        """Test updating manager as user (forbidden)."""
        token = create_token(user_account)
        response = client.patch(
            f"/api/v1/managers/{manager_account['id']}",
            json={"first_name": "Forbidden"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403

    def test_update_manager_not_found(
        self, client: TestClient, master_admin_account: dict
    ):
        """Test updating non-existent manager."""
        token = create_token(master_admin_account)
        response = client.patch(
            f"/api/v1/managers/{uuid4()}",
            json={"first_name": "Not Found"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404


class TestManagerDelete:
    """Test DELETE /managers/{id} endpoint."""

    def test_delete_manager_as_master_admin(
        self, client: TestClient, master_admin_account: dict
    ):
        """Test deleting manager as master admin."""
        token = create_token(master_admin_account)

        # Create manager
        manager_data = {
            "first_name": "Delete",
            "last_name": "Manager",
            "second_last_name": "Name",
            "phone": "+523312345709",
            "address": "123 Test St",
            "city": "Mexico City",
            "state": "Mexico",
            "postal_code": "06500",
            "birth_date": datetime(1990, 6, 15).isoformat(),
            "email": "delete_manager@test.com",
            "password": "TestPass123!",
            "curp": "DELM111111HDFRRL09",
            "rfc": "DELM111111AB0",
        }
        create_response = client.post(
            "/api/v1/managers",
            json=manager_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        manager_id = create_response.json()["id"]

        # Delete
        response = client.delete(
            f"/api/v1/managers/{manager_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 204

        # Verify deletion
        get_response = client.get(
            f"/api/v1/managers/{manager_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert get_response.status_code == 404

    def test_delete_manager_as_admin(
        self, client: TestClient, regular_admin_account: dict
    ):
        """Test deleting manager as regular admin."""
        token = create_token(regular_admin_account)

        # Create manager
        manager_data = {
            "first_name": "AdminDelete",
            "last_name": "Manager",
            "second_last_name": "Name",
            "phone": "+523312345710",
            "address": "123 Test St",
            "city": "Mexico City",
            "state": "Mexico",
            "postal_code": "06500",
            "birth_date": datetime(1990, 6, 15).isoformat(),
            "email": "admin_delete_manager@test.com",
            "password": "TestPass123!",
            "curp": "ADLM111111HDFRRL09",
            "rfc": "ADLM111111AB0",
        }
        create_response = client.post(
            "/api/v1/managers",
            json=manager_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        manager_id = create_response.json()["id"]

        # Delete
        response = client.delete(
            f"/api/v1/managers/{manager_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 204

    def test_delete_manager_as_manager_forbidden(
        self, client: TestClient, manager_account: dict, master_admin_account: dict
    ):
        """Test deleting manager as manager (forbidden - read-only)."""
        # Create manager as admin
        admin_token = create_token(master_admin_account)
        manager_data = {
            "first_name": "ManagerDelete",
            "last_name": "Manager",
            "second_last_name": "Name",
            "phone": "+523312345711",
            "address": "123 Test St",
            "city": "Mexico City",
            "state": "Mexico",
            "postal_code": "06500",
            "birth_date": datetime(1990, 6, 15).isoformat(),
            "email": "manager_delete@test.com",
            "password": "TestPass123!",
            "curp": "MDLM111111HDFRRL09",
            "rfc": "MDLM111111AB0",
        }
        create_response = client.post(
            "/api/v1/managers",
            json=manager_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        manager_id = create_response.json()["id"]

        # Try to delete as manager
        manager_token = create_token(manager_account)
        response = client.delete(
            f"/api/v1/managers/{manager_id}",
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert response.status_code == 403

    def test_delete_manager_as_user_forbidden(
        self, client: TestClient, user_account: dict, manager_account: dict
    ):
        """Test deleting manager as user (forbidden)."""
        token = create_token(user_account)
        response = client.delete(
            f"/api/v1/managers/{manager_account['id']}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403

    def test_delete_manager_not_found(
        self, client: TestClient, master_admin_account: dict
    ):
        """Test deleting non-existent manager."""
        token = create_token(master_admin_account)
        response = client.delete(
            f"/api/v1/managers/{uuid4()}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404
