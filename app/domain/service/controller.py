from app.shared.base_domain.controller import FullCrudApiController
from app.domain.service.schemas import ServiceCreate, ServiceResponse, ServiceUpdate
from app.domain.service.service import ServiceServiceDep


class ServiceController(FullCrudApiController):
    prefix = "/services"
    tags = ["Services"]
    service_dep = ServiceServiceDep
    response_schema = ServiceResponse
    create_schema = ServiceCreate
    update_schema = ServiceUpdate


service_router = ServiceController().router