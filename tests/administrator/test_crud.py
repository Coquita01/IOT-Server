import pytest
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
import jwt
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


class TestAdministratorList:
    """Test GET /administrators endpoint."""

    def test_list_administrators_as_master_admin(
        self, client: TestClient, master_admin_account: dict
    ):
        """Test listing administrators as master admin."""
        token = create_token(master_admin_account)
        response = client.get(
            "/api/v1/administrators",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "data" in data
        assert isinstance(data["data"], list)

    def test_list_administrators_as_regular_admin(
        self, client: TestClient, regular_admin_account: dict
    ):
        """Test listing administrators as regular (non-master) admin."""
        token = create_token(regular_admin_account)
        response = client.get(
            "/api/v1/administrators",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200  # Regular admins can read administrators

    def test_list_administrators_as_user(self, client: TestClient, user_account: dict):
        """Test listing administrators as user."""
        token = create_token(user_account)
        response = client.get(
            "/api/v1/administrators",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403

    def test_list_administrators_as_manager(
        self, client: TestClient, manager_account: dict
    ):
        """Test listing administrators as manager."""
        token = create_token(manager_account)
        response = client.get(
            "/api/v1/administrators",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403

    def test_list_administrators_without_token(self, client: TestClient):
        """Test listing administrators without authentication."""
        response = client.get("/api/v1/administrators")
        assert response.status_code == 401

    def test_list_administrators_pagination(
        self, client: TestClient, master_admin_account: dict
    ):
        """Test listing administrators with pagination parameters."""
        token = create_token(master_admin_account)
        response = client.get(
            "/api/v1/administrators?offset=0&limit=10",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 10
        assert data["offset"] == 0

    def test_list_administrators_items_do_not_expose_sensitive_fields(
        self, client: TestClient, master_admin_account: dict
    ):
        """Test list endpoint does not expose sensitive fields in items."""
        token = create_token(master_admin_account)
        response = client.get(
            "/api/v1/administrators",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

        items = response.json().get("data", [])
        sensitive_fields = {"password_hash", "curp", "rfc"}
        for item in items:
            # List payload must not leak sensitive identity fields.
            assert sensitive_fields.isdisjoint(item.keys())


class TestAdministratorRetrieve:
    """Test GET /administrators/{id} endpoint."""

    def test_retrieve_administrator_as_master_admin(
        self, client: TestClient, master_admin_account: dict
    ):
        """Test retrieving an administrator as master admin."""
        token = create_token(master_admin_account)
        response = client.get(
            f"/api/v1/administrators/{master_admin_account['id']}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "Admin"
        assert data["is_active"] is True

    def test_retrieve_administrator_not_found(
        self, client: TestClient, master_admin_account: dict
    ):
        """Test retrieving a non-existent administrator."""
        token = create_token(master_admin_account)
        response = client.get(
            f"/api/v1/administrators/{uuid4()}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404

    def test_retrieve_administrator_invalid_uuid(
        self, client: TestClient, master_admin_account: dict
    ):
        """Test retrieving administrator with invalid UUID."""
        token = create_token(master_admin_account)
        response = client.get(
            "/api/v1/administrators/not-a-uuid",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    def test_retrieve_administrator_as_regular_admin(
        self,
        client: TestClient,
        master_admin_account: dict,
        regular_admin_account: dict,
    ):
        """Test retrieving administrator as regular admin (allowed - can read)."""
        token = create_token(regular_admin_account)
        response = client.get(
            f"/api/v1/administrators/{master_admin_account['id']}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200  # Regular admins can read administrators

    def test_retrieve_administrator_response_does_not_expose_sensitive_fields(
        self, client: TestClient, master_admin_account: dict
    ):
        """Test retrieve endpoint does not expose sensitive fields."""
        token = create_token(master_admin_account)
        response = client.get(
            f"/api/v1/administrators/{master_admin_account['id']}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

        data = response.json()
        sensitive_fields = {"password_hash", "curp", "rfc"}
        assert sensitive_fields.isdisjoint(data.keys())


class TestAdministratorCreate:
    """Test POST /administrators endpoint."""

    def test_create_administrator_as_master_admin(
        self, client: TestClient, master_admin_account: dict
    ):
        """Test creating a new administrator as master admin."""
        token = create_token(master_admin_account)
        admin_data = {
            "first_name": "Test",
            "last_name": "User",
            "second_last_name": "Name",
            "phone": "+523312345700",
            "address": "123 Test St",
            "city": "Mexico City",
            "state": "Mexico",
            "postal_code": "06500",
            "birth_date": datetime(1990, 6, 15).isoformat(),
            "email": "new_admin@test.com",
            "password": "TestPass123!",
            "curp": "NEWC111111HDFRRL09",
            "rfc": "NEWC111111AB0",
        }

        response = client.post(
            "/api/v1/administrators",
            json=admin_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["first_name"] == "Test"
        assert data["is_active"] is True

    def test_create_administrator_duplicate_email(
        self,
        client: TestClient,
        master_admin_account: dict,
        regular_admin_account: dict,
    ):
        """Test creating administrator with duplicate email."""
        token = create_token(master_admin_account)
        admin_data = {
            "first_name": "Test",
            "last_name": "User",
            "second_last_name": "Name",
            "phone": "+523312345700",
            "address": "123 Test St",
            "city": "Mexico City",
            "state": "Mexico",
            "postal_code": "06500",
            "birth_date": datetime(1990, 6, 15).isoformat(),
            "email": regular_admin_account["email"],
            "password": "TestPass123!",
            "curp": "DUPC111111HDFRRL09",
            "rfc": "DUPC111111AB0",
        }

        response = client.post(
            "/api/v1/administrators",
            json=admin_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    def test_create_administrator_missing_required_field(
        self, client: TestClient, master_admin_account: dict
    ):
        """Test creating administrator with missing required field."""
        token = create_token(master_admin_account)
        admin_data = {
            "last_name": "User",
            "second_last_name": "Name",
            "phone": "+523312345700",
            "address": "123 Test St",
            "city": "Mexico City",
            "state": "Mexico",
            "postal_code": "06500",
            "birth_date": datetime(1990, 6, 15).isoformat(),
            "email": "test@example.com",
            "password": "TestPass123!",
            "curp": "MISS111111HDFRRL09",
            "rfc": "MISS111111AB0",
        }

        response = client.post(
            "/api/v1/administrators",
            json=admin_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    def test_create_administrator_invalid_phone(
        self, client: TestClient, master_admin_account: dict
    ):
        """Test creating administrator with invalid phone format."""
        token = create_token(master_admin_account)
        admin_data = {
            "first_name": "Test",
            "last_name": "User",
            "second_last_name": "Name",
            "phone": "ABC123",
            "address": "123 Test St",
            "city": "Mexico City",
            "state": "Mexico",
            "postal_code": "06500",
            "birth_date": datetime(1990, 6, 15).isoformat(),
            "email": "admin_phone@test.com",
            "password": "TestPass123!",
            "curp": "PHON111111HDFRRL09",
            "rfc": "PHON111111AB0",
        }

        response = client.post(
            "/api/v1/administrators",
            json=admin_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    def test_create_administrator_invalid_postal_code(
        self, client: TestClient, master_admin_account: dict
    ):
        """Test creating administrator with invalid postal code."""
        token = create_token(master_admin_account)
        admin_data = {
            "first_name": "Test",
            "last_name": "User",
            "second_last_name": "Name",
            "phone": "+523312345700",
            "address": "123 Test St",
            "city": "Mexico City",
            "state": "Mexico",
            "postal_code": "123",
            "birth_date": datetime(1990, 6, 15).isoformat(),
            "email": "admin_postal@test.com",
            "password": "TestPass123!",
            "curp": "POST111111HDFRRL09",
            "rfc": "POST111111AB0",
        }

        response = client.post(
            "/api/v1/administrators",
            json=admin_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    def test_create_administrator_invalid_curp(
        self, client: TestClient, master_admin_account: dict
    ):
        """Test creating administrator with invalid CURP."""
        token = create_token(master_admin_account)
        admin_data = {
            "first_name": "Test",
            "last_name": "User",
            "second_last_name": "Name",
            "phone": "+523312345700",
            "address": "123 Test St",
            "city": "Mexico City",
            "state": "Mexico",
            "postal_code": "06500",
            "birth_date": datetime(1990, 6, 15).isoformat(),
            "email": "admin_curp@test.com",
            "password": "TestPass123!",
            "curp": "INVALID",
            "rfc": "CURP111111AB0",
        }

        response = client.post(
            "/api/v1/administrators",
            json=admin_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    def test_create_administrator_invalid_rfc(
        self, client: TestClient, master_admin_account: dict
    ):
        """Test creating administrator with invalid RFC."""
        token = create_token(master_admin_account)
        admin_data = {
            "first_name": "Test",
            "last_name": "User",
            "second_last_name": "Name",
            "phone": "+523312345700",
            "address": "123 Test St",
            "city": "Mexico City",
            "state": "Mexico",
            "postal_code": "06500",
            "birth_date": datetime(1990, 6, 15).isoformat(),
            "email": "admin_rfc@test.com",
            "password": "TestPass123!",
            "curp": "CURF111111HDFRRL09",
            "rfc": "INVALID",
        }

        response = client.post(
            "/api/v1/administrators",
            json=admin_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    def test_create_administrator_future_birth_date(
        self, client: TestClient, master_admin_account: dict
    ):
        """Test creating administrator with future birth date."""
        token = create_token(master_admin_account)
        future_date = (datetime.now() + timedelta(days=1)).isoformat()
        admin_data = {
            "first_name": "Test",
            "last_name": "User",
            "second_last_name": "Name",
            "phone": "+523312345700",
            "address": "123 Test St",
            "city": "Mexico City",
            "state": "Mexico",
            "postal_code": "06500",
            "birth_date": future_date,
            "email": "admin_birth@test.com",
            "password": "TestPass123!",
            "curp": "FUTE111111HDFRRL09",
            "rfc": "FUTE111111AB0",
        }

        response = client.post(
            "/api/v1/administrators",
            json=admin_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    def test_create_administrator_as_regular_admin_forbidden(
        self, client: TestClient, regular_admin_account: dict
    ):
        """Test creating administrator as regular admin."""
        token = create_token(regular_admin_account)
        admin_data = {
            "first_name": "Test",
            "last_name": "User",
            "second_last_name": "Name",
            "phone": "+523312345700",
            "address": "123 Test St",
            "city": "Mexico City",
            "state": "Mexico",
            "postal_code": "06500",
            "birth_date": datetime(1990, 6, 15).isoformat(),
            "email": "test@example.com",
            "password": "TestPass123!",
            "curp": "ABCD111111HDFRRL09",
            "rfc": "ABCD111111AB0",
        }

        response = client.post(
            "/api/v1/administrators",
            json=admin_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403

    def test_create_administrator_as_user_forbidden(
        self, client: TestClient, user_account: dict
    ):
        """Test creating administrator as user."""
        token = create_token(user_account)
        admin_data = {
            "first_name": "Test",
            "last_name": "User",
            "second_last_name": "Name",
            "phone": "+523312345700",
            "address": "123 Test St",
            "city": "Mexico City",
            "state": "Mexico",
            "postal_code": "06500",
            "birth_date": datetime(1990, 6, 15).isoformat(),
            "email": "test@example.com",
            "password": "TestPass123!",
            "curp": "ABCD111111HDFRRL09",
            "rfc": "ABCD111111AB0",
        }

        response = client.post(
            "/api/v1/administrators",
            json=admin_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403


class TestAdministratorUpdate:
    """Test PATCH /administrators/{id} endpoint."""

    def test_update_administrator_partial(
        self,
        client: TestClient,
        master_admin_account: dict,
        regular_admin_account: dict,
    ):
        """Test updating administrator with partial fields actually persists changes."""
        token = create_token(master_admin_account)

        response = client.patch(
            f"/api/v1/administrators/{regular_admin_account['id']}",
            json={"first_name": "PartialUpdate"},
            headers={"Authorization": f"Bearer {token}"},
        )
        print(response.json())
        assert response.status_code == 200

        get_response = client.get(
            f"/api/v1/administrators/{regular_admin_account['id']}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert get_response.status_code == 200
        assert get_response.json()["first_name"] == "PartialUpdate"

    def test_update_administrator_full(
        self,
        client: TestClient,
        master_admin_account: dict,
        regular_admin_account: dict,
    ):
        """Test updating multiple fields at once and verifying persistence."""
        token = create_token(master_admin_account)

        response = client.patch(
            f"/api/v1/administrators/{regular_admin_account['id']}",
            json={
                "first_name": "UpdatedName",
                "last_name": "UpdatedLast",
                "phone": "+523312345777",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

        get_response = client.get(
            f"/api/v1/administrators/{regular_admin_account['id']}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert get_response.status_code == 200
        data = get_response.json()
        assert data["first_name"] == "UpdatedName"
        assert data["last_name"] == "UpdatedLast"

    def test_update_administrator_deactivate(
        self,
        client: TestClient,
        master_admin_account: dict,
        regular_admin_account: dict,
    ):
        """Test that deactivating an administrator actually persists."""
        token = create_token(master_admin_account)

        response = client.patch(
            f"/api/v1/administrators/{regular_admin_account['id']}",
            json={"is_active": False},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

        get_response = client.get(
            f"/api/v1/administrators/{regular_admin_account['id']}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert get_response.status_code == 200
        assert get_response.json()["is_active"] is False

    def test_update_administrator_not_found(
        self, client: TestClient, master_admin_account: dict
    ):
        """Test updating non-existent administrator."""
        token = create_token(master_admin_account)
        response = client.patch(
            f"/api/v1/administrators/{uuid4()}",
            json={"first_name": "Ghost"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404

    def test_update_administrator_invalid_email(
        self,
        client: TestClient,
        master_admin_account: dict,
        regular_admin_account: dict,
    ):
        """Test updating administrator with invalid email."""
        token = create_token(master_admin_account)
        response = client.patch(
            f"/api/v1/administrators/{regular_admin_account['id']}",
            json={"email": "@"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    def test_update_administrator_as_regular_admin_forbidden(
        self,
        client: TestClient,
        master_admin_account: dict,
        regular_admin_account: dict,
    ):
        """Test updating administrator as regular admin."""
        token = create_token(regular_admin_account)
        response = client.patch(
            f"/api/v1/administrators/{master_admin_account['id']}",
            json={"first_name": "Hacker"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403

    def test_update_administrator_partial_is_atomic_for_first_name(
        self,
        client: TestClient,
        master_admin_account: dict,
        regular_admin_account: dict,
    ):
        """Test first_name patch updates only that field and keeps others intact."""
        token = create_token(master_admin_account)

        before_response = client.get(
            f"/api/v1/administrators/{regular_admin_account['id']}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert before_response.status_code == 200
        before_data = before_response.json()

        patch_response = client.patch(
            f"/api/v1/administrators/{regular_admin_account['id']}",
            json={"first_name": "AtomicAdminName"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert patch_response.status_code == 200

        after_response = client.get(
            f"/api/v1/administrators/{regular_admin_account['id']}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert after_response.status_code == 200
        after_data = after_response.json()

        assert after_data["first_name"] == "AtomicAdminName"
        assert after_data["last_name"] == before_data["last_name"]
        # Some response schemas do not expose phone; verify it only when present.
        if "phone" in before_data and "phone" in after_data:
            assert after_data["phone"] == before_data["phone"]

    def test_update_administrator_partial_is_atomic_for_is_active(
        self,
        client: TestClient,
        master_admin_account: dict,
        regular_admin_account: dict,
    ):
        """Test is_active patch updates only status and keeps identity fields intact."""
        token = create_token(master_admin_account)

        before_response = client.get(
            f"/api/v1/administrators/{regular_admin_account['id']}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert before_response.status_code == 200
        before_data = before_response.json()

        patch_response = client.patch(
            f"/api/v1/administrators/{regular_admin_account['id']}",
            json={"is_active": False},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert patch_response.status_code == 200

        after_response = client.get(
            f"/api/v1/administrators/{regular_admin_account['id']}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert after_response.status_code == 200
        after_data = after_response.json()

        assert after_data["is_active"] is False
        assert after_data["first_name"] == before_data["first_name"]
        assert after_data["last_name"] == before_data["last_name"]
        # Some response schemas do not expose phone; verify it only when present.
        if "phone" in before_data and "phone" in after_data:
            assert after_data["phone"] == before_data["phone"]


class TestAdministratorDelete:
    """Test DELETE /administrators/{id} endpoint."""

    @pytest.fixture
    def deletable_admin(self, session):
        """Fixture que crea un admin limpio listo para ser eliminado."""
        from app.database.model import (
            NonCriticalPersonalData,
            SensitiveData,
            Administrator,
        )
        from app.domain.auth.security import get_password_hash

        non_critical = NonCriticalPersonalData(
            first_name="ToDelete",
            last_name="Admin",
            second_last_name="Test",
            phone="+523312345790",
            address="Delete St 123",
            city="Mexico City",
            state="Mexico",
            postal_code="06505",
            birth_date=datetime(1991, 7, 10),
        )
        session.add(non_critical)
        session.flush()

        sensitive = SensitiveData(
            non_critical_data_id=non_critical.id,
            email="todelete@test.com",
            password_hash=get_password_hash("DeletePass123!"),
            curp="DELT111111HDFRRL09",
            rfc="DELT111111AB0",
        )
        session.add(sensitive)
        session.flush()

        admin = Administrator(
            sensitive_data_id=sensitive.id,
            is_master=False,
        )
        session.add(admin)
        session.commit()

        return {
            "admin_id": admin.id,
            "sensitive_id": sensitive.id,
            "non_critical_id": non_critical.id,
        }

    def test_delete_administrator_returns_204(
        self, client: TestClient, master_admin_account: dict, deletable_admin: dict
    ):
        """Test que el endpoint retorna 204 al eliminar correctamente."""
        token = create_token(master_admin_account)
        response = client.delete(
            f"/api/v1/administrators/{deletable_admin['admin_id']}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 204

    def test_delete_administrator_is_gone_after_deletion(
        self, client: TestClient, master_admin_account: dict, deletable_admin: dict
    ):
        """Test que el admin ya no es recuperable tras ser eliminado."""
        token = create_token(master_admin_account)

        client.delete(
            f"/api/v1/administrators/{deletable_admin['admin_id']}",
            headers={"Authorization": f"Bearer {token}"},
        )

        get_response = client.get(
            f"/api/v1/administrators/{deletable_admin['admin_id']}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert get_response.status_code == 404

    def test_delete_administrator_cascades_related_records(
        self,
        client: TestClient,
        master_admin_account: dict,
        deletable_admin: dict,
        session,
    ):
        """Test que borrar un admin elimina también SensitiveData y NonCriticalPersonalData."""
        from app.database.model import (
            Administrator,
            NonCriticalPersonalData,
            SensitiveData,
        )

        token = create_token(master_admin_account)
        client.delete(
            f"/api/v1/administrators/{deletable_admin['admin_id']}",
            headers={"Authorization": f"Bearer {token}"},
        )

        session.expire_all()
        assert session.get(Administrator, deletable_admin["admin_id"]) is None
        assert session.get(SensitiveData, deletable_admin["sensitive_id"]) is None
        assert (
            session.get(NonCriticalPersonalData, deletable_admin["non_critical_id"])
            is None
        )

    def test_delete_administrator_not_found(
        self, client: TestClient, master_admin_account: dict
    ):
        """Test deleting non-existent administrator."""
        token = create_token(master_admin_account)
        response = client.delete(
            f"/api/v1/administrators/{uuid4()}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404

    def test_delete_administrator_as_regular_admin_forbidden(
        self,
        client: TestClient,
        master_admin_account: dict,
        regular_admin_account: dict,
    ):
        """Regular admin cannot delete administrators."""
        token = create_token(regular_admin_account)
        response = client.delete(
            f"/api/v1/administrators/{master_admin_account['id']}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403

    def test_delete_administrator_as_user_forbidden(
        self, client: TestClient, user_account: dict, regular_admin_account: dict
    ):
        """User cannot delete administrators."""
        token = create_token(user_account)
        response = client.delete(
            f"/api/v1/administrators/{regular_admin_account['id']}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403

    def test_master_admin_cannot_delete_self(
            self, client: TestClient, master_admin_account: dict
    ):
        """Master admin cannot delete its own account."""
        token = create_token(master_admin_account)
        response = client.delete(
            f"/api/v1/administrators/{master_admin_account['id']}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 400