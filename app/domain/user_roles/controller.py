from app.shared.base_domain.controller import FullCrudApiController
from app.domain.user_roles.schemas import UserRoleCreate, UserRoleResponse, UserRoleUpdate
from app.domain.user_roles.service import UserRoleServiceDep
from app.shared.authorization.dependencies import require_read, require_write, require_delete
from app.database.model import UserRole


class UserRoleController(FullCrudApiController):
    prefix = "/user-roles"
    tags = ["User Roles"]
    service_dep = UserRoleServiceDep
    response_schema = UserRoleResponse
    create_schema = UserRoleCreate
    update_schema = UserRoleUpdate
    
    # OSO-based authorization
    list_dependencies = [require_read(UserRole)]
    retrieve_dependencies = [require_read(UserRole)]
    create_dependencies = [require_write(UserRole)]
    update_dependencies = [require_write(UserRole)]
    delete_dependencies = [require_delete(UserRole)]


user_role_router = UserRoleController().router
