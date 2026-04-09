from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.domain.auth.schemas import (
    ChangePasswordRequest,
    LoginRequest,
    MessageResponse,
    RefreshTokenRequest,
    TokenResponse,
)
from app.domain.auth.service import AuthServiceDep, CurrentAccountDep

auth_router = APIRouter(prefix="/auth", tags=["Auth"])
bearer_scheme = HTTPBearer()


@auth_router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, service: AuthServiceDep):
    return await service.login(payload)


@auth_router.post("/refresh", response_model=TokenResponse)
async def refresh_token(payload: RefreshTokenRequest, service: AuthServiceDep):
    return await service.refresh(payload)


@auth_router.post("/logout", response_model=MessageResponse)
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    service: AuthServiceDep = None,
    current: CurrentAccountDep = None,
):
    token = credentials.credentials
    return await service.logout(current, token)


@auth_router.patch("/change-password", response_model=MessageResponse)
def change_password(
    payload: ChangePasswordRequest,
    service: AuthServiceDep,
    current: CurrentAccountDep,
):
    return service.change_password(current, payload)