# from app.shared.base_domain.controller import ReadOnlyApiController
from app.shared.base_domain.controller import FullCrudApiController
from app.domain.user.schemas import UserResponse
from app.domain.user.service import UserServiceDep
from app.domain.personal_data.schemas import PersonalDataCreate, PersonalDataUpdate


class UserController(FullCrudApiController):
    prefix = "/users"
    tags = ["Users"]
    service_dep = UserServiceDep
    response_schema = UserResponse
    create_schema = PersonalDataCreate
    update_schema = PersonalDataUpdate


user_router = UserController().router
