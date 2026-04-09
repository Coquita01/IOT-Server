from dataclasses import dataclass
from typing import Annotated, Literal
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer
from sqlmodel import Session, select

from app.database import SessionDep
from app.database.model import SensitiveData
from app.domain.auth.schemas import (
    ChangePasswordRequest,
    LoginRequest,
    MessageResponse,
    RefreshTokenRequest,
    TokenResponse,
)
from app.domain.auth.security import (
    create_access_token,
    decode_access_token,
    verify_password,
)
from app.shared.exceptions import BadRequestException
from app.shared.session.service import SessionService
from app.config import settings


AccountType = Literal["administrator", "manager", "user"]

bearer_scheme = HTTPBearer()


@dataclass
class CurrentAccount:
    account_id: UUID
    sensitive_data_id: UUID
    account_type: AccountType
    email: str
    is_master: bool = False


class AuthService:
    def __init__(self, session: Session, request: Request):
        self.session = session
        self.request = request
        self.session_service = SessionService()

    def _resolve_account(self, sensitive_data: SensitiveData):
        if sensitive_data.administrator is not None:
            account = sensitive_data.administrator
            return account, "administrator", bool(account.is_master)

        if sensitive_data.manager is not None:
            account = sensitive_data.manager
            return account, "manager", False

        if sensitive_data.user is not None:
            account = sensitive_data.user
            return account, "user", False

        return None, None, False

    def _get_client_ip(self) -> str:
        forwarded = self.request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return self.request.client.host if self.request.client else "unknown"

    def _get_user_agent(self) -> str:
        return self.request.headers.get("User-Agent", "unknown")

    async def login(self, payload: LoginRequest) -> TokenResponse:
        ip_address = self._get_client_ip()
        await self.session_service.check_rate_limit(ip_address)

        stmt = select(SensitiveData).where(SensitiveData.email == payload.email)
        sensitive_data = self.session.exec(stmt).first()

        if sensitive_data is None:
            await self.session_service.record_failed_login(ip_address)
            raise BadRequestException("Invalid credentials")

        if not verify_password(payload.password, sensitive_data.password_hash):
            await self.session_service.record_failed_login(ip_address)
            raise BadRequestException("Invalid credentials")

        account, account_type, is_master = self._resolve_account(sensitive_data)
        if account is None or account_type is None:
            raise BadRequestException("Account has no associated profile")

        if not account.is_active:
            raise BadRequestException("Account is inactive")

        token_id, refresh_token = await self.session_service.create_session(
            user_id=str(account.id),
            email=sensitive_data.email,
            account_type=account_type,
            is_master=is_master,
            ip_address=ip_address,
            user_agent=self._get_user_agent(),
        )

        access_token = create_access_token(
            {
                "sub": str(account.id),
                "email": sensitive_data.email,
                "type": account_type,
                "is_master": is_master,
            },
            token_id=token_id,
        )

        await self.session_service.record_successful_login(ip_address)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            account_type=account_type,
            is_master=is_master,
        )

    async def refresh(self, payload: RefreshTokenRequest) -> TokenResponse:
        user_id = await self.session_service.validate_refresh_token(
            payload.refresh_token
        )

        session = await self.session_service.repository.get_session(user_id)
        
        if not session:
            from app.shared.session.exceptions import SessionNotFoundException
            raise SessionNotFoundException()

        token_id, new_refresh_token = await self.session_service.rotate_refresh_token(
            user_id=user_id,
            old_refresh_token=payload.refresh_token,
            ip_address=self._get_client_ip(),
            user_agent=self._get_user_agent(),
        )

        access_token = create_access_token(
            {
                "sub": session.user_id,
                "email": session.email,
                "type": session.account_type,
                "is_master": session.is_master,
            },
            token_id=token_id,
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            account_type=session.account_type,
            is_master=session.is_master,
        )

    async def logout(self, current: CurrentAccount, token: str) -> MessageResponse:
        try:
            payload = decode_access_token(token)
            expires_in = int(payload.get("exp", 0)) - int(
                payload.get("iat", 0)
            )
        except Exception:
            expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

        await self.session_service.destroy_session(
            user_id=str(current.account_id),
            access_token=token,
            expires_in=expires_in,
        )

        return MessageResponse(message="Logout successful")

    def change_password(
        self,
        current: CurrentAccount,
        payload: ChangePasswordRequest,
    ) -> MessageResponse:
        sensitive_data = self.session.get(SensitiveData, current.sensitive_data_id)
        if sensitive_data is None:
            raise BadRequestException("Associated account was not found")

        if not verify_password(payload.current_password, sensitive_data.password_hash):
            raise BadRequestException("Current password is incorrect")

        sensitive_data.password = payload.new_password
        self.session.add(sensitive_data)
        self.session.commit()
        self.session.refresh(sensitive_data)

        return MessageResponse(message="Password updated successfully")


def get_auth_service(session: SessionDep, request: Request) -> AuthService:
    return AuthService(session, request)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


def get_current_account_from_request(request: Request) -> CurrentAccount:
    current = getattr(request.state, "current_account", None)

    if not isinstance(current, dict):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    try:
        return CurrentAccount(
            account_id=UUID(current["account_id"]),
            sensitive_data_id=UUID(current["sensitive_data_id"]),
            account_type=current["account_type"],
            email=current["email"],
            is_master=bool(current["is_master"]),
        )
    except (KeyError, ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication context",
        ) from exc


CurrentAccountDep = Annotated[
    CurrentAccount,
    Depends(get_current_account_from_request),
]


def require_authenticated(
    _: Annotated[object, Depends(bearer_scheme)],
    current: CurrentAccountDep,
) -> CurrentAccount:
    return current


def require_admin(
    _: Annotated[object, Depends(bearer_scheme)],
    current: CurrentAccountDep,
) -> CurrentAccount:
    if current.account_type != "administrator":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator privileges are required",
        )
    return current


def require_master_admin(
    _: Annotated[object, Depends(bearer_scheme)],
    current: CurrentAccountDep,
) -> CurrentAccount:
    if current.account_type != "administrator" or not current.is_master:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Master administrator privileges are required",
        )
    return current


def require_admin_or_manager(
    _: Annotated[object, Depends(bearer_scheme)],
    current: CurrentAccountDep,
) -> CurrentAccount:
    if current.account_type not in {"administrator", "manager"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator or manager privileges are required",
        )
    return current