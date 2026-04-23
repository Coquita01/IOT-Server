from uuid import UUID
from fastapi import status, Depends
from app.shared.base_domain.controller import FullCrudApiController
from app.domain.manager.schemas import ManagerResponse
from app.domain.manager.service import ManagerServiceDep
from app.shared.authorization.dependencies import require_read, require_write, require_delete
from app.shared.authorization.models import CurrentUser
from app.domain.personal_data.schemas import PersonalDataCreate, PersonalDataUpdate
from app.domain.user_roles.schemas import UserRoleResponse
from app.database.model import Manager
from app.shared.authorization.dependencies import require_oso_permission


class ManagerController(FullCrudApiController):
    prefix = "/managers"
    tags = ["Managers"]
    service_dep = ManagerServiceDep
    response_schema = ManagerResponse
    create_schema = PersonalDataCreate
    update_schema = PersonalDataUpdate

    list_dependencies = [require_read(Manager)]
    retrieve_dependencies = [require_read(Manager)]
    create_dependencies = [require_write(Manager)]
    update_dependencies = [require_write(Manager)]
    delete_dependencies = [require_delete(Manager)]

    def _register_routes(self):
        super()._register_routes()
        
        # Manager - assign user to role
        def assign_user_to_role(
            service: self.service_dep,
            user_id: UUID,
            role_id: UUID,
            current_user: CurrentUser = Depends(require_oso_permission("write", Manager)),
        ):
            return service.assign_user_to_role(current_user.account_id, user_id, role_id)
        
        self.router.add_api_route(
            "/users/{user_id}/roles/{role_id}/assign",
            assign_user_to_role,
            methods=["POST"],
            response_model=UserRoleResponse,
            status_code=status.HTTP_201_CREATED,
            dependencies=[require_write(Manager)],
        )
        
        # Manager - remove user from role
        def remove_user_from_role(
            service: self.service_dep,
            user_id: UUID,
            role_id: UUID,
            current_user: CurrentUser = Depends(require_oso_permission("write", Manager)),
        ):
            service.remove_user_from_role(current_user.account_id, user_id, role_id)
            return {"message": "User removed from role"}
        
        self.router.add_api_route(
            "/users/{user_id}/roles/{role_id}",
            remove_user_from_role,
            methods=["DELETE"],
            status_code=status.HTTP_204_NO_CONTENT,
            dependencies=[require_write(Manager)],
        )
        
        # Manager - get user roles
        def get_user_roles(
            service: self.service_dep,
            user_id: UUID,
            current_user: CurrentUser = Depends(require_oso_permission("read", Manager)),
        ):
            return service.get_user_roles(user_id)
        
        self.router.add_api_route(
            "/users/{user_id}/roles",
            get_user_roles,
            methods=["GET"],
            response_model=list[UserRoleResponse],
            dependencies=[require_read(Manager)],
        )


manager_router = ManagerController().router
