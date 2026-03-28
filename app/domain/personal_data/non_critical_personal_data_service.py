from abc import ABC
from app.shared.base_domain.service import IBaseService, BaseService
from app.database.model import NonCriticalPersonalData
from app.domain.personal_data.non_critical_personal_data_repository import (
    NonCriticalPersonalDataRepository,
)
from app.domain.personal_data.schemas import (
    NonCriticalPersonalDataCreate,
    NonCriticalPersonalDataUpdate,
)


class INonCriticalPersonalDataService(
    IBaseService[
        NonCriticalPersonalData,
        NonCriticalPersonalDataCreate,
        NonCriticalPersonalDataUpdate,
    ]
):
    pass


class NonCriticalPersonalDataService(
    BaseService[
        NonCriticalPersonalData,
        NonCriticalPersonalDataCreate,
        NonCriticalPersonalDataUpdate,
    ],
):
    entity_name = "NonCriticalPersonalData"
    repository_class = NonCriticalPersonalDataRepository
