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


def service_ticket_payload(**overrides) -> dict:
    """Return valid payload for creating a ServiceTicket."""
    data = {
        "title": "Service Ticket Test",
        "description": "A test service ticket",
        "user_role_id": str(uuid4()),
        "status_id": 1,
        "service_id": str(uuid4()),
        "priority": "medium",
    }
    data.update(overrides)
    return data


def ecosystem_ticket_payload(**overrides) -> dict:
    """Return valid payload for creating an EcosystemTicket."""
    data = {
        "title": "Ecosystem Ticket Test",
        "description": "A test ecosystem ticket",
        "manager_service_id": str(uuid4()),
        "status_id": 1,
        "priority": "low",
    }
    data.update(overrides)
    return data


# ─────────────────────────────────────────────────────────────────────────────
# ServiceTicket — CRUD tests
# Policies: read+write allowed for all roles; delete only master admin
# ─────────────────────────────────────────────────────────────────────────────

class TestServiceTicketList:
    """Test GET /tickets/service endpoint."""

    def test_list_service_tickets_as_master_admin(
        self, client: TestClient, master_admin_account: dict
    ):
        """Master admin can list service tickets."""
        token = create_token(master_admin_account)
        response = client.get(
            "/api/v1/tickets/service",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "data" in data
        assert isinstance(data["data"], list)

    def test_list_service_tickets_as_regular_admin(
        self, client: TestClient, regular_admin_account: dict
    ):
        """Regular admin can list service tickets."""
        token = create_token(regular_admin_account)
        response = client.get(
            "/api/v1/tickets/service",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "data" in data

    def test_list_service_tickets_as_manager(
        self, client: TestClient, manager_account: dict
    ):
        """Manager can list service tickets."""
        token = create_token(manager_account)
        response = client.get(
            "/api/v1/tickets/service",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "data" in data

    def test_list_service_tickets_as_user(
        self, client: TestClient, user_account: dict
    ):
        """Regular user can list service tickets."""
        token = create_token(user_account)
        response = client.get(
            "/api/v1/tickets/service",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "data" in data

    def test_list_service_tickets_without_token(self, client: TestClient):
        """Unauthenticated request returns 401."""
        response = client.get("/api/v1/tickets/service")
        assert response.status_code == 401

    def test_list_service_tickets_pagination(
        self, client: TestClient, master_admin_account: dict
    ):
        """Pagination parameters are respected."""
        token = create_token(master_admin_account)
        response = client.get(
            "/api/v1/tickets/service?offset=0&limit=5",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 5
        assert data["offset"] == 0


class TestServiceTicketRetrieve:
    """Test GET /tickets/service/{id} endpoint."""

    def test_retrieve_service_ticket_as_master_admin(
        self, client: TestClient, master_admin_account: dict
    ):
        """Master admin can retrieve a service ticket."""
        token = create_token(master_admin_account)

        create_response = client.post(
            "/api/v1/tickets/service",
            json=service_ticket_payload(title="Retrieve Test"),
            headers={"Authorization": f"Bearer {token}"},
        )
        assert create_response.status_code == 201
        ticket_id = create_response.json()["id"]

        response = client.get(
            f"/api/v1/tickets/service/{ticket_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Retrieve Test"
        assert data["priority"] == "medium"

    def test_retrieve_service_ticket_as_user(
        self, client: TestClient, user_account: dict, master_admin_account: dict
    ):
        """Regular user can retrieve a service ticket."""
        admin_token = create_token(master_admin_account)
        create_response = client.post(
            "/api/v1/tickets/service",
            json=service_ticket_payload(title="User Retrieve Test"),
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        ticket_id = create_response.json()["id"]

        user_token = create_token(user_account)
        response = client.get(
            f"/api/v1/tickets/service/{ticket_id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 200

    def test_retrieve_service_ticket_not_found(
        self, client: TestClient, master_admin_account: dict
    ):
        """Returns 404 for non-existent ticket."""
        token = create_token(master_admin_account)
        response = client.get(
            f"/api/v1/tickets/service/{uuid4()}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404

    def test_retrieve_service_ticket_invalid_uuid(
        self, client: TestClient, master_admin_account: dict
    ):
        """Returns 422 for invalid UUID in path."""
        token = create_token(master_admin_account)
        response = client.get(
            "/api/v1/tickets/service/not-a-uuid",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422


class TestServiceTicketCreate:
    """Test POST /tickets/service endpoint."""

    def test_create_service_ticket_as_master_admin(
        self, client: TestClient, master_admin_account: dict
    ):
        """Master admin can create a service ticket."""
        token = create_token(master_admin_account)
        response = client.post(
            "/api/v1/tickets/service",
            json=service_ticket_payload(title="Master Admin Ticket"),
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Master Admin Ticket"
        assert data["priority"] == "medium"
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_service_ticket_as_regular_admin(
        self, client: TestClient, regular_admin_account: dict
    ):
        """Regular admin can create a service ticket."""
        token = create_token(regular_admin_account)
        response = client.post(
            "/api/v1/tickets/service",
            json=service_ticket_payload(title="Admin Ticket"),
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 201

    def test_create_service_ticket_as_manager(
        self, client: TestClient, manager_account: dict
    ):
        """Manager can create a service ticket."""
        token = create_token(manager_account)
        response = client.post(
            "/api/v1/tickets/service",
            json=service_ticket_payload(title="Manager Ticket"),
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 201

    def test_create_service_ticket_as_user(
        self, client: TestClient, user_account: dict
    ):
        """Regular user can create a service ticket."""
        token = create_token(user_account)
        response = client.post(
            "/api/v1/tickets/service",
            json=service_ticket_payload(title="User Ticket"),
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 201

    def test_create_service_ticket_without_token(self, client: TestClient):
        """Unauthenticated request returns 401."""
        response = client.post(
            "/api/v1/tickets/service",
            json=service_ticket_payload(),
        )
        assert response.status_code == 401

    def test_create_service_ticket_missing_title(
        self, client: TestClient, master_admin_account: dict
    ):
        """Missing required title returns 422."""
        token = create_token(master_admin_account)
        payload = service_ticket_payload()
        payload.pop("title")
        response = client.post(
            "/api/v1/tickets/service",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    def test_create_service_ticket_missing_user_role_id(
        self, client: TestClient, master_admin_account: dict
    ):
        """Missing required user_role_id returns 422."""
        token = create_token(master_admin_account)
        payload = service_ticket_payload()
        payload.pop("user_role_id")
        response = client.post(
            "/api/v1/tickets/service",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    def test_create_service_ticket_with_default_priority(
        self, client: TestClient, master_admin_account: dict
    ):
        """Priority defaults to 'medium' when not specified."""
        token = create_token(master_admin_account)
        payload = service_ticket_payload()
        payload.pop("priority")
        response = client.post(
            "/api/v1/tickets/service",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 201
        assert response.json()["priority"] == "medium"

    def test_create_service_ticket_without_description(
        self, client: TestClient, master_admin_account: dict
    ):
        """Description is optional."""
        token = create_token(master_admin_account)
        payload = service_ticket_payload()
        payload.pop("description")
        response = client.post(
            "/api/v1/tickets/service",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 201
        assert response.json()["description"] is None

    def test_create_service_ticket_all_priorities(
        self, client: TestClient, master_admin_account: dict
    ):
        """All valid priority values are accepted."""
        token = create_token(master_admin_account)
        for priority in ["low", "medium", "high", "critical"]:
            response = client.post(
                "/api/v1/tickets/service",
                json=service_ticket_payload(title=f"Ticket {priority}", priority=priority),
                headers={"Authorization": f"Bearer {token}"},
            )
            assert response.status_code == 201
            assert response.json()["priority"] == priority

    def test_create_service_ticket_invalid_priority(
        self, client: TestClient, master_admin_account: dict
    ):
        """Invalid priority value returns 422."""
        token = create_token(master_admin_account)
        response = client.post(
            "/api/v1/tickets/service",
            json=service_ticket_payload(priority="urgent"),
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422


class TestServiceTicketUpdate:
    """Test PATCH /tickets/service/{id} endpoint."""

    def test_update_service_ticket_title_as_master_admin(
        self, client: TestClient, master_admin_account: dict
    ):
        """Master admin can update a service ticket title."""
        token = create_token(master_admin_account)

        create_response = client.post(
            "/api/v1/tickets/service",
            json=service_ticket_payload(title="Original Title"),
            headers={"Authorization": f"Bearer {token}"},
        )
        ticket_id = create_response.json()["id"]

        response = client.patch(
            f"/api/v1/tickets/service/{ticket_id}",
            json={"title": "Updated Title"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json()["title"] == "Updated Title"

    def test_update_service_ticket_priority_as_manager(
        self, client: TestClient, master_admin_account: dict, manager_account: dict
    ):
        """Manager can update a service ticket priority."""
        admin_token = create_token(master_admin_account)
        create_response = client.post(
            "/api/v1/tickets/service",
            json=service_ticket_payload(title="Manager Update Test"),
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        ticket_id = create_response.json()["id"]

        manager_token = create_token(manager_account)
        response = client.patch(
            f"/api/v1/tickets/service/{ticket_id}",
            json={"priority": "high"},
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert response.status_code == 200
        assert response.json()["priority"] == "high"

    def test_update_service_ticket_as_user(
        self, client: TestClient, master_admin_account: dict, user_account: dict
    ):
        """Regular user can update a service ticket."""
        admin_token = create_token(master_admin_account)
        create_response = client.post(
            "/api/v1/tickets/service",
            json=service_ticket_payload(title="User Update Test"),
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        ticket_id = create_response.json()["id"]

        user_token = create_token(user_account)
        response = client.patch(
            f"/api/v1/tickets/service/{ticket_id}",
            json={"description": "Updated by user"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 200
        assert response.json()["description"] == "Updated by user"

    def test_update_service_ticket_not_found(
        self, client: TestClient, master_admin_account: dict
    ):
        """Returns 404 for non-existent ticket."""
        token = create_token(master_admin_account)
        response = client.patch(
            f"/api/v1/tickets/service/{uuid4()}",
            json={"title": "Doesn't exist"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404

    def test_update_service_ticket_partial_fields_preserved(
        self, client: TestClient, master_admin_account: dict
    ):
        """Non-updated fields are preserved after partial update."""
        token = create_token(master_admin_account)
        create_response = client.post(
            "/api/v1/tickets/service",
            json=service_ticket_payload(title="Partial Test", priority="high"),
            headers={"Authorization": f"Bearer {token}"},
        )
        ticket_id = create_response.json()["id"]

        response = client.patch(
            f"/api/v1/tickets/service/{ticket_id}",
            json={"description": "New description"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Partial Test"
        assert data["priority"] == "high"
        assert data["description"] == "New description"


class TestServiceTicketDelete:
    """Test DELETE /tickets/service/{id} endpoint.

    Only master admin can delete service tickets.
    Regular admin, manager, and user are denied (403).
    """

    def test_delete_service_ticket_as_master_admin(
        self, client: TestClient, master_admin_account: dict
    ):
        """Master admin can delete a service ticket."""
        token = create_token(master_admin_account)

        create_response = client.post(
            "/api/v1/tickets/service",
            json=service_ticket_payload(title="To Delete"),
            headers={"Authorization": f"Bearer {token}"},
        )
        assert create_response.status_code == 201
        ticket_id = create_response.json()["id"]

        response = client.delete(
            f"/api/v1/tickets/service/{ticket_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 204

        get_response = client.get(
            f"/api/v1/tickets/service/{ticket_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert get_response.status_code == 404

    def test_delete_service_ticket_as_regular_admin_forbidden(
        self, client: TestClient, master_admin_account: dict, regular_admin_account: dict
    ):
        """Regular admin cannot delete service tickets."""
        admin_token = create_token(master_admin_account)
        create_response = client.post(
            "/api/v1/tickets/service",
            json=service_ticket_payload(title="Admin Cannot Delete"),
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        ticket_id = create_response.json()["id"]

        regular_token = create_token(regular_admin_account)
        response = client.delete(
            f"/api/v1/tickets/service/{ticket_id}",
            headers={"Authorization": f"Bearer {regular_token}"},
        )
        assert response.status_code == 403

    def test_delete_service_ticket_as_manager_forbidden(
        self, client: TestClient, master_admin_account: dict, manager_account: dict
    ):
        """Manager cannot delete service tickets."""
        admin_token = create_token(master_admin_account)
        create_response = client.post(
            "/api/v1/tickets/service",
            json=service_ticket_payload(title="Manager Cannot Delete"),
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        ticket_id = create_response.json()["id"]

        manager_token = create_token(manager_account)
        response = client.delete(
            f"/api/v1/tickets/service/{ticket_id}",
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert response.status_code == 403

    def test_delete_service_ticket_as_user_forbidden(
        self, client: TestClient, master_admin_account: dict, user_account: dict
    ):
        """Regular user cannot delete service tickets."""
        admin_token = create_token(master_admin_account)
        create_response = client.post(
            "/api/v1/tickets/service",
            json=service_ticket_payload(title="User Cannot Delete"),
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        ticket_id = create_response.json()["id"]

        user_token = create_token(user_account)
        response = client.delete(
            f"/api/v1/tickets/service/{ticket_id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 403

    def test_delete_service_ticket_not_found(
        self, client: TestClient, master_admin_account: dict
    ):
        """Returns 404 when deleting a non-existent ticket."""
        token = create_token(master_admin_account)
        response = client.delete(
            f"/api/v1/tickets/service/{uuid4()}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404


# ─────────────────────────────────────────────────────────────────────────────
# EcosystemTicket — CRUD tests
# Policies: only master admin has access; all other roles are denied (403)
# ─────────────────────────────────────────────────────────────────────────────

class TestEcosystemTicketList:
    """Test GET /tickets/ecosystem endpoint."""

    def test_list_ecosystem_tickets_as_master_admin(
        self, client: TestClient, master_admin_account: dict
    ):
        """Master admin can list ecosystem tickets."""
        token = create_token(master_admin_account)
        response = client.get(
            "/api/v1/tickets/ecosystem",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "data" in data
        assert isinstance(data["data"], list)

    def test_list_ecosystem_tickets_as_regular_admin_forbidden(
        self, client: TestClient, regular_admin_account: dict
    ):
        """Regular admin cannot list ecosystem tickets."""
        token = create_token(regular_admin_account)
        response = client.get(
            "/api/v1/tickets/ecosystem",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403

    def test_list_ecosystem_tickets_as_manager_forbidden(
        self, client: TestClient, manager_account: dict
    ):
        """Manager cannot list ecosystem tickets."""
        token = create_token(manager_account)
        response = client.get(
            "/api/v1/tickets/ecosystem",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403

    def test_list_ecosystem_tickets_as_user_forbidden(
        self, client: TestClient, user_account: dict
    ):
        """Regular user cannot list ecosystem tickets."""
        token = create_token(user_account)
        response = client.get(
            "/api/v1/tickets/ecosystem",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403

    def test_list_ecosystem_tickets_without_token(self, client: TestClient):
        """Unauthenticated request returns 401."""
        response = client.get("/api/v1/tickets/ecosystem")
        assert response.status_code == 401

    def test_list_ecosystem_tickets_pagination(
        self, client: TestClient, master_admin_account: dict
    ):
        """Pagination parameters are respected."""
        token = create_token(master_admin_account)
        response = client.get(
            "/api/v1/tickets/ecosystem?offset=0&limit=5",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 5
        assert data["offset"] == 0


class TestEcosystemTicketRetrieve:
    """Test GET /tickets/ecosystem/{id} endpoint."""

    def test_retrieve_ecosystem_ticket_as_master_admin(
        self, client: TestClient, master_admin_account: dict
    ):
        """Master admin can retrieve an ecosystem ticket."""
        token = create_token(master_admin_account)

        create_response = client.post(
            "/api/v1/tickets/ecosystem",
            json=ecosystem_ticket_payload(title="Eco Retrieve Test"),
            headers={"Authorization": f"Bearer {token}"},
        )
        assert create_response.status_code == 201
        ticket_id = create_response.json()["id"]

        response = client.get(
            f"/api/v1/tickets/ecosystem/{ticket_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Eco Retrieve Test"

    def test_retrieve_ecosystem_ticket_as_regular_admin_forbidden(
        self, client: TestClient, master_admin_account: dict, regular_admin_account: dict
    ):
        """Regular admin cannot retrieve ecosystem tickets."""
        admin_token = create_token(master_admin_account)
        create_response = client.post(
            "/api/v1/tickets/ecosystem",
            json=ecosystem_ticket_payload(title="Admin Cannot Retrieve"),
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        ticket_id = create_response.json()["id"]

        regular_token = create_token(regular_admin_account)
        response = client.get(
            f"/api/v1/tickets/ecosystem/{ticket_id}",
            headers={"Authorization": f"Bearer {regular_token}"},
        )
        assert response.status_code == 403

    def test_retrieve_ecosystem_ticket_not_found(
        self, client: TestClient, master_admin_account: dict
    ):
        """Returns 404 for non-existent ecosystem ticket."""
        token = create_token(master_admin_account)
        response = client.get(
            f"/api/v1/tickets/ecosystem/{uuid4()}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404

    def test_retrieve_ecosystem_ticket_invalid_uuid(
        self, client: TestClient, master_admin_account: dict
    ):
        """Returns 422 for invalid UUID in path."""
        token = create_token(master_admin_account)
        response = client.get(
            "/api/v1/tickets/ecosystem/not-a-uuid",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422


class TestEcosystemTicketCreate:
    """Test POST /tickets/ecosystem endpoint."""

    def test_create_ecosystem_ticket_as_master_admin(
        self, client: TestClient, master_admin_account: dict
    ):
        """Master admin can create an ecosystem ticket."""
        token = create_token(master_admin_account)
        response = client.post(
            "/api/v1/tickets/ecosystem",
            json=ecosystem_ticket_payload(title="Master Eco Ticket"),
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Master Eco Ticket"
        assert data["priority"] == "low"
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_ecosystem_ticket_as_regular_admin_forbidden(
        self, client: TestClient, regular_admin_account: dict
    ):
        """Regular admin cannot create ecosystem tickets."""
        token = create_token(regular_admin_account)
        response = client.post(
            "/api/v1/tickets/ecosystem",
            json=ecosystem_ticket_payload(),
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403

    def test_create_ecosystem_ticket_as_manager_forbidden(
        self, client: TestClient, manager_account: dict
    ):
        """Manager cannot create ecosystem tickets."""
        token = create_token(manager_account)
        response = client.post(
            "/api/v1/tickets/ecosystem",
            json=ecosystem_ticket_payload(),
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403

    def test_create_ecosystem_ticket_as_user_forbidden(
        self, client: TestClient, user_account: dict
    ):
        """Regular user cannot create ecosystem tickets."""
        token = create_token(user_account)
        response = client.post(
            "/api/v1/tickets/ecosystem",
            json=ecosystem_ticket_payload(),
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403

    def test_create_ecosystem_ticket_without_token(self, client: TestClient):
        """Unauthenticated request returns 401."""
        response = client.post(
            "/api/v1/tickets/ecosystem",
            json=ecosystem_ticket_payload(),
        )
        assert response.status_code == 401

    def test_create_ecosystem_ticket_missing_title(
        self, client: TestClient, master_admin_account: dict
    ):
        """Missing required title returns 422."""
        token = create_token(master_admin_account)
        payload = ecosystem_ticket_payload()
        payload.pop("title")
        response = client.post(
            "/api/v1/tickets/ecosystem",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    def test_create_ecosystem_ticket_missing_manager_service_id(
        self, client: TestClient, master_admin_account: dict
    ):
        """Missing required manager_service_id returns 422."""
        token = create_token(master_admin_account)
        payload = ecosystem_ticket_payload()
        payload.pop("manager_service_id")
        response = client.post(
            "/api/v1/tickets/ecosystem",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    def test_create_ecosystem_ticket_with_default_priority(
        self, client: TestClient, master_admin_account: dict
    ):
        """Priority defaults to 'medium' when not specified."""
        token = create_token(master_admin_account)
        payload = ecosystem_ticket_payload()
        payload.pop("priority")
        response = client.post(
            "/api/v1/tickets/ecosystem",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 201
        assert response.json()["priority"] == "medium"

    def test_create_ecosystem_ticket_without_description(
        self, client: TestClient, master_admin_account: dict
    ):
        """Description is optional."""
        token = create_token(master_admin_account)
        payload = ecosystem_ticket_payload()
        payload.pop("description")
        response = client.post(
            "/api/v1/tickets/ecosystem",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 201
        assert response.json()["description"] is None

    def test_create_ecosystem_ticket_all_priorities(
        self, client: TestClient, master_admin_account: dict
    ):
        """All valid priority values are accepted."""
        token = create_token(master_admin_account)
        for priority in ["low", "medium", "high", "critical"]:
            response = client.post(
                "/api/v1/tickets/ecosystem",
                json=ecosystem_ticket_payload(
                    title=f"Eco Ticket {priority}", priority=priority
                ),
                headers={"Authorization": f"Bearer {token}"},
            )
            assert response.status_code == 201
            assert response.json()["priority"] == priority

    def test_create_ecosystem_ticket_invalid_priority(
        self, client: TestClient, master_admin_account: dict
    ):
        """Invalid priority value returns 422."""
        token = create_token(master_admin_account)
        response = client.post(
            "/api/v1/tickets/ecosystem",
            json=ecosystem_ticket_payload(priority="urgent"),
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422


class TestEcosystemTicketUpdate:
    """Test PATCH /tickets/ecosystem/{id} endpoint."""

    def test_update_ecosystem_ticket_as_master_admin(
        self, client: TestClient, master_admin_account: dict
    ):
        """Master admin can update an ecosystem ticket."""
        token = create_token(master_admin_account)

        create_response = client.post(
            "/api/v1/tickets/ecosystem",
            json=ecosystem_ticket_payload(title="Original Eco Title"),
            headers={"Authorization": f"Bearer {token}"},
        )
        ticket_id = create_response.json()["id"]

        response = client.patch(
            f"/api/v1/tickets/ecosystem/{ticket_id}",
            json={"title": "Updated Eco Title"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json()["title"] == "Updated Eco Title"

    def test_update_ecosystem_ticket_as_regular_admin_forbidden(
        self, client: TestClient, master_admin_account: dict, regular_admin_account: dict
    ):
        """Regular admin cannot update ecosystem tickets."""
        admin_token = create_token(master_admin_account)
        create_response = client.post(
            "/api/v1/tickets/ecosystem",
            json=ecosystem_ticket_payload(title="Admin Cannot Update"),
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        ticket_id = create_response.json()["id"]

        regular_token = create_token(regular_admin_account)
        response = client.patch(
            f"/api/v1/tickets/ecosystem/{ticket_id}",
            json={"title": "Attempted Update"},
            headers={"Authorization": f"Bearer {regular_token}"},
        )
        assert response.status_code == 403

    def test_update_ecosystem_ticket_as_manager_forbidden(
        self, client: TestClient, master_admin_account: dict, manager_account: dict
    ):
        """Manager cannot update ecosystem tickets."""
        admin_token = create_token(master_admin_account)
        create_response = client.post(
            "/api/v1/tickets/ecosystem",
            json=ecosystem_ticket_payload(title="Manager Cannot Update"),
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        ticket_id = create_response.json()["id"]

        manager_token = create_token(manager_account)
        response = client.patch(
            f"/api/v1/tickets/ecosystem/{ticket_id}",
            json={"title": "Attempted Update"},
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert response.status_code == 403

    def test_update_ecosystem_ticket_not_found(
        self, client: TestClient, master_admin_account: dict
    ):
        """Returns 404 for non-existent ecosystem ticket."""
        token = create_token(master_admin_account)
        response = client.patch(
            f"/api/v1/tickets/ecosystem/{uuid4()}",
            json={"title": "Doesn't exist"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404

    def test_update_ecosystem_ticket_partial_fields_preserved(
        self, client: TestClient, master_admin_account: dict
    ):
        """Non-updated fields are preserved after partial update."""
        token = create_token(master_admin_account)
        create_response = client.post(
            "/api/v1/tickets/ecosystem",
            json=ecosystem_ticket_payload(title="Partial Eco Test", priority="critical"),
            headers={"Authorization": f"Bearer {token}"},
        )
        ticket_id = create_response.json()["id"]

        response = client.patch(
            f"/api/v1/tickets/ecosystem/{ticket_id}",
            json={"description": "Updated description"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Partial Eco Test"
        assert data["priority"] == "critical"
        assert data["description"] == "Updated description"


class TestEcosystemTicketDelete:
    """Test DELETE /tickets/ecosystem/{id} endpoint.

    Only master admin can delete ecosystem tickets.
    All other roles are denied (403).
    """

    def test_delete_ecosystem_ticket_as_master_admin(
        self, client: TestClient, master_admin_account: dict
    ):
        """Master admin can delete an ecosystem ticket."""
        token = create_token(master_admin_account)

        create_response = client.post(
            "/api/v1/tickets/ecosystem",
            json=ecosystem_ticket_payload(title="To Delete Eco"),
            headers={"Authorization": f"Bearer {token}"},
        )
        assert create_response.status_code == 201
        ticket_id = create_response.json()["id"]

        response = client.delete(
            f"/api/v1/tickets/ecosystem/{ticket_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 204

        get_response = client.get(
            f"/api/v1/tickets/ecosystem/{ticket_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert get_response.status_code == 404

    def test_delete_ecosystem_ticket_as_regular_admin_forbidden(
        self, client: TestClient, master_admin_account: dict, regular_admin_account: dict
    ):
        """Regular admin cannot delete ecosystem tickets."""
        admin_token = create_token(master_admin_account)
        create_response = client.post(
            "/api/v1/tickets/ecosystem",
            json=ecosystem_ticket_payload(title="Admin Cannot Delete Eco"),
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        ticket_id = create_response.json()["id"]

        regular_token = create_token(regular_admin_account)
        response = client.delete(
            f"/api/v1/tickets/ecosystem/{ticket_id}",
            headers={"Authorization": f"Bearer {regular_token}"},
        )
        assert response.status_code == 403

    def test_delete_ecosystem_ticket_as_manager_forbidden(
        self, client: TestClient, master_admin_account: dict, manager_account: dict
    ):
        """Manager cannot delete ecosystem tickets."""
        admin_token = create_token(master_admin_account)
        create_response = client.post(
            "/api/v1/tickets/ecosystem",
            json=ecosystem_ticket_payload(title="Manager Cannot Delete Eco"),
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        ticket_id = create_response.json()["id"]

        manager_token = create_token(manager_account)
        response = client.delete(
            f"/api/v1/tickets/ecosystem/{ticket_id}",
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert response.status_code == 403

    def test_delete_ecosystem_ticket_as_user_forbidden(
        self, client: TestClient, master_admin_account: dict, user_account: dict
    ):
        """Regular user cannot delete ecosystem tickets."""
        admin_token = create_token(master_admin_account)
        create_response = client.post(
            "/api/v1/tickets/ecosystem",
            json=ecosystem_ticket_payload(title="User Cannot Delete Eco"),
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        ticket_id = create_response.json()["id"]

        user_token = create_token(user_account)
        response = client.delete(
            f"/api/v1/tickets/ecosystem/{ticket_id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 403

    def test_delete_ecosystem_ticket_not_found(
        self, client: TestClient, master_admin_account: dict
    ):
        """Returns 404 when deleting a non-existent ecosystem ticket."""
        token = create_token(master_admin_account)
        response = client.delete(
            f"/api/v1/tickets/ecosystem/{uuid4()}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404
