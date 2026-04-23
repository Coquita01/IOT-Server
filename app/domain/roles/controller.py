from app.shared.base_domain.controller import FullCrudApiController
from app.domain.roles.schemas import RoleCreate, RoleResponse, RoleUpdate
from app.domain.roles.service import RoleServiceDep
from app.shared.authorization.dependencies import require_read, require_write, require_delete
from app.database.model import Role


class RoleController(FullCrudApiController):
    prefix = "/roles"
    tags = ["Roles"]
    service_dep = RoleServiceDep
    response_schema = RoleResponse
    create_schema = RoleCreate
    update_schema = RoleUpdate
    
    # OSO-based authorization
    list_dependencies = [require_read(Role)]
    retrieve_dependencies = [require_read(Role)]
    create_dependencies = [require_write(Role)]
    update_dependencies = [require_write(Role)]
    delete_dependencies = [require_delete(Role)]


role_router = RoleController().router
