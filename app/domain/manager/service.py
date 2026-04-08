from abc import ABC
from typing import Annotated
from uuid import UUID

from fastapi import Depends

from app.shared.base_domain.service import IBaseService
from app.database.model import Manager, ManagerService
from app.database import SessionDep
from app.domain.manager.repository import ManagerRepository
from app.domain.personal_data.schemas import PersonalDataCreate, PersonalDataUpdate
from app.domain.personal_data.service import PersonalDataService
from app.shared.exceptions import AlreadyExistsException, NotFoundException


class IManagerService(
    IBaseService[Manager, PersonalDataCreate, PersonalDataUpdate], ABC
):
    pass


class ManagerService(PersonalDataService[Manager], IManagerService):
    entity_name = "Manager"
    repository_class = ManagerRepository

    def list_services(self, manager_id: UUID) -> list[ManagerService]:
        manager = self.get_by_id(manager_id)
        return manager.manager_services

    def assign_service(self, manager_id: UUID, service_id: UUID) -> ManagerService:
        self.get_by_id(manager_id)  # raises 404 if manager not found

        service = self.repository.get_service(service_id)
        if service is None:
            raise NotFoundException("Service", service_id)

        existing = self.repository.get_manager_service(manager_id, service_id)
        if existing is not None:
            raise AlreadyExistsException("ManagerService", "manager_id+service_id", f"{manager_id}+{service_id}")

        return self.repository.assign_service(manager_id, service_id)

    def unassign_service(self, manager_id: UUID, service_id: UUID) -> None:
        self.get_by_id(manager_id)  # raises 404 if manager not found

        link = self.repository.get_manager_service(manager_id, service_id)
        if link is None:
            raise NotFoundException("ManagerService", f"{manager_id}+{service_id}")

        self.repository.unassign_service(link)


def get_manager_service(session: SessionDep) -> ManagerService:
    return ManagerService(session)


ManagerServiceDep = Annotated[ManagerService, Depends(get_manager_service)]
