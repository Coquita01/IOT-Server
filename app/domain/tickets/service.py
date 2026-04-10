from abc import ABC
from typing import Annotated

from fastapi import Depends

from app.database import SessionDep
from app.database.model import EcosystemTicket, ServiceTicket
from app.domain.tickets.repository import EcosystemTicketRepository, ServiceTicketRepository
from app.domain.tickets.schemas import (
    EcosystemTicketCreate,
    EcosystemTicketUpdate,
    ServiceTicketCreate,
    ServiceTicketUpdate,
)
from app.shared.base_domain.service import BaseService, IBaseService


# ─────────────────────────────────────────────
# ServiceTicket service
# ─────────────────────────────────────────────

class IServiceTicketService(
    IBaseService[ServiceTicket, ServiceTicketCreate, ServiceTicketUpdate], ABC
):
    pass


class ServiceTicketService(
    BaseService[ServiceTicket, ServiceTicketCreate, ServiceTicketUpdate],
    IServiceTicketService,
):
    entity_name = "ServiceTicket"
    repository_class = ServiceTicketRepository


def get_service_ticket_service(session: SessionDep) -> ServiceTicketService:
    return ServiceTicketService(session)


ServiceTicketServiceDep = Annotated[ServiceTicketService, Depends(get_service_ticket_service)]


# ─────────────────────────────────────────────
# EcosystemTicket service
# ─────────────────────────────────────────────

class IEcosystemTicketService(
    IBaseService[EcosystemTicket, EcosystemTicketCreate, EcosystemTicketUpdate], ABC
):
    pass


class EcosystemTicketService(
    BaseService[EcosystemTicket, EcosystemTicketCreate, EcosystemTicketUpdate],
    IEcosystemTicketService,
):
    entity_name = "EcosystemTicket"
    repository_class = EcosystemTicketRepository


def get_ecosystem_ticket_service(session: SessionDep) -> EcosystemTicketService:
    return EcosystemTicketService(session)


EcosystemTicketServiceDep = Annotated[
    EcosystemTicketService, Depends(get_ecosystem_ticket_service)
]
