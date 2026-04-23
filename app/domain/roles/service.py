from abc import ABC
from app.shared.base_domain.service import IBaseService
from app.database.model import Role
from typing import Annotated
from fastapi import Depends
from app.shared.base_domain.service import BaseService
from app.domain.roles.repository import RoleRepository
from app.database import SessionDep
from app.domain.roles.schemas import RoleCreate, RoleUpdate


class IRoleService(IBaseService[Role, RoleCreate, RoleUpdate]):
    pass


class RoleService(BaseService[Role, RoleCreate, RoleUpdate], IRoleService):
    entity_name = "Role"
    repository_class = RoleRepository


def get_role_service(session: SessionDep) -> RoleService:
    return RoleService(session)


RoleServiceDep = Annotated[RoleService, Depends(get_role_service)]
