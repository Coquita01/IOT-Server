from abc import ABC
from app.shared.base_domain.repository import IBaseRepository, BaseRepository
from app.database.model import Manager
from sqlmodel import Session


class IManagerRepository(IBaseRepository[Manager], ABC):
    pass


class ManagerRepository(BaseRepository[Manager], IManagerRepository):
    model = Manager

    def __init__(self, session: Session):
        super().__init__(session)
