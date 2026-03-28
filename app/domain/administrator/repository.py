from abc import ABC
from app.shared.base_domain.repository import IBaseRepository, BaseRepository
from app.database.model import Administrator
from sqlmodel import Session


class IAdministratorRepository(IBaseRepository[Administrator], ABC):
    pass


class AdministratorRepository(BaseRepository[Administrator], IAdministratorRepository):
    model = Administrator

    def __init__(self, session: Session):
        super().__init__(session)
