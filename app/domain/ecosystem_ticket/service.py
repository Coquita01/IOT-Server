from typing import Annotated
from uuid import UUID

from fastapi import Depends

from app.database import SessionDep
from app.database.model import EcosystemTicket
from app.domain.ecosystem_ticket.repository import EcosystemTicketRepository
from app.domain.ecosystem_ticket.schemas import EcosystemTicketCreate, EcosystemTicketUpdate
from app.shared.base_domain.service import BaseService, IBaseService
from app.shared.exceptions import BadRequestException, NotFoundException
from app.shared.pagination import PageResponse


class IEcosystemTicketService(
    IBaseService[EcosystemTicket, EcosystemTicketCreate, EcosystemTicketUpdate]
):
    pass


class EcosystemTicketService(
    BaseService[EcosystemTicket, EcosystemTicketCreate, EcosystemTicketUpdate]
):
    entity_name = "EcosystemTicket"
    repository_class = EcosystemTicketRepository

    def get_all_for_manager(
        self, manager_id: UUID, offset: int = 0, limit: int = 20
    ) -> PageResponse[EcosystemTicket]:
        items, total = self.repository.get_all_for_manager(manager_id, offset, limit)
        return PageResponse(total=total, offset=offset, limit=limit, data=items)

    def _assert_manager_owns_ticket(self, ticket_id: UUID, manager_id: UUID) -> None:
        """Raises 404 (not 403) to avoid confirming the ticket exists to unauthorized managers."""
        if not self.repository.ticket_belongs_to_manager(ticket_id, manager_id):
            raise NotFoundException(self.entity_name, ticket_id)

    def get_by_id_for_manager(self, ticket_id: UUID, manager_id: UUID) -> EcosystemTicket:
        self._assert_manager_owns_ticket(ticket_id, manager_id)
        return self.get_by_id(ticket_id)

    def update_for_manager(
        self, ticket_id: UUID, payload: EcosystemTicketUpdate, manager_id: UUID
    ) -> EcosystemTicket:
        self._assert_manager_owns_ticket(ticket_id, manager_id)
        return self.update_entity(ticket_id, payload)

    def create_for_manager(
        self, payload: EcosystemTicketCreate, manager_id: UUID
    ) -> EcosystemTicket:
        belongs = self.repository.manager_service_belongs_to_manager(
            payload.manager_service_id, manager_id
        )
        if not belongs:
            raise BadRequestException(
                "The manager_service_id does not belong to the current manager"
            )
        return self.create_entity(payload)

    def _build_entity(self, payload: EcosystemTicketCreate) -> EcosystemTicket:
        return EcosystemTicket(**payload.model_dump())


def get_ecosystem_ticket_service(session: SessionDep) -> EcosystemTicketService:
    return EcosystemTicketService(session)


EcosystemTicketServiceDep = Annotated[
    EcosystemTicketService, Depends(get_ecosystem_ticket_service)
]
