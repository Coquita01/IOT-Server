from abc import ABC
from typing import Annotated
from fastapi import Depends
from app.shared.base_domain.service import IBaseService
from app.database.model import Administrator
from app.database import SessionDep
from app.domain.administrator.repository import AdministratorRepository
from app.domain.personal_data.schemas import PersonalDataCreate, PersonalDataUpdate
from app.domain.personal_data.service import PersonalDataService


class IAdministratorService(
    IBaseService[Administrator, PersonalDataCreate, PersonalDataUpdate], ABC
):
    pass


class AdministratorService(PersonalDataService, IAdministratorService):
    entity_name = "Administrator"
    repository_class = AdministratorRepository


def get_administrator_service(session: SessionDep) -> AdministratorService:
    return AdministratorService(session)


AdministratorServiceDep = Annotated[
    AdministratorService, Depends(get_administrator_service)
]
