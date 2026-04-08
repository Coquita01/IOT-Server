from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field
from app.shared.base_domain.schemas import BaseSchemaResponse
from app.database.model import Priority


class TicketStatusResponse(BaseSchemaResponse):
    name: str
    description: str | None = None


class EcosystemTicketCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    manager_service_id: UUID
    status_id: int
    priority: Priority = Priority.medium


class EcosystemTicketUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    status_id: int | None = None
    priority: Priority | None = None


class EcosystemTicketResponse(BaseSchemaResponse):
    title: str
    description: str | None = None
    manager_service_id: UUID
    status_id: int
    priority: Priority
    status: TicketStatusResponse | None = None
