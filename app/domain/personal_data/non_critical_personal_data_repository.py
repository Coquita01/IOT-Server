from abc import ABC
from app.shared.base_domain.repository import IBaseRepository, BaseRepository
from app.database.model import NonCriticalPersonalData
from sqlmodel import Session


class INonCriticalPersonalDataRepository(IBaseRepository[NonCriticalPersonalData], ABC):
    pass


class NonCriticalPersonalDataRepository(
    BaseRepository[NonCriticalPersonalData], INonCriticalPersonalDataRepository
):
    model = NonCriticalPersonalData

    def __init__(self, session: Session):
        super().__init__(session)
