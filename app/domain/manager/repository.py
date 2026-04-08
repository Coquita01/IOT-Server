from abc import ABC
from uuid import UUID

from sqlmodel import Session, select

from app.shared.base_domain.repository import IBaseRepository, BaseRepository
from app.database.model import Manager, ManagerService, Service


class IManagerRepository(IBaseRepository[Manager], ABC):
    pass


class ManagerRepository(BaseRepository[Manager], IManagerRepository):
    model = Manager

    def __init__(self, session: Session):
        super().__init__(session)

    def get_manager_service(
        self, manager_id: UUID, service_id: UUID
    ) -> ManagerService | None:
        stmt = select(ManagerService).where(
            ManagerService.manager_id == manager_id,
            ManagerService.service_id == service_id,
        )
        return self.session.exec(stmt).first()

    def get_service(self, service_id: UUID) -> Service | None:
        return self.session.get(Service, service_id)

    def assign_service(self, manager_id: UUID, service_id: UUID) -> ManagerService:
        link = ManagerService(manager_id=manager_id, service_id=service_id)
        self.session.add(link)
        self.session.commit()
        self.session.refresh(link)
        return link

    def unassign_service(self, link: ManagerService) -> None:
        self.session.delete(link)
        self.session.commit()
