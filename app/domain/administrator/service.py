from abc import ABC
from typing import Annotated
from uuid import UUID
from fastapi import Depends
from app.shared.base_domain.service import IBaseService
from app.database.model import Administrator
from sqlmodel import Session
from app.database import get_session
from app.domain.administrator.repository import AdministratorRepository
from app.domain.auth.service import CurrentAccount
from app.domain.personal_data.schemas import PersonalDataCreate, PersonalDataUpdate
from app.domain.personal_data.service import PersonalDataService
from app.shared.exceptions import BadRequestException


class IAdministratorService(
    IBaseService[Administrator, PersonalDataCreate, PersonalDataUpdate], ABC
):
    pass


class AdministratorService(PersonalDataService[Administrator], IAdministratorService):
    entity_name = "Administrator"
    repository_class = AdministratorRepository

    def delete_administrator(self, target_id: UUID, current: CurrentAccount) -> None:
        if current.account_id == target_id:
            raise BadRequestException("You cannot delete your own account")

        self.delete_entity(target_id)


def get_administrator_service(session: Session = Depends(get_session)):
    return AdministratorService(session)


AdministratorServiceDep = Annotated[
    AdministratorService, Depends(get_administrator_service)
]
