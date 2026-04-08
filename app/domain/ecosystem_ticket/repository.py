from abc import ABC
from uuid import UUID

from sqlmodel import Session, select, func

from app.shared.base_domain.repository import IBaseRepository, BaseRepository
from app.database.model import EcosystemTicket, ManagerService


class IEcosystemTicketRepository(IBaseRepository[EcosystemTicket], ABC):
    pass


class EcosystemTicketRepository(
    BaseRepository[EcosystemTicket], IEcosystemTicketRepository
):
    model = EcosystemTicket

    def __init__(self, session: Session):
        super().__init__(session)

    def get_all_for_manager(
        self, manager_id: UUID, offset: int = 0, limit: int = 20
    ) -> tuple[list[EcosystemTicket], int]:
        stmt = (
            select(EcosystemTicket)
            .join(ManagerService, EcosystemTicket.manager_service_id == ManagerService.id)
            .where(ManagerService.manager_id == manager_id)
        )
        total = self.session.exec(
            select(func.count()).select_from(stmt.subquery())
        ).one()
        items = self.session.exec(stmt.offset(offset).limit(limit)).all()
        return list(items), total

    def manager_service_belongs_to_manager(
        self, manager_service_id: UUID, manager_id: UUID
    ) -> bool:
        stmt = select(ManagerService).where(
            ManagerService.id == manager_service_id,
            ManagerService.manager_id == manager_id,
        )
        return self.session.exec(stmt).first() is not None

    def ticket_belongs_to_manager(
        self, ticket_id: UUID, manager_id: UUID
    ) -> bool:
        stmt = (
            select(EcosystemTicket)
            .join(ManagerService, EcosystemTicket.manager_service_id == ManagerService.id)
            .where(
                EcosystemTicket.id == ticket_id,
                ManagerService.manager_id == manager_id,
            )
        )
        return self.session.exec(stmt).first() is not None
