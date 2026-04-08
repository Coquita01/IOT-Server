from uuid import UUID
from app.shared.base_domain.schemas import BaseSchemaResponse
from app.domain.personal_data.schemas import NonCriticalPersonalDataResponse


class ServiceSummaryResponse(BaseSchemaResponse):
    name: str
    description: str | None = None
    is_active: bool


class ManagerResponse(NonCriticalPersonalDataResponse):
    services: list[ServiceSummaryResponse] = []


class ManagerServiceResponse(BaseSchemaResponse):
    manager_id: UUID
    service_id: UUID
    service: ServiceSummaryResponse
