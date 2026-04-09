from uuid import UUID
import logging

from fastapi import status
from sqlmodel import Session
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.database import engine
from app.database.model import Administrator, Manager, User
from app.domain.auth.security import decode_access_token
from app.shared.session.service import SessionService


PUBLIC_PATHS = {
    "/docs",
    "/openapi.json",
    "/redoc",
    "/api/v1/auth/login",
    "/api/v1/auth/refresh",
}

logger = logging.getLogger(__name__)


class Human(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        if path in PUBLIC_PATHS or path.startswith("/docs") or path.startswith("/redoc"):
            return await call_next(request)

        request.state.current_account = None

        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return await call_next(request)

        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid token format"},
            )

        token = auth_header.replace("Bearer ", "", 1).strip()

        session_service = SessionService()

        try:
            is_blacklisted = await session_service.is_token_blacklisted(token)
            if is_blacklisted:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Token has been revoked"},
                )

            payload = decode_access_token(token)

            raw_account_id = payload.get("sub")
            account_type = payload.get("type")
            email = payload.get("email")
            is_master = bool(payload.get("is_master", False))
            token_id = payload.get("jti")

            if not raw_account_id or not token_id:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Token is missing required fields"},
                )

            session = await session_service.validate_session(raw_account_id, token_id)
            await session_service.update_activity(raw_account_id)

            if account_type not in {"administrator", "manager", "user"}:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Invalid account type in token"},
                )

            model_map = {
                "administrator": Administrator,
                "manager": Manager,
                "user": User,
            }

            account_id = UUID(str(raw_account_id))

            with Session(engine) as db_session:
                account = db_session.get(model_map[account_type], account_id)

                if account is None:
                    return JSONResponse(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        content={"detail": "Token account does not exist"},
                    )

                if hasattr(account, "is_active") and not account.is_active:
                    return JSONResponse(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        content={"detail": "Account is inactive"},
                    )

                request.state.current_account = {
                    "account_id": str(account.id),
                    "sensitive_data_id": str(account.sensitive_data_id),
                    "account_type": account_type,
                    "email": email,
                    "is_master": is_master,
                }

        except Exception as e:
            logger.exception("Unhandled error in authentication middleware")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": str(e) if hasattr(e, "detail") and e.detail else "Invalid or expired token"},
            )
        finally:
            await session_service.close()

        return await call_next(request)