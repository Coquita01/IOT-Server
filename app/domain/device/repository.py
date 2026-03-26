from abc import ABC
from app.shared.base_domain.repository import IBaseRepository
from app.database.model import Dispositivo
from sqlmodel import Session
from app.shared.base_domain.repository import BaseRepository


class IDeviceRepository(IBaseRepository[Dispositivo], ABC):
    pass


class DeviceRepository(BaseRepository[Dispositivo], IDeviceRepository):
    model = Dispositivo

    def __init__(self, session: Session):
        super().__init__(session)
