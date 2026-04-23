from datetime import date, datetime, time, timedelta, timezone
from uuid import uuid4

import jwt
from fastapi.testclient import TestClient

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


def years_ago_iso(years: int) -> str:
    today = date.today()
    try:
        target = today.replace(year=today.year - years)
    except ValueError:
        # Handle leap day
        target = today.replace(year=today.year - years, day=28)

    return datetime.combine(target, time.min).isoformat()


def build_valid_user_payload(
    *,
    email: str = "new_user@test.com",
    curp: str = "TESA900615HDFLRNA8",
    rfc: str = "TESA900615AB1",
) -> dict:
    return {
        "first_name": "Test",
        "last_name": "User",
        "second_last_name": "Name",
        "phone": "+523312345800",
        "address": "123 Test St",
        "city": "Mexico City",
        "state": "Mexico",
        "postal_code": "06500",
        "birth_date": datetime(1990, 6, 15).isoformat(),
        "email": email,
        "password": "TestPass123!",
        "curp": curp,
        "rfc": rfc,
    }


class TestUserList:
    """Test GET /users endpoint."""

    def test_list_users_as_admin(
        self, client: TestClient, master_admin_account: dict
    ):
        """Test listing users as admin."""
        token = create_token(master_admin_account)
        response = client.get(
            "/api/v1/users",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "data" in data
        assert isinstance(data["data"], list)

    def test_list_users_as_manager(
        self, client: TestClient, manager_account: dict
    ):
        """Test listing users as manager."""
        token = create_token(manager_account)
        response = client.get(
            "/api/v1/users",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "data" in data

    def test_list_users_as_user_forbidden(self, client: TestClient, user_account: dict):
        """Test listing users as user is forbidden."""
        token = create_token(user_account)
        response = client.get(
            "/api/v1/users",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403

    def test_list_users_without_token(self, client: TestClient):
        """Test listing users without authentication."""
        response = client.get("/api/v1/users")
        assert response.status_code == 401

    def test_list_users_pagination(
        self, client: TestClient, master_admin_account: dict
    ):
        """Test listing users with pagination parameters."""
        token = create_token(master_admin_account)
        response = client.get(
            "/api/v1/users?offset=0&limit=10",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 10
        assert data["offset"] == 0

    def test_list_users_items_do_not_expose_sensitive_fields(
        self, client: TestClient, master_admin_account: dict
    ):
        """Test list endpoint does not expose sensitive fields in items."""
        token = create_token(master_admin_account)
        response = client.get(
            "/api/v1/users",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

        items = response.json().get("data", [])
        sensitive_fields = {"password_hash", "curp", "rfc"}
        for item in items:
            assert sensitive_fields.isdisjoint(item.keys())


class TestUserRetrieve:
    """Test GET /users/{id} endpoint."""

    def test_retrieve_user_as_admin(
        self, client: TestClient, master_admin_account: dict, user_account: dict
    ):
        """Test retrieving a user as admin."""
        token = create_token(master_admin_account)
        response = client.get(
            f"/api/v1/users/{user_account['id']}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "John"
        assert data["is_active"] is True

    def test_retrieve_user_as_manager(
        self, client: TestClient, manager_account: dict, user_account: dict
    ):
        """Test retrieving a user as manager."""
        token = create_token(manager_account)
        response = client.get(
            f"/api/v1/users/{user_account['id']}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    def test_retrieve_user_not_found(
        self, client: TestClient, master_admin_account: dict
    ):
        """Test retrieving a non-existent user."""
        token = create_token(master_admin_account)
        fake_id = uuid4()
        response = client.get(
            f"/api/v1/users/{fake_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404

    def test_retrieve_user_invalid_uuid(
        self, client: TestClient, master_admin_account: dict
    ):
        """Test retrieving user with invalid UUID."""
        token = create_token(master_admin_account)
        response = client.get(
            "/api/v1/users/not-a-uuid",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    def test_retrieve_user_as_user_forbidden(
        self, client: TestClient, user_account: dict
    ):
        """Test retrieving user as user is forbidden."""
        token = create_token(user_account)
        response = client.get(
            f"/api/v1/users/{user_account['id']}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403

    def test_retrieve_user_response_does_not_expose_sensitive_fields(
        self, client: TestClient, master_admin_account: dict, user_account: dict
    ):
        """Test retrieve endpoint does not expose sensitive fields."""
        token = create_token(master_admin_account)
        response = client.get(
            f"/api/v1/users/{user_account['id']}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

        data = response.json()
        sensitive_fields = {"password_hash", "curp", "rfc"}
        assert sensitive_fields.isdisjoint(data.keys())


class TestUserCreate:
    """Test POST /users endpoint."""

    def test_create_user_as_admin(
        self, client: TestClient, master_admin_account: dict
    ):
        """Test creating a new user as admin."""
        token = create_token(master_admin_account)
        user_data = build_valid_user_payload()

        response = client.post(
            "/api/v1/users",
            json=user_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["first_name"] == "Test"
        assert data["is_active"] is True

    def test_create_user_duplicate_email(
        self, client: TestClient, master_admin_account: dict, user_account: dict
    ):
        """Test creating user with duplicate email."""
        token = create_token(master_admin_account)
        user_data = build_valid_user_payload(
            email=user_account["email"],
            curp="DEUA900615HDFLRNA2",
            rfc="DEUA900615AB1",
        )

        response = client.post(
            "/api/v1/users",
            json=user_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 500

    def test_create_user_missing_required_field(
        self, client: TestClient, master_admin_account: dict
    ):
        """Test creating user with missing required field."""
        token = create_token(master_admin_account)
        user_data = build_valid_user_payload(
            email="missing_required@test.com",
            curp="MEIA900615HDFLRNA8",
            rfc="MEIA900615AB1",
        )
        user_data.pop("last_name")

        response = client.post(
            "/api/v1/users",
            json=user_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    def test_create_user_invalid_phone(
        self, client: TestClient, master_admin_account: dict
    ):
        """Test creating user with invalid phone format."""
        token = create_token(master_admin_account)
        user_data = build_valid_user_payload(
            email="user_phone@test.com",
            curp="PEUA900615HDFLRNA8",
            rfc="PEUA900615AB1",
        )
        user_data["phone"] = "XYZ"

        response = client.post(
            "/api/v1/users",
            json=user_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    def test_create_user_invalid_postal_code(
        self, client: TestClient, master_admin_account: dict
    ):
        """Test creating user with invalid postal code length."""
        token = create_token(master_admin_account)
        user_data = build_valid_user_payload(
            email="user_postal@test.com",
            curp="CEUA900615HDFLRNA0",
            rfc="CEUA900615AB1",
        )
        user_data["postal_code"] = "12"

        response = client.post(
            "/api/v1/users",
            json=user_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    def test_create_user_postal_code_out_of_range(
        self, client: TestClient, master_admin_account: dict
    ):
        """Test creating user with postal code outside Mexico valid range."""
        token = create_token(master_admin_account)
        user_data = build_valid_user_payload(
            email="user_postal_range@test.com",
            curp="FEUA900615HDFLRNA6",
            rfc="FEUA900615AB1",
        )
        user_data["postal_code"] = "00000"

        response = client.post(
            "/api/v1/users",
            json=user_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    def test_create_user_invalid_curp(
        self, client: TestClient, master_admin_account: dict
    ):
        """Test creating user with invalid CURP format."""
        token = create_token(master_admin_account)
        user_data = build_valid_user_payload(
            email="user_curp@test.com",
            curp="AEDA900615HDFLRNA4",
            rfc="AEDA900615AB1",
        )
        user_data["curp"] = "SHORT"

        response = client.post(
            "/api/v1/users",
            json=user_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    def test_create_user_invalid_curp_check_digit(
        self, client: TestClient, master_admin_account: dict
    ):
        """Test creating user with invalid CURP check digit."""
        token = create_token(master_admin_account)
        user_data = build_valid_user_payload(
            email="user_curp_digit@test.com",
            curp="REGA920520HDFLRNA2",
            rfc="REGA920520AB1",
        )
        user_data["curp"] = "REGA920520HDFLRNA9"

        response = client.post(
            "/api/v1/users",
            json=user_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    def test_create_user_invalid_rfc(
        self, client: TestClient, master_admin_account: dict
    ):
        """Test creating user with invalid RFC."""
        token = create_token(master_admin_account)
        user_data = build_valid_user_payload(
            email="user_rfc@test.com",
            curp="JOHA950310HDFLRNA4",
            rfc="JOHA950310AB1",
        )
        user_data["rfc"] = "X"

        response = client.post(
            "/api/v1/users",
            json=user_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    def test_create_user_rejects_weak_password(
        self, client: TestClient, master_admin_account: dict
    ):
        """Test creating user with weak password."""
        token = create_token(master_admin_account)
        user_data = build_valid_user_payload(
            email="weak_password@test.com",
            curp="JEMA930825MDFLRNA7",
            rfc="JEMA930825AB1",
        )
        user_data["password"] = "12345678"

        response = client.post(
            "/api/v1/users",
            json=user_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    def test_create_user_future_birth_date(
        self, client: TestClient, master_admin_account: dict
    ):
        """Test creating user with future birth date."""
        token = create_token(master_admin_account)
        user_data = build_valid_user_payload(
            email="user_birth@test.com",
            curp="INUA941205HDFLRNA9",
            rfc="INUA941205AB1",
        )
        user_data["birth_date"] = (datetime.now() + timedelta(days=1)).isoformat()

        response = client.post(
            "/api/v1/users",
            json=user_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    def test_create_user_underage_birth_date(
        self, client: TestClient, master_admin_account: dict
    ):
        """Test creating user under 18 years old."""
        token = create_token(master_admin_account)
        user_data = build_valid_user_payload(
            email="underage@test.com",
            curp="TESA900615HDFLRNA8",
            rfc="TESA900615AB1",
        )
        user_data["birth_date"] = years_ago_iso(17)

        response = client.post(
            "/api/v1/users",
            json=user_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    def test_create_user_as_user_forbidden(
        self, client: TestClient, user_account: dict
    ):
        """Test creating user as user is forbidden."""
        token = create_token(user_account)
        user_data = build_valid_user_payload(
            email="test@example.com",
            curp="DEUA900615HDFLRNA2",
            rfc="DEUA900615AB1",
        )

        response = client.post(
            "/api/v1/users",
            json=user_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403


class TestUserUpdate:
    """Test PATCH /users/{id} endpoint."""

    def test_update_user_full(
        self, client: TestClient, master_admin_account: dict, user_account: dict
    ):
        """Test updating user with all fields."""
        token = create_token(master_admin_account)
        update_data = {
            "first_name": "UpdatedJohn",
            "last_name": "UpdatedDoe",
            "phone": "+523312345850",
        }
        response = client.patch(
            f"/api/v1/users/{user_account['id']}",
            json=update_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "UpdatedJohn"

    def test_update_user_partial(
        self, client: TestClient, master_admin_account: dict, user_account: dict
    ):
        """Test updating user with partial fields."""
        token = create_token(master_admin_account)
        update_data = {"first_name": "PartialJohn"}
        response = client.patch(
            f"/api/v1/users/{user_account['id']}",
            json=update_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "PartialJohn"

    def test_update_user_not_found(
        self, client: TestClient, master_admin_account: dict
    ):
        """Test updating non-existent user."""
        token = create_token(master_admin_account)
        fake_id = uuid4()
        response = client.patch(
            f"/api/v1/users/{fake_id}",
            json={"first_name": "Updated"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404

    def test_update_user_invalid_email(
        self, client: TestClient, master_admin_account: dict, user_account: dict
    ):
        """Test updating user with invalid email."""
        token = create_token(master_admin_account)
        update_data = {"email": "@invalid"}
        response = client.patch(
            f"/api/v1/users/{user_account['id']}",
            json=update_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    def test_update_user_rejects_weak_password(
        self, client: TestClient, master_admin_account: dict, user_account: dict
    ):
        """Test updating user with weak password."""
        token = create_token(master_admin_account)
        response = client.patch(
            f"/api/v1/users/{user_account['id']}",
            json={"password": "12345678"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    def test_update_user_rejects_invalid_curp_check_digit(
        self, client: TestClient, master_admin_account: dict, user_account: dict
    ):
        """Test updating user with invalid CURP check digit."""
        token = create_token(master_admin_account)
        response = client.patch(
            f"/api/v1/users/{user_account['id']}",
            json={"curp": "REGA920520HDFLRNA9"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    def test_update_user_rejects_invalid_rfc_format(
        self, client: TestClient, master_admin_account: dict, user_account: dict
    ):
        """Test updating user with invalid RFC."""
        token = create_token(master_admin_account)
        response = client.patch(
            f"/api/v1/users/{user_account['id']}",
            json={"rfc": "RFC-INVALID"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    def test_update_user_rejects_postal_code_out_of_range(
        self, client: TestClient, master_admin_account: dict, user_account: dict
    ):
        """Test updating user with postal code out of range."""
        token = create_token(master_admin_account)
        response = client.patch(
            f"/api/v1/users/{user_account['id']}",
            json={"postal_code": "00000"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    def test_update_user_rejects_underage_birth_date(
        self, client: TestClient, master_admin_account: dict, user_account: dict
    ):
        """Test updating user with underage birth date."""
        token = create_token(master_admin_account)
        response = client.patch(
            f"/api/v1/users/{user_account['id']}",
            json={"birth_date": years_ago_iso(17)},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    def test_update_user_deactivate(
        self, client: TestClient, master_admin_account: dict, user_account: dict
    ):
        """Test deactivating a user."""
        token = create_token(master_admin_account)
        update_data = {"is_active": False}
        response = client.patch(
            f"/api/v1/users/{user_account['id']}",
            json=update_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False

        client.patch(
            f"/api/v1/users/{user_account['id']}",
            json={"is_active": True},
            headers={"Authorization": f"Bearer {token}"},
        )

    def test_update_user_partial_is_atomic_for_first_name(
        self, client: TestClient, master_admin_account: dict, user_account: dict
    ):
        """Test first_name patch updates only that field and keeps others intact."""
        token = create_token(master_admin_account)

        before_response = client.get(
            f"/api/v1/users/{user_account['id']}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert before_response.status_code == 200
        before_data = before_response.json()

        patch_response = client.patch(
            f"/api/v1/users/{user_account['id']}",
            json={"first_name": "AtomicUserName"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert patch_response.status_code == 200

        after_response = client.get(
            f"/api/v1/users/{user_account['id']}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert after_response.status_code == 200
        after_data = after_response.json()

        assert after_data["first_name"] == "AtomicUserName"
        assert after_data["last_name"] == before_data["last_name"]
        if "phone" in before_data and "phone" in after_data:
            assert after_data["phone"] == before_data["phone"]

    def test_update_user_partial_is_atomic_for_is_active(
        self, client: TestClient, master_admin_account: dict, user_account: dict
    ):
        """Test is_active patch updates only status and keeps identity fields intact."""
        token = create_token(master_admin_account)

        before_response = client.get(
            f"/api/v1/users/{user_account['id']}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert before_response.status_code == 200
        before_data = before_response.json()

        patch_response = client.patch(
            f"/api/v1/users/{user_account['id']}",
            json={"is_active": False},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert patch_response.status_code == 200

        after_response = client.get(
            f"/api/v1/users/{user_account['id']}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert after_response.status_code == 200
        after_data = after_response.json()

        assert after_data["is_active"] is False
        assert after_data["first_name"] == before_data["first_name"]
        assert after_data["last_name"] == before_data["last_name"]
        if "phone" in before_data and "phone" in after_data:
            assert after_data["phone"] == before_data["phone"]


class TestUserDelete:
    """Test DELETE /users/{id} endpoint."""

    def test_delete_user_as_admin(
        self, client: TestClient, master_admin_account: dict, session
    ):
        """Test deleting a user as admin."""
        from app.database.model import NonCriticalPersonalData, SensitiveData, User
        from app.domain.auth.security import get_password_hash

        non_critical_data = NonCriticalPersonalData(
            first_name="ToDelete",
            last_name="User",
            second_last_name="Test",
            phone="+523312345860",
            address="Delete St",
            city="Mexico City",
            state="Mexico",
            postal_code="06506",
            birth_date=datetime(1996, 9, 15),
            is_active=True,
        )
        session.add(non_critical_data)
        session.flush()

        sensitive_data = SensitiveData(
            non_critical_data_id=non_critical_data.id,
            email="deluser@test.com",
            password_hash=get_password_hash("DeletePass123!"),
            curp="DELU111111HDFRRL09",
            rfc="DELU111111AB0",
        )
        session.add(sensitive_data)
        session.flush()

        user_to_delete = User(
            sensitive_data_id=sensitive_data.id,
            is_active=True,
        )
        session.add(user_to_delete)
        session.commit()

        token = create_token(master_admin_account)
        response = client.delete(
            f"/api/v1/users/{user_to_delete.id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 204

    def test_delete_user_not_found(
        self, client: TestClient, master_admin_account: dict
    ):
        """Test deleting non-existent user."""
        token = create_token(master_admin_account)
        fake_id = uuid4()
        response = client.delete(
            f"/api/v1/users/{fake_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404

    def test_delete_user_as_manager_forbidden(
        self, client: TestClient, manager_account: dict, user_account: dict
    ):
        """Test deleting user as manager is forbidden."""
        token = create_token(manager_account)
        response = client.delete(
            f"/api/v1/users/{user_account['id']}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403

    def test_delete_user_as_user_forbidden(
        self, client: TestClient, user_account: dict
    ):
        """Test deleting user as user is forbidden."""
        token = create_token(user_account)
        response = client.delete(
            f"/api/v1/users/{user_account['id']}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403