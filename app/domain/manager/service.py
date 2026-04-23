from abc import ABC
from typing import Annotated
from uuid import UUID
from fastapi import Depends
from app.shared.base_domain.service import IBaseService
from app.database.model import Manager, UserRole, Role, User
from app.database import SessionDep
from app.domain.manager.repository import ManagerRepository
from app.domain.personal_data.schemas import PersonalDataCreate, PersonalDataUpdate
from app.domain.personal_data.service import PersonalDataService
from app.shared.exceptions import NotFoundException, AlreadyExistsException
from sqlmodel import Session, select


class IManagerService(
    IBaseService[Manager, PersonalDataCreate, PersonalDataUpdate], ABC
):
    pass


class ManagerService(PersonalDataService[Manager], IManagerService):
    entity_name = "Manager"
    repository_class = ManagerRepository

    def assign_user_to_role(self, manager_id: UUID, user_id: UUID, role_id: UUID) -> UserRole:
        """Assign a user to a role (Manager only operation)
        
        Validates that the role belongs to a service managed by this manager.
        """
        # Verify manager exists and get their services
        manager = self.repository.session.get(Manager, manager_id)
        if not manager:
            raise NotFoundException(f"Manager with id '{manager_id}' was not found")
        
        # Verify user exists
        user = self.repository.session.get(User, user_id)
        if not user:
            raise NotFoundException(f"User with id '{user_id}' was not found")
        
        # Verify role exists
        role = self.repository.session.get(Role, role_id)
        if not role:
            raise NotFoundException(f"Role with id '{role_id}' was not found")
        
        # SECURITY: Verify the role's service is managed by this manager
        manager_service = self.repository.session.exec(
            select(ManagerService).where(
                ManagerService.manager_id == manager_id,
                ManagerService.service_id == role.service_id
            )
        ).first()
        
        if not manager_service:
            raise NotFoundException(
                f"Manager '{manager_id}' does not manage Service '{role.service_id}' "
                f"that contains Role '{role_id}'"
            )
        
        # Check if assignment already exists
        existing = self.repository.session.exec(
            select(UserRole).where(
                UserRole.user_id == user_id, UserRole.role_id == role_id
            )
        ).first()
        
        if existing:
            raise AlreadyExistsException(
                f"User '{user_id}' is already assigned to role '{role_id}'"
            )
        
        # Create the assignment
        user_role = UserRole(user_id=user_id, role_id=role_id)
        self.repository.session.add(user_role)
        self.repository.session.commit()
        self.repository.session.refresh(user_role)
        
        return user_role

    def remove_user_from_role(self, manager_id: UUID, user_id: UUID, role_id: UUID) -> None:
        """Remove a user from a role (Manager only operation)
        
        Validates that the role belongs to a service managed by this manager.
        """
        # Verify manager exists and manages the service
        manager = self.repository.session.get(Manager, manager_id)
        if not manager:
            raise NotFoundException(f"Manager with id '{manager_id}' was not found")
        
        # Verify role exists
        role = self.repository.session.get(Role, role_id)
        if not role:
            raise NotFoundException(f"Role with id '{role_id}' was not found")
        
        # SECURITY: Verify the role's service is managed by this manager
        manager_service = self.repository.session.exec(
            select(ManagerService).where(
                ManagerService.manager_id == manager_id,
                ManagerService.service_id == role.service_id
            )
        ).first()
        
        if not manager_service:
            raise NotFoundException(
                f"Manager '{manager_id}' does not manage Service '{role.service_id}' "
                f"that contains Role '{role_id}'"
            )
        
        user_role = self.repository.session.exec(
            select(UserRole).where(
                UserRole.user_id == user_id, UserRole.role_id == role_id
            )
        ).first()
        
        if not user_role:
            raise NotFoundException(
                f"User '{user_id}' is not assigned to role '{role_id}'"
            )
        
        self.repository.session.delete(user_role)
        self.repository.session.commit()

    def get_user_roles(self, user_id: UUID) -> list[UserRole]:
        """Get all roles assigned to a user"""
        user = self.repository.session.get(User, user_id)
        if not user:
            raise NotFoundException(f"User with id '{user_id}' was not found")
        
        return self.repository.session.exec(
            select(UserRole).where(UserRole.user_id == user_id)
        ).all()


def get_manager_service(session: SessionDep) -> ManagerService:
    return ManagerService(session)


ManagerServiceDep = Annotated[ManagerService, Depends(get_manager_service)]
