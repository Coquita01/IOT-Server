from app.shared.base_domain.controller import FullCrudApiController
from app.domain.device.schemas import DeviceCreate, DeviceResponse, DeviceUpdate
from app.domain.device.service import DeviceServiceDep


class DeviceController(FullCrudApiController):
    prefix = "/devices"
    tags = ["Devices"]
    service_dep = DeviceServiceDep
    response_schema = DeviceResponse
    create_schema = DeviceCreate
    update_schema = DeviceUpdate


router = DeviceController().router
