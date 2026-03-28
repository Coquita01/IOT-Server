from datetime import datetime
from pydantic import BaseModel
from app.shared.base_domain.schemas import BaseSchemaResponse
from uuid import UUID


class NonCriticalPersonalDataCreate(BaseModel):
    first_name: str
    last_name: str
    second_last_name: str
    phone: str
    address: str
    city: str
    state: str
    postal_code: str
    birth_date: datetime


class NonCriticalPersonalDataUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    second_last_name: str | None = None
    phone: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    postal_code: str | None = None
    birth_date: datetime | None = None
    is_active: bool | None = None


class NonCriticalPersonalDataResponse(BaseSchemaResponse):
    first_name: str
    last_name: str
    second_last_name: str | None = None
    is_active: bool


class SensitiveDataCreate(BaseModel):
    non_critical_data_id: UUID | None = None
    email: str
    password_hash: str
    curp: str
    rfc: str


class SensitiveDataUpdate(BaseModel):
    non_critical_data_id: UUID | None = None
    email: str | None = None
    password_hash: str | None = None
    curp: str | None = None
    rfc: str | None = None


class PersonalDataCreate(NonCriticalPersonalDataCreate, SensitiveDataCreate):
    sensitive_data_id: UUID | None = None


class PersonalDataUpdate(NonCriticalPersonalDataUpdate, SensitiveDataUpdate):
    pass
