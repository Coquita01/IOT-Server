from app.shared.base_domain.controller import FullCrudApiController
from app.domain.manager.schemas import ManagerResponse
from app.domain.manager.service import ManagerServiceDep
from app.shared.authorization.dependencies import require_read, require_write, require_delete
from app.domain.personal_data.schemas import PersonalDataCreate, PersonalDataUpdate
from app.database.model import Manager


class ManagerController(FullCrudApiController):
    prefix = "/managers"
    tags = ["Managers"]
    service_dep = ManagerServiceDep
    response_schema = ManagerResponse
    create_schema = PersonalDataCreate
    update_schema = PersonalDataUpdate

    list_dependencies = [require_read(Manager)]
    retrieve_dependencies = [require_read(Manager)]
    create_dependencies = [require_write(Manager)]
    update_dependencies = [require_write(Manager)]
    delete_dependencies = [require_delete(Manager)]


manager_router = ManagerController().router

# Endpoint de login de manager
from app.shared.auth.controller import AuthApiController
manager_auth_controller = AuthApiController("master", "/managers/login")
manager_login_router = manager_auth_controller.router
