from abc import ABC
from app.shared.base_domain.repository import IBaseRepository, BaseRepository
from app.database.model import Application
from sqlmodel import Session


class IApplicationRepository(IBaseRepository[Application], ABC):
    pass


class ApplicationRepository(BaseRepository[Application], IApplicationRepository):
    model = Application

    def __init__(self, session: Session):
        super().__init__(session)