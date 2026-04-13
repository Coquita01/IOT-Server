from fastapi import APIRouter

from app.domain.auth.schemas import (
    ChangePasswordRequest,
    MessageResponse,
)
from app.domain.auth.service import AuthServiceDep, CurrentAccountDep

auth_router = APIRouter(prefix="/auth", tags=["Change Password"])




@auth_router.patch("/change-password", response_model=MessageResponse)
def change_password(
    payload: ChangePasswordRequest,
    service: AuthServiceDep,
    current: CurrentAccountDep,
):
    return service.change_password(current, payload)