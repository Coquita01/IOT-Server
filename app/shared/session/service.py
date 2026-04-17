import secrets
from datetime import datetime, timezone
from typing import Dict, Optional
from uuid import uuid4

from jose.exceptions import JWEError

from app.config import settings

from .exceptions import (
    InvalidRefreshTokenException,
    InvalidTagException,
    InvalidTokenException,
    RateLimitExceededException,
    SessionExpiredException,
    SessionNotFoundException,
    TokenBlacklistedException,
)
from .models import SessionData, SessionTokens, UserData, EntitySessionData, EntitySessionResponse, EntitySessionKeyResponse
from .repository import SessionRepository
from .security import JWEHandler


class SessionService:
    def __init__(
        self,
        valkey_url: Optional[str] = None,
        encryption_key: Optional[str] = None,
    ):
        self._repository = SessionRepository(valkey_url or settings.VALKEY_URL)
        self._jwe_handler = JWEHandler(encryption_key or settings.ENCRYPTION_KEY)
    
    async def close(self):
        await self._repository.close()
    
    def _extract_entity_type(self, entity_id: str) -> str:
        if entity_id.startswith("user_"):
            return "user"
        elif entity_id.startswith("device_"):
            return "device"
        elif entity_id.startswith("application_") or entity_id.startswith("app_"):
            return "application"
        else:
            raise ValueError(f"Unknown entity type in ID: {entity_id}")
    
    async def check_active_session(self, entity_id: str) -> bool:
        entity_type = self._extract_entity_type(entity_id)
        valkey_key = f"session:{entity_type}:{entity_id}"
        return await self._repository.exists(valkey_key)
    
    async def create_entity_session(
        self,
        entity_id: str,
        key_session: str,
        ip: str,
        user_agent: str
    ) -> EntitySessionResponse:
        entity_type = self._extract_entity_type(entity_id)
        session_id = secrets.token_urlsafe(32)
        
        now = datetime.now(timezone.utc)
        session_data = EntitySessionData(
            session_id=session_id,
            entity_id=entity_id,
            entity_type=entity_type,
            key_session=key_session,
            ip_address=ip,
            user_agent=user_agent,
            created_at=now,
            last_activity=now
        )
        
        await self._repository.store_entity_session(
            entity_id=entity_id,
            entity_type=entity_type,
            session_data=session_data,
            ttl_seconds=259200
        )
        
        token_payload = {
            "session_id": session_id,
            "entity_id": entity_id,
            "entity_type": entity_type
        }
        encrypted_token = self._jwe_handler.encrypt_with_key(
            data=token_payload,
            key_session=key_session,
            ttl_minutes=30
        )
        
        return EntitySessionResponse(
            session_id=session_id,
            encrypted_token=encrypted_token,
            key_session=key_session
        )
    
    async def process_encrypted_request(
        self,
        session_id: str,
        tag: str,
        pf: str
    ) -> EntitySessionKeyResponse:
        session_data = await self._repository.get_entity_session_by_id(session_id)
        
        if not session_data:
            raise SessionNotFoundException()
        
        is_valid = self._jwe_handler.verify_hmac(
            session_id=session_id,
            payload=pf,
            tag=tag,
            key_session=session_data.key_session
        )
        
        if not is_valid:
            raise InvalidTagException()
        
        return EntitySessionKeyResponse(
            key_session=session_data.key_session
        )
    
    async def create_session_with_tokens(
        self,
        user_id: str,
        claims: Dict[str, any],
        request_info: Dict[str, str],
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
            ttl_seconds=259200,
        )
        
        return SessionTokens(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="Bearer",
        )
    
    async def validate_token(self, jwe_token: str) -> Optional[UserData]:
        try:
            claims = self._jwe_handler.decrypt(jwe_token)
        except JWEError:
            return None
        
        if not self._jwe_handler.verify_expiration(claims):
            return None
        
        token_id = claims.get("jti")
        user_id = claims.get("sub")
        
        if not token_id or not user_id:
            return None
        
        is_blacklisted = await self._repository.is_blacklisted(token_id)
        if is_blacklisted:
            return None
        
        session = await self._repository.get_session(user_id)
        if not session:
            return None
        
        if session.token_id != token_id:
            return None
        
        await self._repository.update_last_activity(user_id)
        
        return UserData(
            user_id=user_id,
            email=session.email,
            account_type=session.account_type,
            is_master=session.is_master,
            token_id=token_id,
        )
    
    async def invalidate_session(
        self,
        user_id: str,
        token_id: Optional[str] = None,
    ) -> None:
        await self._repository.delete_session(user_id)
        
        if token_id:
            await self._repository.add_to_blacklist(token_id, ttl_seconds=1800)
    
    async def rotate_refresh_token(
        self,
        refresh_token: str,
        request_info: Dict[str, str],
    ) -> Optional[SessionTokens]:
        user_id = await self._repository.get_user_by_refresh_token(refresh_token)
        if not user_id:
            return None
        
        session = await self._repository.get_session(user_id)
        if not session:
            return None
        
        if session.refresh_token != refresh_token:
            return None
        
        await self._repository.add_to_blacklist(session.token_id, ttl_seconds=1800)
        
        new_token_id = str(uuid4())
        new_refresh_token = secrets.token_urlsafe(32)
        
        claims = {
            "sub": user_id,
            "email": session.email,
            "type": session.account_type,
            "is_master": session.is_master,
            "jti": new_token_id,
        }
        new_access_token = self._jwe_handler.encrypt(claims, ttl_minutes=30)
        
        session.token_id = new_token_id
        session.refresh_token = new_refresh_token
        session.last_activity = datetime.now(timezone.utc)
        session.ip_address = request_info.get("ip_address", session.ip_address)
        session.user_agent = request_info.get("user_agent", session.user_agent)
        
        await self._repository.store_session(user_id, session, ttl_seconds=259200)
        
        return SessionTokens(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
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
    
    async def is_token_blacklisted(self, token_id: str) -> bool:
        return await self._repository.is_blacklisted(token_id)
    
    async def get_session(self, user_id: str) -> Optional[SessionData]:
        return await self._repository.get_session(user_id)
