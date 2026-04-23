from uuid import UUID
from fastapi import status

from app.domain.administrator.schemas import AdministratorResponse
from app.domain.administrator.service import AdministratorServiceDep
from app.domain.auth.service import CurrentAccountDep
from app.shared.authorization.dependencies import require_read, require_administer
from app.domain.personal_data.schemas import PersonalDataCreate, PersonalDataUpdate
from app.database.model import Administrator
from app.shared.base_domain.controller import ImmutableApiController


class AdministratorController(ImmutableApiController):
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

    def _register_routes(self):
        super()._register_routes()

        def update(
            service: AdministratorServiceDep,
            resource_id: UUID,
            payload: PersonalDataUpdate,
        ):
            return service.update_entity(resource_id, payload)

        self.router.add_api_route(
            "/{resource_id}",
            update,
            methods=["PATCH"],
            response_model=self.response_schema,
            dependencies=self.update_dependencies,
        )


administrator_router = AdministratorController().router


@administrator_router.delete(
    "/{resource_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[require_administer(Administrator)],
)
def delete_administrator(
    resource_id: UUID,
    service: AdministratorServiceDep,
    current: CurrentAccountDep,
):
    service.delete_administrator(resource_id, current)