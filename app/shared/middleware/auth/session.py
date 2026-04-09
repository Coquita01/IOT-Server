from fastapi import Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.domain.auth.security import decode_access_token
from app.shared.session.service import SessionService
from app.shared.session.exceptions import TokenBlacklistedException

bearer_scheme = HTTPBearer()


async def validate_token_not_blacklisted(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
) -> str:
    token = credentials.credentials
    session_service = SessionService()

    try:
        is_blacklisted = await session_service.is_token_blacklisted(token)
        if is_blacklisted:
            raise TokenBlacklistedException()
        return token
    finally:
        await session_service.close()


async def get_current_user_with_session(
    request: Request,
    token: str = Depends(validate_token_not_blacklisted)
) -> dict:
    payload = decode_access_token(token)
    user_id = payload.get("sub")
    token_id = payload.get("jti")

    if not user_id or not token_id:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )

    session_service = SessionService()

    try:
        session = await session_service.validate_session(user_id, token_id)
        await session_service.update_activity(user_id)

        return {
            "account_id": user_id,
            "email": session.email,
            "account_type": session.account_type,
            "is_master": session.is_master,
            "token_id": token_id,
        }
    finally:
        await session_service.close()
