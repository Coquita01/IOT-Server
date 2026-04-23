import base64
import json
import logging
import secrets
from datetime import datetime, timezone
from typing import Annotated, Any, Optional
from uuid import UUID, uuid4

from fastapi import Depends

from app.config import settings

from .exceptions import (
    InvalidEntityIdException,
    InvalidKeySessionException,
    InvalidMetadataException,
    InvalidTagException,
    SessionAlreadyExistsException,
    SessionNotFoundException,
)
from .models import (
    EntitySessionData,
    EntitySessionResponse,
    SessionData,
    SessionTokens,
)
from .repository import SessionRepository
from .security import JWEHandler


logger = logging.getLogger(__name__)

_KEY_SESSION_EXPECTED_BYTES = 32


class SessionService:
    def __init__(
        self,
        valkey_url: Optional[str] = None,
        encryption_key: Optional[str] = None,
    ):
        self._repository = SessionRepository(valkey_url or settings.VALKEY_URL)
        self._jwe_handler = JWEHandler(encryption_key or settings.ENCRYPTION_KEY)

    async def close(self) -> None:
        await self._repository.close()

    # ==============================================================
    # Entity session API (per-key encryption flow)
    # ==============================================================

    async def check_active_session(self, entity_id: UUID) -> bool:
        entity_id_str = self._validate_entity_id(entity_id)
        return await self._repository.entity_session_exists(entity_id_str)

    async def create_entity_session(
        self,
        entity_id: UUID,
        key_session: str,
        ip_address: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> EntitySessionResponse:
        entity_id_str = self._validate_entity_id(entity_id)
        self._validate_key_session(key_session)
        self._validate_ip_address(ip_address)
        safe_metadata = self._validate_metadata(metadata)

        if await self._repository.entity_session_exists(entity_id_str):
            raise SessionAlreadyExistsException()

        session_id = secrets.token_urlsafe(32)
        now = datetime.now(timezone.utc)

        session_data = EntitySessionData(
            session_id=session_id,
            entity_id=entity_id_str,
            key_session=key_session,
            ip_address=ip_address,
            metadata=safe_metadata,
            created_at=now,
            last_activity=now,
        )

        await self._repository.store_entity_session(
            session_data=session_data,
            ttl_seconds=settings.SESSION_TTL_SECONDS,
        )

        logger.info(
            "Entity session created: entity_id=%s metadata_keys=%d",
            entity_id_str,
            len(safe_metadata),
        )

        return EntitySessionResponse(session_id=session_id)

    async def process_encrypted_request(
        self,
        session_id: str,
        tag: str,
        payload: str,
    ) -> str:
        if not session_id or not tag or not payload:
            raise InvalidTagException()

        session_data = await self._repository.get_entity_session_by_id(session_id)
        if not session_data:
            raise SessionNotFoundException()

        is_valid = JWEHandler.verify_hmac(
            session_id=session_id,
            payload=payload,
            tag=tag,
            key_session=session_data.key_session,
        )
        if not is_valid:
            logger.warning(
                "HMAC verification failed: session_id=%s entity_id=%s",
                session_id,
                session_data.entity_id,
            )
            raise InvalidTagException()

        await self._repository.touch_entity_session(session_data)

        logger.info(
            "Encrypted request verified: session_id=%s entity_id=%s",
            session_id,
            session_data.entity_id,
        )

        return session_data.key_session

    async def invalidate_entity_session(self, entity_id: UUID) -> None:
        entity_id_str = self._validate_entity_id(entity_id)
        await self._repository.delete_entity_session(entity_id_str)
        logger.info("Entity session invalidated: entity_id=%s", entity_id_str)

    # ==============================================================
    # Validation helpers
    # ==============================================================

    @staticmethod
    def _validate_entity_id(entity_id: UUID) -> str:
        if isinstance(entity_id, UUID):
            return str(entity_id)
        try:
            return str(UUID(str(entity_id)))
        except (ValueError, TypeError):
            raise InvalidEntityIdException()

    @staticmethod
    def _validate_key_session(key_session: str) -> None:
        if not key_session:
            raise InvalidKeySessionException("key_session cannot be empty")
        try:
            key_bytes = base64.urlsafe_b64decode(key_session)
        except Exception:
            raise InvalidKeySessionException("key_session must be valid urlsafe base64")

        if len(key_bytes) != _KEY_SESSION_EXPECTED_BYTES:
            raise InvalidKeySessionException(
                f"key_session must decode to {_KEY_SESSION_EXPECTED_BYTES} bytes"
            )

    @staticmethod
    def _validate_ip_address(ip_address: str) -> None:
        if not ip_address or not ip_address.strip():
            raise InvalidEntityIdException()

    @staticmethod
    def _validate_metadata(
        metadata: Optional[dict[str, Any]],
    ) -> dict[str, Any]:
        if metadata is None:
            return {}

        if not isinstance(metadata, dict):
            raise InvalidMetadataException("metadata must be a dict")

        if len(metadata) > settings.METADATA_MAX_KEYS:
            raise InvalidMetadataException(
                f"metadata cannot have more than {settings.METADATA_MAX_KEYS} keys"
            )

        forbidden = set(metadata.keys()) & settings.METADATA_FORBIDDEN_KEYS
        if forbidden:
            raise InvalidMetadataException(
                f"metadata contains forbidden keys: {sorted(forbidden)}"
            )

        try:
            serialized = json.dumps(metadata)
        except (TypeError, ValueError):
            raise InvalidMetadataException("metadata must be JSON-serializable")

        if len(serialized.encode("utf-8")) > settings.METADATA_MAX_SIZE_BYTES:
            raise InvalidMetadataException(
                f"metadata exceeds {settings.METADATA_MAX_SIZE_BYTES} bytes"
            )

        return metadata

    # ==============================================================
    # Legacy user session API (JWT-based, kept for existing auth flow)
    # ==============================================================

    async def create_session_with_tokens(
        self,
        user_id: str,
        claims: dict[str, Any],
        request_info: dict[str, str],
    ) -> SessionTokens:
        await self._repository.delete_session(user_id)

        token_id = str(uuid4())
        refresh_token = secrets.token_urlsafe(32)

        access_token = self._jwe_handler.encrypt(
            claims={**claims, "jti": token_id},
            ttl_minutes=30,
        )

        now = datetime.now(timezone.utc)
        session_data = SessionData(
            user_id=user_id,
            token_id=token_id,
            refresh_token=refresh_token,
            email=claims.get("email", ""),
            account_type=claims.get("type", ""),
            is_master=claims.get("is_master", False),
            ip_address=request_info.get("ip_address", "unknown"),
            user_agent=request_info.get("user_agent", "unknown"),
            created_at=now,
            last_activity=now,
        )

        await self._repository.store_session(
            user_id=user_id,
            session_data=session_data,
            ttl_seconds=settings.SESSION_TTL_SECONDS,
        )

        return SessionTokens(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="Bearer",
        )

    async def check_rate_limit(self, ip_address: str, max_attempts: int = 3) -> bool:
        return await self._repository.is_rate_limited(ip_address, max_attempts)

    async def increment_rate_limit(
        self,
        ip_address: str,
        max_attempts: int = 3,
        window_seconds: int = 900,
    ) -> int:
        return await self._repository.increment_rate_limit(
            ip_address,
            window_seconds,
        )

    async def reset_rate_limit(self, ip_address: str) -> None:
        await self._repository.reset_rate_limit(ip_address)

    async def get_session(self, user_id: str) -> Optional[SessionData]:
        return await self._repository.get_session(user_id)


def get_session_service() -> SessionService:
    return SessionService()


SessionServiceDep = Annotated[SessionService, Depends(get_session_service)]
