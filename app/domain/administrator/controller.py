from app.shared.base_domain.controller import FullCrudApiController
from app.domain.administrator.schemas import AdministratorResponse
from app.domain.administrator.service import AdministratorServiceDep
from app.shared.authorization.dependencies import require_read, require_administer
from app.domain.personal_data.schemas import PersonalDataCreate, PersonalDataUpdate
from app.database.model import Administrator


class AdministratorController(FullCrudApiController):
    prefix = "/administrators"
    tags = ["Administrators"]

    service_dep = AdministratorServiceDep
    response_schema = AdministratorResponse
    create_schema = PersonalDataCreate
    update_schema = PersonalDataUpdate

    list_dependencies = [require_read(Administrator)]
    retrieve_dependencies = [require_read(Administrator)]
    create_dependencies = [require_administer(Administrator)]
    update_dependencies = [require_administer(Administrator)]
    delete_dependencies = [require_administer(Administrator)]


administrator_router = AdministratorController().router

# Administrator login endpoint
from app.shared.auth.controller import AuthApiController
administrator_auth_controller = AuthApiController("admin", "/administrators/login")
administrator_login_router = administrator_auth_controller.router