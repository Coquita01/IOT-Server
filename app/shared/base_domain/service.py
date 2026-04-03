from abc import ABC
from typing import Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel
from sqlmodel import Session

from app.shared.base_domain.model import BaseTable
from app.shared.base_domain.repository import IBaseRepository, BaseRepository
from app.shared.exceptions import NotFoundException
from app.shared.pagination import PageResponse

T = TypeVar("T", bound=BaseTable)
P_create = TypeVar("P_create", bound=BaseModel)
P_update = TypeVar("P_update", bound=BaseModel)


class IBaseService(ABC, Generic[T, P_create, P_update]):
    repository: IBaseRepository[T] | None = None
    entity_name: str = "Resource"


class BaseService(ABC, Generic[T, P_create, P_update]):
    repository_class: type[BaseRepository] | None = None
    entity_name: str = "Resource"

    def __init__(self, session: Session):
        self.session = session
        if self.repository_class is None:
            raise ValueError("repository_class must be defined in subclass")
        self.repository: IBaseRepository[T] = self.repository_class(session)

    def get_by_id(self, id: UUID) -> T:
        entity = self.repository.get_by_id(id)
        if not entity:
            raise NotFoundException(self.entity_name, id)
        return entity

    def get_all(self, offset: int = 0, limit: int = 20) -> PageResponse[T]:
        items, total = self.repository.get_all(offset, limit)
        return PageResponse(
            total=total,
            offset=offset,
            limit=limit,
            data=items,
        )

    def create_entity(self, payload: P_create) -> T:
        return self.repository.create(self._build_entity(payload))

    def update_entity(self, id: UUID, payload: P_update) -> T:
        entity = self.get_by_id(id)
        update_data = payload.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            
            if not hasattr(entity, field):
                continue

            attr = getattr(type(entity), field, None)

            
            if isinstance(attr, property) and attr.fset is None:
                continue

            setattr(entity, field, value)

        return self.repository.update(entity)

    def delete_entity(self, id: UUID) -> bool:
        entity = self.repository.get_by_id(id)
        if not entity:
            return False

        self.repository.delete(entity)
        return True

    def _build_entity(self, payload: P_create | P_update) -> T:
        return self.repository.model(**payload.model_dump())