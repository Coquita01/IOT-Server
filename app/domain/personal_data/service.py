from typing import override, Generic, TypeVar
from uuid import UUID

from sqlmodel import Session

from app.shared.base_domain.service import BaseService
from app.domain.auth.security import get_password_hash
from app.domain.personal_data.non_critical_personal_data_service import (
    NonCriticalPersonalDataService,
)
from app.domain.personal_data.sensitive_data_service import SensitiveDataService
from app.domain.personal_data.schemas import PersonalDataCreate, PersonalDataUpdate
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

    def _hash_password_if_needed(
        self, payload: PersonalDataCreate | PersonalDataUpdate
    ) -> None:
        password_hash = getattr(payload, "password_hash", None)
        if password_hash and not str(password_hash).startswith("$2"):
            payload.password_hash = get_password_hash(password_hash)

    @override
    def create_entity(self, payload: PersonalDataCreate) -> T:
        self._hash_password_if_needed(payload)

        non_critical_personal_data = (
            self.non_critical_personal_data_service.create_entity(payload)
        )
        payload.non_critical_data_id = non_critical_personal_data.id

        sensitive_data = self.sensitive_data_service.create_entity(payload)
        payload.sensitive_data_id = sensitive_data.id

        return super().create_entity(payload)

    @override
    def update_entity(self, id: UUID, payload: PersonalDataUpdate) -> T:
        self._hash_password_if_needed(payload)


        entity = self.get_by_id(id)

        update_data = payload.model_dump(exclude_unset=True)

        allowed_direct_fields = {"is_master"}

        for field, value in update_data.items():
            if field in allowed_direct_fields and hasattr(entity, field):
                setattr(entity, field, value)

        self.repository.update(entity)
        return self.get_by_id(id)

    @override
    def delete_entity(self, id: UUID) -> bool:
        entity = self.get_by_id(id)

        sensitive_data_id = entity.sensitive_data_id
        non_critical_data_id = entity.sensitive_data.non_critical_data_id

        deleted = super().delete_entity(id)
        self.sensitive_data_service.delete_entity(sensitive_data_id)
        self.non_critical_personal_data_service.delete_entity(non_critical_data_id)

        return deleted