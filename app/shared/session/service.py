import secrets
from datetime import datetime, timezone
from uuid import uuid4

from app.shared.session.repository import SessionRepository
from app.shared.session.models import SessionData
from app.shared.session.exceptions import (
    SessionNotFoundException,
    InvalidRefreshTokenException,
    RateLimitExceededException,
)
from app.config import settings


class SessionService:
    def __init__(self):
        self.repository = SessionRepository()

    async def create_session(
        self,
        user_id: str,
        email: str,
        account_type: str,
        is_master: bool,
        ip_address: str,
        user_agent: str,
    ) -> tuple[str, str]:
        await self.repository.delete_session(user_id)

        token_id = str(uuid4())
        refresh_token = secrets.token_urlsafe(32)
        now = datetime.now(timezone.utc)

        session = SessionData(
            user_id=user_id,
            token_id=token_id,
            refresh_token=refresh_token,
            email=email,
            account_type=account_type,
            is_master=is_master,
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=now,
            last_activity=now,
        )

        await self.repository.store_session(session)

        return token_id, refresh_token

    async def validate_session(self, user_id: str, token_id: str) -> SessionData:
        session = await self.repository.get_session(user_id)

        if not session:
            raise SessionNotFoundException()

        if session.token_id != token_id:
            raise SessionNotFoundException()

        return session

    async def update_activity(self, user_id: str) -> None:
        await self.repository.update_last_activity(user_id)

    async def destroy_session(
        self, user_id: str, access_token: str, expires_in: int
    ) -> None:
        await self.repository.delete_session(user_id)
        await self.repository.blacklist_token(access_token, expires_in)

    async def validate_refresh_token(self, refresh_token: str) -> str:
        user_id = await self.repository.get_user_by_refresh_token(refresh_token)

        if not user_id:
            raise InvalidRefreshTokenException()

        return user_id

    async def rotate_refresh_token(
        self,
        user_id: str,
        old_refresh_token: str,
        ip_address: str,
        user_agent: str,
    ) -> tuple[str, str]:
        session = await self.repository.get_session(user_id)

        if not session:
            raise SessionNotFoundException()

        if session.refresh_token != old_refresh_token:
            raise InvalidRefreshTokenException()

        token_id = str(uuid4())
        new_refresh_token = secrets.token_urlsafe(32)
        now = datetime.now(timezone.utc)

        session.token_id = token_id
        session.refresh_token = new_refresh_token
        session.last_activity = now

        if settings.IP_STRICT_MODE and session.ip_address != ip_address:
            raise InvalidRefreshTokenException()

        await self.repository.store_session(session)

        return token_id, new_refresh_token

    async def check_rate_limit(self, ip_address: str) -> None:
        attempts = await self.repository.get_login_attempts(ip_address)

        if attempts >= settings.MAX_LOGIN_ATTEMPTS:
            retry_after = settings.RATE_LIMIT_WINDOW_MINUTES * 60
            raise RateLimitExceededException(retry_after)

    async def record_failed_login(self, ip_address: str) -> None:
        await self.repository.increment_login_attempts(ip_address)

    async def record_successful_login(self, ip_address: str) -> None:
        await self.repository.reset_login_attempts(ip_address)

    async def is_token_blacklisted(self, token: str) -> bool:
        return await self.repository.is_token_blacklisted(token)

    async def close(self) -> None:
        await self.repository.close()
