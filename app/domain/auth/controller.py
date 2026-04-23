from fastapi import APIRouter, HTTPException, Request, status

from app.config import settings
from app.domain.auth.schemas import (
    ChangePasswordRequest,
    LoginRequest,
    MessageResponse,
    TokenResponse,
)
from app.domain.auth.security import get_token_ttl_seconds
from app.domain.auth.service import AuthServiceDep, CurrentAccountDep
from app.shared.session.repository import SessionRepository

auth_router = APIRouter(prefix="/auth", tags=["Auth"])


@auth_router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, service: AuthServiceDep):
    return service.login(payload)


@auth_router.patch("/change-password", response_model=MessageResponse)
def change_password(
    payload: ChangePasswordRequest,
    service: AuthServiceDep,
    current: CurrentAccountDep,
):
    return service.change_password(current, payload)


@auth_router.post("/logout", response_model=MessageResponse)
async def logout(
    request: Request,
    _current: CurrentAccountDep,
):
    payload = getattr(request.state, "token_payload", None)
    if not isinstance(payload, dict):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    token_id = payload.get("jti")
    if not token_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token cannot be invalidated because it has no jti",
        )

    ttl_seconds = get_token_ttl_seconds(payload)

    repository = SessionRepository(settings.VALKEY_URL)
    try:
        if ttl_seconds > 0:
            await repository.add_to_blacklist(token_id, ttl_seconds=ttl_seconds)

        return MessageResponse(message="Logged out successfully")
    finally:
        await repository.close()

