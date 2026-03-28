# from app.shared.base_domain.controller import ReadOnlyApiController
from app.shared.base_domain.controller import FullCrudApiController
from app.domain.administrator.schemas import AdministratorResponse
from app.domain.administrator.service import AdministratorServiceDep
from app.domain.personal_data.schemas import PersonalDataCreate, PersonalDataUpdate


class AdministratorController(FullCrudApiController):
    prefix = "/administrators"
    tags = ["Administrators"]
    service_dep = AdministratorServiceDep
    response_schema = AdministratorResponse
    create_schema = PersonalDataCreate
    update_schema = PersonalDataUpdate


administrator_router = AdministratorController().router
