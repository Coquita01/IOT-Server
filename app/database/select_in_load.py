from sqlalchemy.orm import selectinload
from app.database.model import (
    NonCriticalPersonalData, SensitiveData, Administrator,
    Manager, User, Service, ManagerService, Application,
    ApplicationService, Device, DeviceService, Role,
    UserRole, TicketStatus, ServiceTicket, EcosystemTicket
)

# ─────────────────────────────────────────────
# NonCriticalPersonalData
# ─────────────────────────────────────────────
LOAD_NON_CRITICAL_PERSONAL_DATA = [
    selectinload(NonCriticalPersonalData.sensitive_data),
]

LOAD_NON_CRITICAL_PERSONAL_DATA_FULL = [
    selectinload(NonCriticalPersonalData.sensitive_data).selectinload(SensitiveData.administrator),
    selectinload(NonCriticalPersonalData.sensitive_data).selectinload(SensitiveData.manager),
    selectinload(NonCriticalPersonalData.sensitive_data).selectinload(SensitiveData.user),
]

# ─────────────────────────────────────────────
# SensitiveData
# ─────────────────────────────────────────────
LOAD_SENSITIVE_DATA = [
    selectinload(SensitiveData.non_critical_data),
    selectinload(SensitiveData.administrator),
    selectinload(SensitiveData.manager),
    selectinload(SensitiveData.user),
]

# ─────────────────────────────────────────────
# Administrator
# ─────────────────────────────────────────────
LOAD_ADMINISTRATOR = [
    selectinload(Administrator.sensitive_data),
    selectinload(Administrator.manager_services),
    selectinload(Administrator.registered_applications),
]

LOAD_ADMINISTRATOR_FULL = [
    selectinload(Administrator.sensitive_data)
        .selectinload(SensitiveData.non_critical_data),
    selectinload(Administrator.manager_services)
        .selectinload(Service.manager_services),
    selectinload(Administrator.registered_applications)
        .selectinload(Application.application_services),
]

# ─────────────────────────────────────────────
# Manager
# ─────────────────────────────────────────────
LOAD_MANAGER = [
    selectinload(Manager.sensitive_data),
    selectinload(Manager.manager_services),
]

LOAD_MANAGER_FULL = [
    selectinload(Manager.sensitive_data)
        .selectinload(SensitiveData.non_critical_data),
    selectinload(Manager.manager_services)
        .selectinload(ManagerService.service),
    selectinload(Manager.manager_services)
        .selectinload(ManagerService.ecosystem_tickets),
]

# ─────────────────────────────────────────────
# User
# ─────────────────────────────────────────────
LOAD_USER = [
    selectinload(User.sensitive_data),
    selectinload(User.user_roles),
]

LOAD_USER_FULL = [
    selectinload(User.sensitive_data)
        .selectinload(SensitiveData.non_critical_data),
    selectinload(User.user_roles)
        .selectinload(UserRole.role)
        .selectinload(Role.service),
    selectinload(User.user_roles)
        .selectinload(UserRole.service_tickets),
]

# ─────────────────────────────────────────────
# Service
# ─────────────────────────────────────────────
LOAD_SERVICE = [
    selectinload(Service.registered_by),
    selectinload(Service.manager_services),
    selectinload(Service.application_services),
    selectinload(Service.device_services),
    selectinload(Service.roles),
    selectinload(Service.service_tickets),
]

LOAD_SERVICE_FULL = [
    selectinload(Service.registered_by)
        .selectinload(Administrator.sensitive_data),
    selectinload(Service.manager_services)
        .selectinload(ManagerService.manager),
    selectinload(Service.application_services)
        .selectinload(ApplicationService.application),
    selectinload(Service.device_services)
        .selectinload(DeviceService.device),
    selectinload(Service.roles)
        .selectinload(Role.permission),
    selectinload(Service.roles)
        .selectinload(Role.user_roles),
    selectinload(Service.service_tickets)
        .selectinload(ServiceTicket.status),
]

# ─────────────────────────────────────────────
# ManagerService
# ─────────────────────────────────────────────
LOAD_MANAGER_SERVICE = [
    selectinload(ManagerService.manager),
    selectinload(ManagerService.service),
    selectinload(ManagerService.ecosystem_tickets),
]

LOAD_MANAGER_SERVICE_FULL = [
    selectinload(ManagerService.manager)
        .selectinload(Manager.sensitive_data),
    selectinload(ManagerService.service)
        .selectinload(Service.roles),
    selectinload(ManagerService.ecosystem_tickets)
        .selectinload(EcosystemTicket.status),
]

# ─────────────────────────────────────────────
# Application
# ─────────────────────────────────────────────
LOAD_APPLICATION = [
    selectinload(Application.registered_by),
    selectinload(Application.application_services),
]

LOAD_APPLICATION_FULL = [
    selectinload(Application.registered_by)
        .selectinload(Administrator.sensitive_data),
    selectinload(Application.application_services)
        .selectinload(ApplicationService.service),
]

# ─────────────────────────────────────────────
# Device
# ─────────────────────────────────────────────
LOAD_DEVICE = [
    selectinload(Device.device_services),
]

LOAD_DEVICE_FULL = [
    selectinload(Device.device_services)
        .selectinload(DeviceService.service),
]

# ─────────────────────────────────────────────
# Role
# ─────────────────────────────────────────────
LOAD_ROLE = [
    selectinload(Role.service),
    selectinload(Role.permission),
    selectinload(Role.user_roles),
]

LOAD_ROLE_FULL = [
    selectinload(Role.service)
        .selectinload(Service.registered_by),
    selectinload(Role.permission),
    selectinload(Role.user_roles)
        .selectinload(UserRole.user),
    selectinload(Role.user_roles)
        .selectinload(UserRole.service_tickets),
]

# ─────────────────────────────────────────────
# UserRole
# ─────────────────────────────────────────────
LOAD_USER_ROLE = [
    selectinload(UserRole.user),
    selectinload(UserRole.role),
    selectinload(UserRole.service_tickets),
]

LOAD_USER_ROLE_FULL = [
    selectinload(UserRole.user)
        .selectinload(User.sensitive_data),
    selectinload(UserRole.role)
        .selectinload(Role.service),
    selectinload(UserRole.service_tickets)
        .selectinload(ServiceTicket.status),
]

# ─────────────────────────────────────────────
# TicketStatus
# ─────────────────────────────────────────────
LOAD_TICKET_STATUS = [
    selectinload(TicketStatus.service_tickets),
    selectinload(TicketStatus.ecosystem_tickets),
]

# ─────────────────────────────────────────────
# ServiceTicket
# ─────────────────────────────────────────────
LOAD_SERVICE_TICKET = [
    selectinload(ServiceTicket.user_role),
    selectinload(ServiceTicket.status),
    selectinload(ServiceTicket.service),
]

LOAD_SERVICE_TICKET_FULL = [
    selectinload(ServiceTicket.user_role)
        .selectinload(UserRole.user)
        .selectinload(User.sensitive_data),
    selectinload(ServiceTicket.status),
    selectinload(ServiceTicket.service)
        .selectinload(Service.roles),
]

# ─────────────────────────────────────────────
# EcosystemTicket
# ─────────────────────────────────────────────
LOAD_ECOSYSTEM_TICKET = [
    selectinload(EcosystemTicket.manager_service),
    selectinload(EcosystemTicket.status),
]

LOAD_ECOSYSTEM_TICKET_FULL = [
    selectinload(EcosystemTicket.manager_service)
        .selectinload(ManagerService.manager)
        .selectinload(Manager.sensitive_data),
    selectinload(EcosystemTicket.manager_service)
        .selectinload(ManagerService.service),
    selectinload(EcosystemTicket.status),
]
