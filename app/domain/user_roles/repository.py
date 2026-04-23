from abc import ABC
from app.shared.base_domain.repository import IBaseRepository
from app.database.model import UserRole
from sqlmodel import Session
from app.shared.base_domain.repository import BaseRepository


class IUserRoleRepository(IBaseRepository[UserRole], ABC):
    pass


class UserRoleRepository(BaseRepository[UserRole], IUserRoleRepository):
    model = UserRole

    def __init__(self, session: Session):
        super().__init__(session)
