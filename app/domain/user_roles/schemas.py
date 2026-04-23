from pydantic import BaseModel
from uuid import UUID
from app.shared.base_domain.schemas import BaseSchemaResponse


class UserRoleCreate(BaseModel):
    user_id: UUID
    role_id: UUID


class UserRoleUpdate(BaseModel):
    pass  # UserRole assignments are immutable - no updates allowed


class UserRoleResponse(BaseSchemaResponse):
    user_id: UUID
    role_id: UUID
