from app.shared.base_domain.model import BaseTable
from app.domain.personal_data.model import DatosSensibles
from sqlmodel import Field, Relationship
from app.domain.service.model import Service
from uuid import UUID



class Manager(BaseTable, table=True):
    __tablename__ = "manager"

    sensitive_data_id: UUID = Field(foreign_key="datos_sensibles.id", unique=True)
    active: bool = Field(default=True)

    sensitive_data: DatosSensibles = Relationship(back_populates="manager")
    manager_servicios: list["ManagerService"] = Relationship(back_populates="manager")


class ManagerService(BaseTable, table=True):
    __tablename__ = "manager_service"

    manager_id: UUID = Field(foreign_key="manager.id")
    service_id: UUID = Field(foreign_key="service.id")

    manager: Manager = Relationship(back_populates="manager_service")
    service: Service = Relationship(back_populates="manager_service")
    ecosystem_tickets: list["EcosystemTicket"] = Relationship(
        back_populates="manager_service"
    )    