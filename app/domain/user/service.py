from abc import ABC
from typing import Annotated
from fastapi import Depends
from app.shared.base_domain.service import IBaseService
from app.database.model import User
from app.database import SessionDep
from app.domain.user.repository import UserRepository
from app.domain.personal_data.schemas import PersonalDataCreate, PersonalDataUpdate
from app.domain.personal_data.service import PersonalDataService


class IUserService(
    IBaseService[User, PersonalDataCreate, PersonalDataUpdate], ABC
):
    pass


class UserService(PersonalDataService, IUserService):
    entity_name = "User"
    repository_class = UserRepository


def get_user_service(session: SessionDep) -> UserService:
    return UserService(session)


UserServiceDep = Annotated[UserService, Depends(get_user_service)]
