from abc import ABC
from app.shared.base_domain.repository import IBaseRepository, BaseRepository
from app.database.model import User
from sqlmodel import Session


class IUserRepository(IBaseRepository[User], ABC):
    pass


class UserRepository(BaseRepository[User], IUserRepository):
    model = User

    def __init__(self, session: Session):
        super().__init__(session)
