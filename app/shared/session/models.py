from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class SessionData(BaseModel):
    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()}
    )
    
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
    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()}
    )
    
    session_id: str
    entity_id: str
    entity_type: str
    key_session: str
    ip_address: str
    user_agent: str
    created_at: datetime
    last_activity: datetime


class EntitySessionResponse(BaseModel):
    session_id: str
    encrypted_token: str
    key_session: str


class EntitySessionKeyResponse(BaseModel):
    key_session: str
