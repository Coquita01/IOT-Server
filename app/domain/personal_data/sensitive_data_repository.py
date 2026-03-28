from abc import ABC
from app.shared.base_domain.repository import IBaseRepository, BaseRepository
from app.database.model import SensitiveData
from sqlmodel import Session


class ISensitiveDataRepository(IBaseRepository[SensitiveData], ABC):
    pass


class SensitiveDataRepository(BaseRepository[SensitiveData], ISensitiveDataRepository):
    model = SensitiveData

    def __init__(self, session: Session):
        super().__init__(session)
