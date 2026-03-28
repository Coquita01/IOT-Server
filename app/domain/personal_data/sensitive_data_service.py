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
    BaseService[SensitiveData, SensitiveDataCreate, SensitiveDataUpdate], ABC
):
    entity_name = "SensitiveData"
    repository_class = SensitiveDataRepository
