from abc import ABC

from sqlmodel import Session

from app.database.model import EcosystemTicket, ServiceTicket
from app.shared.base_domain.repository import BaseRepository, IBaseRepository


# ─────────────────────────────────────────────
# ServiceTicket repository
# ─────────────────────────────────────────────

class IServiceTicketRepository(IBaseRepository[ServiceTicket], ABC):
    pass


class ServiceTicketRepository(BaseRepository[ServiceTicket], IServiceTicketRepository):
    model = ServiceTicket

    def __init__(self, session: Session):
        super().__init__(session)


# ─────────────────────────────────────────────
# EcosystemTicket repository
# ─────────────────────────────────────────────

class IEcosystemTicketRepository(IBaseRepository[EcosystemTicket], ABC):
    pass


class EcosystemTicketRepository(BaseRepository[EcosystemTicket], IEcosystemTicketRepository):
    model = EcosystemTicket

    def __init__(self, session: Session):
        super().__init__(session)
