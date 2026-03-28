from typing import override, Generic, TypeVar
from app.shared.base_domain.service import BaseService
from sqlmodel import Session
from app.domain.personal_data.non_critical_personal_data_service import (
    NonCriticalPersonalDataService,
)
from app.domain.personal_data.sensitive_data_service import SensitiveDataService
from app.domain.personal_data.schemas import PersonalDataCreate, PersonalDataUpdate
from uuid import UUID
from app.database.model import PersonalData

T = TypeVar("T", bound=PersonalData)


class PersonalDataService(
    BaseService[T, PersonalDataCreate, PersonalDataUpdate], Generic[T]
):
    def __init__(self, session: Session):
        super().__init__(session)
        self.non_critical_personal_data_service = NonCriticalPersonalDataService(
            session
        )
        self.sensitive_data_service = SensitiveDataService(session)

    @override
    def create_entity(self, payload: PersonalDataCreate) -> T:
        non_critical_personal_data = (
            self.non_critical_personal_data_service.create_entity(payload)
        )
        payload.non_critical_data_id = non_critical_personal_data.id
        sensitive_data = self.sensitive_data_service.create_entity(payload)
        payload.sensitive_data_id = sensitive_data.id
        return super().create_entity(payload)

    @override
    def update_entity(self, id: UUID, payload: PersonalDataUpdate) -> T:
        entity = super().update_entity(id, payload)
        sensitive_data = self.sensitive_data_service.update_entity(
            entity.sensitive_data_id, payload
        )
        self.non_critical_personal_data_service.update_entity(
            sensitive_data.non_critical_data_id, payload
        )
        return entity

    @override
    def delete_entity(self, id: UUID) -> bool:
        super().delete_entity(id)
        self.sensitive_data_service.delete_entity(id)
        return self.non_critical_personal_data_service.delete_entity(id)
