from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class SessionData(BaseModel):
    user_id: str
    token_id: str
    refresh_token: str
    email: str
    account_type: str
    is_master: bool
    ip_address: str
    user_agent: str
    created_at: datetime
    last_activity: datetime


class SessionTokens(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserData(BaseModel):
    user_id: str
    email: str
    account_type: str
    is_master: bool
    token_id: Optional[str] = None


class EntitySessionData(BaseModel):
    session_id: str
    entity_id: str
    key_session: str
    ip_address: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    last_activity: datetime


class EntitySessionResponse(BaseModel):
    session_id: str
