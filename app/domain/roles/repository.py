from abc import ABC
from app.shared.base_domain.repository import IBaseRepository
from app.database.model import Role
from sqlmodel import Session
from app.shared.base_domain.repository import BaseRepository


class IRoleRepository(IBaseRepository[Role], ABC):
    pass


class RoleRepository(BaseRepository[Role], IRoleRepository):
    model = Role

    def __init__(self, session: Session):
        super().__init__(session)
