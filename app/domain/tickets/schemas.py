from uuid import UUID

from pydantic import BaseModel

from app.database.model import Priority
from app.shared.base_domain.schemas import BaseSchemaResponse


# ─────────────────────────────────────────────
# ServiceTicket schemas
# ─────────────────────────────────────────────

class ServiceTicketCreate(BaseModel):
    title: str
    description: str | None = None
    user_role_id: UUID
    status_id: int
    service_id: UUID
    priority: Priority = Priority.medium


class ServiceTicketUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status_id: int | None = None
    priority: Priority | None = None


class ServiceTicketResponse(BaseSchemaResponse):
    title: str
    description: str | None
    user_role_id: UUID
    status_id: int
    service_id: UUID
    priority: Priority


# ─────────────────────────────────────────────
# EcosystemTicket schemas
# ─────────────────────────────────────────────

class EcosystemTicketCreate(BaseModel):
    title: str
    description: str | None = None
    manager_service_id: UUID
    status_id: int
    priority: Priority = Priority.medium


class EcosystemTicketUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status_id: int | None = None
    priority: Priority | None = None


class EcosystemTicketResponse(BaseSchemaResponse):
    title: str
    description: str | None
    manager_service_id: UUID
    status_id: int
    priority: Priority
