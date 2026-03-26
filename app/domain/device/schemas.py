from typing import Optional
from uuid import UUID
from pydantic import BaseModel


class DeviceCreate(BaseModel):
    nombre: str


class DeviceUpdate(BaseModel):
    nombre: Optional[str] = None


class DeviceResponse(BaseModel):
    id: UUID
    nombre: str
