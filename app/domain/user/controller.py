from app.shared.base_domain.controller import FullCrudApiController
from app.domain.user.schemas import UserResponse
from app.domain.user.service import UserServiceDep
from app.shared.authorization.dependencies import require_read, require_write, require_delete
from app.domain.personal_data.schemas import PersonalDataCreate, PersonalDataUpdate
from app.database.model import User


class UserController(FullCrudApiController):
    prefix = "/users"
    tags = ["Users"]

    service_dep = UserServiceDep
    response_schema = UserResponse
    create_schema = PersonalDataCreate
    update_schema = PersonalDataUpdate

    list_dependencies = [require_read(User)]
    retrieve_dependencies = [require_read(User)]
    create_dependencies = [require_write(User)]
    update_dependencies = [require_write(User)]
    delete_dependencies = [require_delete(User)]


user_router = UserController().router

# User login endpoint
from app.shared.auth.controller import AuthApiController
user_auth_controller = AuthApiController("user", "/users/login")
user_login_router = user_auth_controller.router