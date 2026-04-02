from app.shared.base_domain.controller import FullCrudApiController
from app.domain.application.schemas import ApplicationCreate, ApplicationResponse, ApplicationUpdate
from app.domain.application.service import ApplicationServiceDep


class ApplicationController(FullCrudApiController):
    prefix = "/applications"
    tags = ["Applications"]
    service_dep = ApplicationServiceDep
    response_schema = ApplicationResponse
    create_schema = ApplicationCreate
    update_schema = ApplicationUpdate


application_router = ApplicationController().router