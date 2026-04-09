import json
import redis.asyncio as redis
from datetime import datetime, timezone

from app.config import settings
from app.shared.session.models import SessionData
from app.shared.session.exceptions import SessionCreationException


class SessionRepository:
    def __init__(self):
        self.client = redis.Redis(
            host=settings.VALKEY_HOST,
            port=settings.VALKEY_PORT,
            db=settings.VALKEY_DB,
            password=settings.VALKEY_PASSWORD if settings.VALKEY_PASSWORD else None,
            decode_responses=True,
        )
        self.session_ttl = settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400
        self.access_token_ttl = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

    async def store_session(self, session: SessionData) -> None:
        session_key = f"session:user:{session.user_id}"
        refresh_key = f"refresh:{session.refresh_token}"

        try:
            await self.client.setex(
                session_key,
                self.session_ttl,
                json.dumps(session.to_dict()),
            )
            await self.client.setex(
                refresh_key,
                self.session_ttl,
                session.user_id,
            )
        except Exception as e:
            raise SessionCreationException(f"Failed to store session: {str(e)}")

    async def get_session(self, user_id: str) -> SessionData | None:
        session_key = f"session:user:{user_id}"
        data = await self.client.get(session_key)

        if not data:
            return None

        return SessionData.from_dict(json.loads(data))

    async def update_last_activity(self, user_id: str) -> None:
        session = await self.get_session(user_id)
        if not session:
            return

        session.last_activity = datetime.now(timezone.utc)
        session_key = f"session:user:{user_id}"

        await self.client.setex(
            session_key,
            self.session_ttl,
            json.dumps(session.to_dict()),
        )

    async def delete_session(self, user_id: str) -> None:
        session = await self.get_session(user_id)
        if not session:
            return

        session_key = f"session:user:{user_id}"
        refresh_key = f"refresh:{session.refresh_token}"

        await self.client.delete(session_key)
        await self.client.delete(refresh_key)

    async def get_user_by_refresh_token(self, refresh_token: str) -> str | None:
        refresh_key = f"refresh:{refresh_token}"
        return await self.client.get(refresh_key)

    async def blacklist_token(self, token: str, expires_in: int) -> None:
        blacklist_key = f"blacklist:token:{token}"
        await self.client.setex(blacklist_key, expires_in, "1")

    async def is_token_blacklisted(self, token: str) -> bool:
        blacklist_key = f"blacklist:token:{token}"
        return bool(await self.client.exists(blacklist_key))

    async def increment_login_attempts(self, ip_address: str) -> int:
        key = f"ratelimit:login:{ip_address}"
        attempts = await self.client.incr(key)

        if attempts == 1:
            await self.client.expire(key, settings.RATE_LIMIT_WINDOW_MINUTES * 60)

        return attempts

    async def get_login_attempts(self, ip_address: str) -> int:
        key = f"ratelimit:login:{ip_address}"
        attempts = await self.client.get(key)
        return int(attempts) if attempts else 0

    async def reset_login_attempts(self, ip_address: str) -> None:
        key = f"ratelimit:login:{ip_address}"
        await self.client.delete(key)

    async def close(self) -> None:
        await self.client.aclose()
