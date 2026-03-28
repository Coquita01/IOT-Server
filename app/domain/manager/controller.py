# from app.shared.base_domain.controller import ReadOnlyApiController
from app.shared.base_domain.controller import FullCrudApiController
from app.domain.manager.schemas import ManagerResponse
from app.domain.manager.service import ManagerServiceDep
from app.domain.personal_data.schemas import PersonalDataCreate, PersonalDataUpdate


class ManagerController(FullCrudApiController):
    prefix = "/managers"
    tags = ["Managers"]
    service_dep = ManagerServiceDep
    response_schema = ManagerResponse
    create_schema = PersonalDataCreate
    update_schema = PersonalDataUpdate


manager_router = ManagerController().router
