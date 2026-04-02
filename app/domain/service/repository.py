
from abc import ABC
from app.shared.base_domain.repository import IBaseRepository, BaseRepository
from app.database.model import Service
from sqlmodel import Session


class IServiceRepository(IBaseRepository[Service], ABC):
    pass


class ServiceRepository(BaseRepository[Service], IServiceRepository):
    model = Service

    def __init__(self, session: Session):
        super().__init__(session)
