from typing import Annotated
from uuid import UUID
from fastapi import Depends, status
from app.shared.base_domain.controller import FullCrudApiController
from app.domain.manager.schemas import ManagerResponse, ManagerServiceResponse
from app.domain.manager.service import ManagerServiceDep
from app.domain.auth.service import CurrentAccount, require_admin, require_manager
from app.domain.personal_data.schemas import PersonalDataCreate, PersonalDataUpdate


class ManagerController(FullCrudApiController):
    prefix = "/managers"
    tags = ["Managers"]
    service_dep = ManagerServiceDep
    response_schema = ManagerResponse
    create_schema = PersonalDataCreate
    update_schema = PersonalDataUpdate

    list_dependencies = [Depends(require_admin)]
    retrieve_dependencies = [Depends(require_admin)]
    create_dependencies = [Depends(require_admin)]
    update_dependencies = [Depends(require_admin)]
    delete_dependencies = [Depends(require_admin)]

    def _register_routes(self):
        # Register /me before /{resource_id} to avoid UUID validation conflict
        def me(
            service: self.service_dep,
            current: Annotated[CurrentAccount, Depends(require_manager)],
        ) -> ManagerResponse:
            return service.get_by_id(current.account_id)

        self.router.add_api_route(
            "/me",
            me,
            methods=["GET"],
            response_model=self.response_schema,
        )

        def update_me(
            service: self.service_dep,
            payload: PersonalDataUpdate,
            current: Annotated[CurrentAccount, Depends(require_manager)],
        ) -> ManagerResponse:
            return service.update_entity(current.account_id, payload)

        self.router.add_api_route(
            "/me",
            update_me,
            methods=["PATCH"],
            response_model=self.response_schema,
        )

        super()._register_routes()

        # --- Service assignment routes ---

        def list_services(
            manager_id: UUID,
            service: self.service_dep,
            _: Annotated[CurrentAccount, Depends(require_admin)],
        ) -> list[ManagerServiceResponse]:
            return service.list_services(manager_id)

        self.router.add_api_route(
            "/{manager_id}/services",
            list_services,
            methods=["GET"],
            response_model=list[ManagerServiceResponse],
        )

        def assign_service(
            manager_id: UUID,
            service_id: UUID,
            service: self.service_dep,
            _: Annotated[CurrentAccount, Depends(require_admin)],
        ) -> ManagerServiceResponse:
            return service.assign_service(manager_id, service_id)

        self.router.add_api_route(
            "/{manager_id}/services/{service_id}",
            assign_service,
            methods=["POST"],
            response_model=ManagerServiceResponse,
            status_code=status.HTTP_201_CREATED,
        )

        def unassign_service(
            manager_id: UUID,
            service_id: UUID,
            service: self.service_dep,
            _: Annotated[CurrentAccount, Depends(require_admin)],
        ) -> None:
            service.unassign_service(manager_id, service_id)

        self.router.add_api_route(
            "/{manager_id}/services/{service_id}",
            unassign_service,
            methods=["DELETE"],
            status_code=status.HTTP_204_NO_CONTENT,
        )


manager_router = ManagerController().router
