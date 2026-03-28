from pydantic import BaseModel
from app.shared.base_domain.schemas import BaseSchemaResponse


class DeviceCreate(BaseModel):
    name: str
    brand: str
    model: str
    serial_number: str
    ip: str
    mac: str


class DeviceUpdate(BaseModel):
    name: str | None
    brand: str | None
    model: str | None
    serial_number: str | None
    ip: str | None
    mac: str | None
    is_active: bool | None


class DeviceResponse(BaseSchemaResponse):
    name: str
    brand: str
    model: str
    serial_number: str
    ip: str
    mac: str
    is_active: bool
