from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.domain.ecosystem_ticket.schemas import (
    EcosystemTicketCreate,
    EcosystemTicketResponse,
    EcosystemTicketUpdate,
)
from app.domain.ecosystem_ticket.service import EcosystemTicketServiceDep
from app.domain.auth.service import (
    CurrentAccount,
    require_admin,
    require_admin_or_manager,
)
from app.shared.pagination import PageParams, PageResponse


router = APIRouter(prefix="/ecosystem-tickets", tags=["Ecosystem Tickets"])


@router.get("/", response_model=PageResponse[EcosystemTicketResponse])
def list_ecosystem_tickets(
    service: EcosystemTicketServiceDep,
    current: Annotated[CurrentAccount, Depends(require_admin_or_manager)],
    page: PageParams = Depends(),
) -> PageResponse[EcosystemTicketResponse]:
    if current.account_type == "manager":
        return service.get_all_for_manager(
            current.account_id, offset=page.offset, limit=page.limit
        )
    return service.get_all(offset=page.offset, limit=page.limit)


@router.get("/{ticket_id}", response_model=EcosystemTicketResponse)
def retrieve_ecosystem_ticket(
    ticket_id: UUID,
    service: EcosystemTicketServiceDep,
    current: Annotated[CurrentAccount, Depends(require_admin_or_manager)],
) -> EcosystemTicketResponse:
    if current.account_type == "manager":
        return service.get_by_id_for_manager(ticket_id, current.account_id)
    return service.get_by_id(ticket_id)


@router.post(
    "/",
    response_model=EcosystemTicketResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_ecosystem_ticket(
    payload: EcosystemTicketCreate,
    service: EcosystemTicketServiceDep,
    current: Annotated[CurrentAccount, Depends(require_admin_or_manager)],
) -> EcosystemTicketResponse:
    if current.account_type == "manager":
        return service.create_for_manager(payload, current.account_id)
    return service.create_entity(payload)


@router.patch("/{ticket_id}", response_model=EcosystemTicketResponse)
def update_ecosystem_ticket(
    ticket_id: UUID,
    payload: EcosystemTicketUpdate,
    service: EcosystemTicketServiceDep,
    current: Annotated[CurrentAccount, Depends(require_admin_or_manager)],
) -> EcosystemTicketResponse:
    if current.account_type == "manager":
        return service.update_for_manager(ticket_id, payload, current.account_id)
    return service.update_entity(ticket_id, payload)


@router.delete("/{ticket_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ecosystem_ticket(
    ticket_id: UUID,
    service: EcosystemTicketServiceDep,
    _: Annotated[CurrentAccount, Depends(require_admin)],
) -> None:
    service.delete_entity(ticket_id)


ecosystem_ticket_router = router
