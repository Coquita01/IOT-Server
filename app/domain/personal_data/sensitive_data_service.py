from typing import override
from uuid import UUID

from abc import ABC
from app.shared.base_domain.service import IBaseService, BaseService
from app.database.model import SensitiveData
from app.domain.personal_data.sensitive_data_repository import SensitiveDataRepository
from app.domain.personal_data.schemas import SensitiveDataCreate, SensitiveDataUpdate


class ISensitiveDataService(
    IBaseService[SensitiveData, SensitiveDataCreate, SensitiveDataUpdate]
):
    pass


class SensitiveDataService(
    BaseService[SensitiveData, SensitiveDataCreate, SensitiveDataUpdate]
):
    entity_name = "SensitiveData"
    repository_class = SensitiveDataRepository

    def _sensitive_fields(self, payload: SensitiveDataCreate | SensitiveDataUpdate) -> dict:
        data = payload.model_dump(exclude_none=True, exclude={"password"})
        return {
            key: value
            for key, value in data.items()
            if key in {"non_critical_data_id", "email", "curp", "rfc"}
        }

    @override
    def create_entity(self, payload: SensitiveDataCreate) -> SensitiveData:
        entity = SensitiveData(**self._sensitive_fields(payload))
        entity.password = payload.password
        return self.repository.create(entity)

    @override
    def update_entity(self, id: UUID, payload: SensitiveDataUpdate) -> SensitiveData:
        entity = self.get_by_id(id)

        for field_name, value in self._sensitive_fields(payload).items():
            setattr(entity, field_name, value)

        if payload.password is not None:
            entity.password = payload.password

        return self.repository.update(entity)
