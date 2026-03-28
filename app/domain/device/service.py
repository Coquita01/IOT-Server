from abc import ABC
from app.shared.base_domain.service import IBaseService
from app.database.model import Device
from typing import Annotated
from fastapi import Depends
from app.shared.base_domain.service import BaseService
from app.domain.device.repository import DeviceRepository
from app.database import SessionDep
from app.domain.device.schemas import DeviceCreate, DeviceUpdate


class IDeviceService(IBaseService[Device, DeviceCreate, DeviceUpdate]):
    pass


class DeviceService(BaseService[Device, DeviceCreate, DeviceUpdate], IDeviceService):
    entity_name = "Device"
    repository_class = DeviceRepository


def get_device_service(session: SessionDep) -> DeviceService:
    return DeviceService(session)


DeviceServiceDep = Annotated[DeviceService, Depends(get_device_service)]
