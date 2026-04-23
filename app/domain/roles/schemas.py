from pydantic import BaseModel
from uuid import UUID
from app.shared.base_domain.schemas import BaseSchemaResponse


class RoleCreate(BaseModel):
    name: str
    description: str | None = None
    service_id: UUID


class RoleUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    is_active: bool | None = None


class RoleResponse(BaseSchemaResponse):
    name: str
    description: str | None = None
    service_id: UUID
    is_active: bool
