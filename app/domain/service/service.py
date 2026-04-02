
from abc import ABC
from typing import Annotated
from fastapi import Depends
from app.shared.base_domain.service import IBaseService, BaseService
from app.database.model import Service
from app.database import SessionDep
from app.domain.service.repository import ServiceRepository
from app.domain.service.schemas import ServiceCreate, ServiceUpdate


class IServiceService(IBaseService[Service, ServiceCreate, ServiceUpdate], ABC):
    pass


class ServiceService(BaseService[Service, ServiceCreate, ServiceUpdate], IServiceService):
    entity_name = "Service"
    repository_class = ServiceRepository


def get_service_service(session: SessionDep) -> ServiceService:
    return ServiceService(session)


ServiceServiceDep = Annotated[ServiceService, Depends(get_service_service)]
