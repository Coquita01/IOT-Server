from abc import ABC
from app.shared.base_domain.service import IBaseService
from app.database.model import UserRole
from typing import Annotated
from fastapi import Depends
from app.shared.base_domain.service import BaseService
from app.domain.user_roles.repository import UserRoleRepository
from app.database import SessionDep
from app.domain.user_roles.schemas import UserRoleCreate, UserRoleUpdate


class IUserRoleService(IBaseService[UserRole, UserRoleCreate, UserRoleUpdate]):
    pass


class UserRoleService(BaseService[UserRole, UserRoleCreate, UserRoleUpdate], IUserRoleService):
    entity_name = "UserRole"
    repository_class = UserRoleRepository


def get_user_role_service(session: SessionDep) -> UserRoleService:
    return UserRoleService(session)


UserRoleServiceDep = Annotated[UserRoleService, Depends(get_user_role_service)]
