from abc import ABC
from typing import Annotated
from fastapi import Depends
from app.shared.base_domain.service import IBaseService
from app.database.model import Manager
from app.database import SessionDep
from app.domain.manager.repository import ManagerRepository
from app.domain.personal_data.schemas import PersonalDataCreate, PersonalDataUpdate
from app.domain.personal_data.service import PersonalDataService


class IManagerService(
    IBaseService[Manager, PersonalDataCreate, PersonalDataUpdate], ABC
):
    pass


class ManagerService(PersonalDataService, IManagerService):
    entity_name = "Manager"
    repository_class = ManagerRepository


def get_manager_service(session: SessionDep) -> ManagerService:
    return ManagerService(session)


ManagerServiceDep = Annotated[ManagerService, Depends(get_manager_service)]
