import re
from ipaddress import ip_address
from uuid import UUID

from pydantic import BaseModel, field_validator

from app.shared.base_domain.schemas import BaseSchemaResponse


MAC_REGEX = re.compile(
    r"^([0-9A-Fa-f]{2}[:\-]){5}([0-9A-Fa-f]{2})$"
)


class DeviceCreate(BaseModel):
    name: str
    brand: str | None = None
    model: str | None = None
    serial_number: str | None = None
    ip: str | None = None
    mac: str | None = None

    @field_validator("ip")
    @classmethod
    def validate_ip(cls, value: str | None) -> str | None:
        if value is None:
            return value
        try:
            ip_address(value)
        except ValueError as e:
            raise ValueError("Invalid IP address format") from e
        return value

    @field_validator("mac")
    @classmethod
    def validate_mac(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if not MAC_REGEX.match(value):
            raise ValueError("Invalid MAC address format")
        return value.upper()


class DeviceUpdate(BaseModel):
    name: str | None = None
    brand: str | None = None
    model: str | None = None
    serial_number: str | None = None
    ip: str | None = None
    mac: str | None = None
    is_active: bool | None = None

    @field_validator("ip")
    @classmethod
    def validate_ip(cls, value: str | None) -> str | None:
        if value is None:
            return value
        try:
            ip_address(value)
        except ValueError as e:
            raise ValueError("Invalid IP address format") from e
        return value

    @field_validator("mac")
    @classmethod
    def validate_mac(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if not MAC_REGEX.match(value):
            raise ValueError("Invalid MAC address format")
        return value.upper()


class DeviceResponse(BaseSchemaResponse):
    name: str
    brand: str | None = None
    model: str | None = None
    serial_number: str | None = None
    ip: str | None = None
    mac: str | None = None
    is_active: bool


class PuzzlePayload(BaseModel):
    ciphertext: str
    iv: str


class PuzzleRequest(BaseModel):
    device_id: UUID
    encrypted_payload: PuzzlePayload