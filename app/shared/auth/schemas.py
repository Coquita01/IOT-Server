from pydantic import BaseModel
from uuid import UUID

class LoginRequest(BaseModel):
    entity: str  # user, admin, master, device
    identifier: str  # username, email, or device_id
    payload: dict

class LoginResponse(BaseModel):
    valid: bool
    access_token: str | None = None
    refresh_token: str | None = None
    token_type: str | None = None
    user_id: str | None = None
    device_id: str | None = None
    error: str | None = None
