"""Tests para la entidad Application — CRUD + generación de api_key (unittest)."""

import unittest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.pool import StaticPool
from app.main import app as fastapi_app
from app.database import get_session
from app.database.model import (  # noqa: F401
    NonCriticalPersonalData, SensitiveData, PersonalData,
    Administrator, Manager, User, Service, Application,
    ApplicationService, Device, DeviceService, ManagerService,
    Role, RolePermission, UserRole, TicketStatus,
    ServiceTicket, EcosystemTicket,
)

test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


class ApplicationTestBase(unittest.TestCase):
    """Clase base con configuración compartida."""

    def setUp(self):
        SQLModel.metadata.create_all(test_engine)
        self.session = Session(test_engine)

        def get_session_override():
            return self.session

        fastapi_app.dependency_overrides[get_session] = get_session_override
        self.client = TestClient(fastapi_app)

        response = self.client.post(
            "/api/v1/administrators",
            json={
                "first_name": "Admin",
                "last_name": "Test",
                "second_last_name": "User",
                "phone": "1234567890",
                "address": "Calle Test 123",
                "city": "Tuxtla",
                "state": "Chiapas",
                "postal_code": "29000",
                "birth_date": "1990-01-01T00:00:00",
                "email": "admin@test.com",
                "password_hash": "test123",
                "curp": "ABCD900101HCSRRL01",
                "rfc": "ABCD900101ABC",
            },
        )
        self.assertEqual(response.status_code, 201)
        self.admin_id = response.json()["id"]

    def tearDown(self):
        fastapi_app.dependency_overrides.clear()
        self.session.close()
        SQLModel.metadata.drop_all(test_engine)


class TestCreateApplication(ApplicationTestBase):

    def test_create_application_success(self):
        response = self.client.post(
            "/api/v1/applications",
            json={
                "name": "Dashboard Web",
                "version": "1.0.0",
                "url": "https://dashboard.example.com",
                "port": 3000,
                "description": "Panel de monitoreo",
                "administrator_id": self.admin_id,
            },
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["name"], "Dashboard Web")
        self.assertEqual(data["version"], "1.0.0")
        self.assertEqual(data["url"], "https://dashboard.example.com")
        self.assertEqual(data["port"], 3000)
        self.assertEqual(data["description"], "Panel de monitoreo")
        self.assertEqual(data["administrator_id"], self.admin_id)
        self.assertTrue(data["is_active"])
        self.assertIn("id", data)
        self.assertIn("created_at", data)
        self.assertIn("updated_at", data)

    def test_create_application_generates_api_key(self):
        response = self.client.post(
            "/api/v1/applications",
            json={
                "name": "App con API Key",
                "administrator_id": self.admin_id,
            },
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertIn("api_key", data)
        self.assertEqual(len(data["api_key"]), 64)

    def test_create_application_unique_api_keys(self):
        response1 = self.client.post(
            "/api/v1/applications",
            json={"name": "App 1", "administrator_id": self.admin_id},
        )
        response2 = self.client.post(
            "/api/v1/applications",
            json={"name": "App 2", "administrator_id": self.admin_id},
        )
        key1 = response1.json()["api_key"]
        key2 = response2.json()["api_key"]
        self.assertNotEqual(key1, key2)

    def test_create_application_only_required_fields(self):
        response = self.client.post(
            "/api/v1/applications",
            json={
                "name": "App Mínima",
                "administrator_id": self.admin_id,
            },
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["name"], "App Mínima")
        self.assertIsNone(data["version"])
        self.assertIsNone(data["url"])
        self.assertIsNone(data["port"])
        self.assertIsNone(data["description"])

    def test_create_application_without_name_fails(self):
        response = self.client.post(
            "/api/v1/applications",
            json={"administrator_id": self.admin_id},
        )
        self.assertEqual(response.status_code, 422)

    def test_create_application_without_administrator_fails(self):
        response = self.client.post(
            "/api/v1/applications",
            json={"name": "Sin admin"},
        )
        self.assertEqual(response.status_code, 422)

    def test_create_application_duplicate_name_fails(self):
        self.client.post(
            "/api/v1/applications",
            json={"name": "Duplicada", "administrator_id": self.admin_id},
        )
        with self.assertRaises(Exception):
            self.client.post(
                "/api/v1/applications",
                json={"name": "Duplicada", "administrator_id": self.admin_id},
            )


class TestListApplications(ApplicationTestBase):

    def test_list_applications_empty(self):
        response = self.client.get("/api/v1/applications")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["total"], 0)
        self.assertEqual(data["data"], [])

    def test_list_applications_with_data(self):
        self.client.post(
            "/api/v1/applications",
            json={"name": "App 1", "administrator_id": self.admin_id},
        )
        self.client.post(
            "/api/v1/applications",
            json={"name": "App 2", "administrator_id": self.admin_id},
        )
        response = self.client.get("/api/v1/applications")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["total"], 2)
        self.assertEqual(len(data["data"]), 2)

    def test_list_applications_pagination(self):
        for i in range(5):
            self.client.post(
                "/api/v1/applications",
                json={"name": f"App {i}", "administrator_id": self.admin_id},
            )
        response = self.client.get("/api/v1/applications?offset=0&limit=2")
        data = response.json()
        self.assertEqual(data["total"], 5)
        self.assertEqual(len(data["data"]), 2)


class TestGetApplication(ApplicationTestBase):

    def test_get_application_by_id(self):
        create_response = self.client.post(
            "/api/v1/applications",
            json={"name": "Mi App", "administrator_id": self.admin_id},
        )
        app_id = create_response.json()["id"]
        response = self.client.get(f"/api/v1/applications/{app_id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["name"], "Mi App")

    def test_get_application_not_found(self):
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = self.client.get(f"/api/v1/applications/{fake_id}")
        self.assertEqual(response.status_code, 404)


class TestUpdateApplication(ApplicationTestBase):

    def test_update_application_name(self):
        create_response = self.client.post(
            "/api/v1/applications",
            json={"name": "Nombre Original", "administrator_id": self.admin_id},
        )
        app_id = create_response.json()["id"]
        response = self.client.patch(
            f"/api/v1/applications/{app_id}",
            json={"name": "Nombre Nuevo"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["name"], "Nombre Nuevo")

    def test_update_application_partial(self):
        create_response = self.client.post(
            "/api/v1/applications",
            json={
                "name": "App Completa",
                "version": "1.0",
                "url": "https://app.com",
                "port": 3000,
                "administrator_id": self.admin_id,
            },
        )
        app_id = create_response.json()["id"]
        response = self.client.patch(
            f"/api/v1/applications/{app_id}",
            json={"version": "2.0"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["version"], "2.0")
        self.assertEqual(data["name"], "App Completa")
        self.assertEqual(data["url"], "https://app.com")
        self.assertEqual(data["port"], 3000)

    def test_update_application_deactivate(self):
        create_response = self.client.post(
            "/api/v1/applications",
            json={"name": "App Activa", "administrator_id": self.admin_id},
        )
        app_id = create_response.json()["id"]
        response = self.client.patch(
            f"/api/v1/applications/{app_id}",
            json={"is_active": False},
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["is_active"])

    def test_update_application_not_found(self):
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = self.client.patch(
            f"/api/v1/applications/{fake_id}",
            json={"name": "No existe"},
        )
        self.assertEqual(response.status_code, 404)


class TestDeleteApplication(ApplicationTestBase):

    def test_delete_application(self):
        create_response = self.client.post(
            "/api/v1/applications",
            json={"name": "Para borrar", "administrator_id": self.admin_id},
        )
        app_id = create_response.json()["id"]
        response = self.client.delete(f"/api/v1/applications/{app_id}")
        self.assertEqual(response.status_code, 204)

        get_response = self.client.get(f"/api/v1/applications/{app_id}")
        self.assertEqual(get_response.status_code, 404)

    def test_delete_application_not_found(self):
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = self.client.delete(f"/api/v1/applications/{fake_id}")
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
