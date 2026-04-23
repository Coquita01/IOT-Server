import json
import logging
from datetime import datetime, timezone
from typing import Optional

import valkey.asyncio as valkey

from app.config import settings

from .models import EntitySessionData, SessionData


logger = logging.getLogger(__name__)


class SessionRepository:
    def __init__(self, valkey_url: str):
        self.valkey_url = valkey_url
        self.client: Optional[valkey.Valkey] = None

    async def connect(self) -> None:
        if not self.client:
            self.client = await valkey.from_url(
                self.valkey_url,
                encoding="utf-8",
                decode_responses=True,
            )

    async def close(self) -> None:
        if self.client:
            await self.client.aclose()
            self.client = None

    # ==============================================================
    # Legacy user session (JWT-based) - kept for existing auth flow
    # ==============================================================

    async def store_session(
        self,
        user_id: str,
        session_data: SessionData,
        ttl_seconds: int = settings.SESSION_TTL_SECONDS,
    ) -> None:
        await self.connect()

        key = f"session:{user_id}"
        value = session_data.model_dump_json()

        await self.client.setex(key, ttl_seconds, value)

        refresh_key = f"refresh_token:{session_data.refresh_token}"
        await self.client.setex(refresh_key, ttl_seconds, user_id)

    async def get_session(self, user_id: str) -> Optional[SessionData]:
        await self.connect()

        key = f"session:{user_id}"
        data = await self.client.get(key)

        if not data:
            return None

        try:
            session_dict = json.loads(data)
            return SessionData(**session_dict)
        except (json.JSONDecodeError, ValueError):
            await self.client.delete(key)
            return None

    async def delete_session(self, user_id: str) -> None:
        await self.connect()

        session = await self.get_session(user_id)

        key = f"session:{user_id}"
        await self.client.delete(key)

        if session:
            refresh_key = f"refresh_token:{session.refresh_token}"
            await self.client.delete(refresh_key)

    async def update_last_activity(self, user_id: str) -> None:
        await self.connect()

        session = await self.get_session(user_id)
        if session:
            session.last_activity = datetime.now(timezone.utc)

            key = f"session:{user_id}"
            remaining_ttl = await self.client.ttl(key)
            ttl = remaining_ttl if remaining_ttl > 0 else settings.SESSION_TTL_SECONDS
            await self.store_session(user_id, session, ttl_seconds=ttl)

    async def get_user_by_refresh_token(self, refresh_token: str) -> Optional[str]:
        await self.connect()

        refresh_key = f"refresh_token:{refresh_token}"
        return await self.client.get(refresh_key)

    async def increment_rate_limit(
        self,
        ip_address: str,
        window_seconds: int = 900,
    ) -> int:
        await self.connect()

        key = f"rate_limit:{ip_address}"
        count = await self.client.incr(key)

        if count == 1:
            await self.client.expire(key, window_seconds)

        return count

    async def get_rate_limit(self, ip_address: str) -> int:
        await self.connect()

        key = f"rate_limit:{ip_address}"
        count = await self.client.get(key)
        return int(count) if count else 0

    async def reset_rate_limit(self, ip_address: str) -> None:
        await self.connect()

        key = f"rate_limit:{ip_address}"
        await self.client.delete(key)

    async def is_rate_limited(self, ip_address: str, max_attempts: int = 3) -> bool:
        count = await self.get_rate_limit(ip_address)
        return count >= max_attempts

    # ==============================================================
    # Entity sessions (per-key encryption, Valkey-backed stateful)
    # ==============================================================

    async def entity_session_exists(self, entity_id: str) -> bool:
        await self.connect()
        key = f"session:{entity_id}"
        return bool(await self.client.exists(key))

    async def store_entity_session(
        self,
        session_data: EntitySessionData,
        ttl_seconds: int = settings.SESSION_TTL_SECONDS,
    ) -> None:
        await self.connect()

        entity_key = f"session:{session_data.entity_id}"
        index_key = f"session_id_index:{session_data.session_id}"
        value = session_data.model_dump_json()

        pipeline = self.client.pipeline()
        pipeline.setex(entity_key, ttl_seconds, value)
        pipeline.setex(index_key, ttl_seconds, session_data.entity_id)
        await pipeline.execute()

    async def get_entity_session(self, entity_id: str) -> Optional[EntitySessionData]:
        await self.connect()

        key = f"session:{entity_id}"
        data = await self.client.get(key)

        if not data:
            return None

        try:
            return EntitySessionData(**json.loads(data))
        except (json.JSONDecodeError, ValueError):
            logger.warning("Corrupted entity session deleted: entity_id=%s", entity_id)
            await self.client.delete(key)
            return None

    async def get_entity_session_by_id(
        self,
        session_id: str,
    ) -> Optional[EntitySessionData]:
        await self.connect()

        index_key = f"session_id_index:{session_id}"
        entity_id = await self.client.get(index_key)

        if not entity_id:
            return None

        return await self.get_entity_session(entity_id)

    async def delete_entity_session(self, entity_id: str) -> None:
        await self.connect()

        existing = await self.get_entity_session(entity_id)

        pipeline = self.client.pipeline()
        pipeline.delete(f"session:{entity_id}")
        if existing:
            pipeline.delete(f"session_id_index:{existing.session_id}")
        await pipeline.execute()

    async def touch_entity_session(self, session_data: EntitySessionData) -> None:
        await self.connect()

        session_data.last_activity = datetime.now(timezone.utc)
        entity_key = f"session:{session_data.entity_id}"

        remaining_ttl = await self.client.ttl(entity_key)
        if remaining_ttl <= 0:
            return

        await self.client.setex(
            entity_key,
            remaining_ttl,
            session_data.model_dump_json(),
        )
