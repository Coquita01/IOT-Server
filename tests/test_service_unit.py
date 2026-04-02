"""Tests para la entidad Service — CRUD completo (unittest)."""

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


class ServiceTestBase(unittest.TestCase):
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


class TestCreateService(ServiceTestBase):

    def test_create_service_success(self):
        response = self.client.post(
            "/api/v1/services",
            json={
                "name": "Monitoreo de Temperatura",
                "description": "Sensores de temperatura",
                "administrator_id": self.admin_id,
            },
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["name"], "Monitoreo de Temperatura")
        self.assertEqual(data["description"], "Sensores de temperatura")
        self.assertEqual(data["administrator_id"], self.admin_id)
        self.assertTrue(data["is_active"])
        self.assertIn("id", data)
        self.assertIn("created_at", data)
        self.assertIn("updated_at", data)

    def test_create_service_without_description(self):
        response = self.client.post(
            "/api/v1/services",
            json={
                "name": "Servicio sin descripción",
                "administrator_id": self.admin_id,
            },
        )
        self.assertEqual(response.status_code, 201)
        self.assertIsNone(response.json()["description"])

    def test_create_service_without_name_fails(self):
        response = self.client.post(
            "/api/v1/services",
            json={
                "description": "Falta el name",
                "administrator_id": self.admin_id,
            },
        )
        self.assertEqual(response.status_code, 422)

    def test_create_service_without_administrator_fails(self):
        response = self.client.post(
            "/api/v1/services",
            json={"name": "Sin admin"},
        )
        self.assertEqual(response.status_code, 422)

    def test_create_service_duplicate_name_fails(self):
        self.client.post(
            "/api/v1/services",
            json={"name": "Duplicado", "administrator_id": self.admin_id},
        )
        with self.assertRaises(Exception):
            self.client.post(
                "/api/v1/services",
                json={"name": "Duplicado", "administrator_id": self.admin_id},
            )


class TestListServices(ServiceTestBase):

    def test_list_services_empty(self):
        response = self.client.get("/api/v1/services")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["total"], 0)
        self.assertEqual(data["data"], [])

    def test_list_services_with_data(self):
        self.client.post(
            "/api/v1/services",
            json={"name": "Servicio 1", "administrator_id": self.admin_id},
        )
        self.client.post(
            "/api/v1/services",
            json={"name": "Servicio 2", "administrator_id": self.admin_id},
        )
        response = self.client.get("/api/v1/services")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["total"], 2)
        self.assertEqual(len(data["data"]), 2)

    def test_list_services_pagination(self):
        for i in range(5):
            self.client.post(
                "/api/v1/services",
                json={"name": f"Servicio {i}", "administrator_id": self.admin_id},
            )
        response = self.client.get("/api/v1/services?offset=0&limit=2")
        data = response.json()
        self.assertEqual(data["total"], 5)
        self.assertEqual(len(data["data"]), 2)


class TestGetService(ServiceTestBase):

    def test_get_service_by_id(self):
        create_response = self.client.post(
            "/api/v1/services",
            json={"name": "Mi Servicio", "administrator_id": self.admin_id},
        )
        service_id = create_response.json()["id"]
        response = self.client.get(f"/api/v1/services/{service_id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["name"], "Mi Servicio")

    def test_get_service_not_found(self):
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = self.client.get(f"/api/v1/services/{fake_id}")
        self.assertEqual(response.status_code, 404)


class TestUpdateService(ServiceTestBase):

    def test_update_service_name(self):
        create_response = self.client.post(
            "/api/v1/services",
            json={"name": "Nombre Original", "administrator_id": self.admin_id},
        )
        service_id = create_response.json()["id"]
        response = self.client.patch(
            f"/api/v1/services/{service_id}",
            json={"name": "Nombre Actualizado"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["name"], "Nombre Actualizado")

    def test_update_service_description(self):
        create_response = self.client.post(
            "/api/v1/services",
            json={"name": "Servicio", "administrator_id": self.admin_id},
        )
        service_id = create_response.json()["id"]
        response = self.client.patch(
            f"/api/v1/services/{service_id}",
            json={"description": "Nueva descripción"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["description"], "Nueva descripción")

    def test_update_service_deactivate(self):
        create_response = self.client.post(
            "/api/v1/services",
            json={"name": "Servicio Activo", "administrator_id": self.admin_id},
        )
        service_id = create_response.json()["id"]
        response = self.client.patch(
            f"/api/v1/services/{service_id}",
            json={"is_active": False},
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["is_active"])

    def test_update_service_not_found(self):
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = self.client.patch(
            f"/api/v1/services/{fake_id}",
            json={"name": "No existe"},
        )
        self.assertEqual(response.status_code, 404)


class TestDeleteService(ServiceTestBase):

    def test_delete_service(self):
        create_response = self.client.post(
            "/api/v1/services",
            json={"name": "Para borrar", "administrator_id": self.admin_id},
        )
        service_id = create_response.json()["id"]
        response = self.client.delete(f"/api/v1/services/{service_id}")
        self.assertEqual(response.status_code, 204)

        get_response = self.client.get(f"/api/v1/services/{service_id}")
        self.assertEqual(get_response.status_code, 404)

    def test_delete_service_not_found(self):
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = self.client.delete(f"/api/v1/services/{fake_id}")
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
