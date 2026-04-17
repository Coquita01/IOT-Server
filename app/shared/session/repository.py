import json
from datetime import datetime, timezone
from typing import Optional

import valkey.asyncio as valkey

from .models import SessionData, EntitySessionData


class SessionRepository:
    def __init__(self, valkey_url: str):
        self.valkey_url = valkey_url
        self.client: Optional[valkey.Valkey] = None
    
    async def connect(self):
        if not self.client:
            self.client = await valkey.from_url(
                self.valkey_url,
                encoding="utf-8",
                decode_responses=True,
            )
    
    async def close(self):
        if self.client:
            await self.client.aclose()
            self.client = None
    
    async def store_session(
        self,
        user_id: str,
        session_data: SessionData,
        ttl_seconds: int = 259200,
    ) -> None:
        await self.connect()
        
        key = f"session:{user_id}"
        value = session_data.model_dump_json()
        
        await self.client.setex(key, ttl_seconds, value)
        
        # Create reverse index for refresh token lookup (O(1) instead of O(n))
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
        
        # Get session to delete refresh token index
        session = await self.get_session(user_id)
        
        key = f"session:{user_id}"
        await self.client.delete(key)
        
        # Delete refresh token index
        if session:
            refresh_key = f"refresh_token:{session.refresh_token}"
            await self.client.delete(refresh_key)
    
    async def update_last_activity(self, user_id: str) -> None:
        await self.connect()
        
        session = await self.get_session(user_id)
        if session:
            session.last_activity = datetime.now(timezone.utc)
            
            # Get current TTL to avoid resetting expiration
            key = f"session:{user_id}"
            remaining_ttl = await self.client.ttl(key)
            
            # Use remaining TTL or default if key doesn't expire
            ttl = remaining_ttl if remaining_ttl > 0 else 259200
            await self.store_session(user_id, session, ttl_seconds=ttl)
    
    async def get_user_by_refresh_token(self, refresh_token: str) -> Optional[str]:
        await self.connect()
        
        # Use reverse index for O(1) lookup instead of O(n) scan
        refresh_key = f"refresh_token:{refresh_token}"
        user_id = await self.client.get(refresh_key)
        
        return user_id
    
    async def add_to_blacklist(self, token_id: str, ttl_seconds: int = 1800) -> None:
        await self.connect()
        
        key = f"blacklist:{token_id}"
        await self.client.setex(key, ttl_seconds, "1")
    
    async def is_blacklisted(self, token_id: str) -> bool:
        await self.connect()
        
        key = f"blacklist:{token_id}"
        exists = await self.client.exists(key)
        return bool(exists)
    
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
    
    async def exists(self, key: str) -> bool:
        await self.connect()
        exists = await self.client.exists(key)
        return bool(exists)
    
    async def store_entity_session(
        self,
        entity_id: str,
        entity_type: str,
        session_data: EntitySessionData,
        ttl_seconds: int = 259200,
    ) -> None:
        await self.connect()
        
        key = f"session:{entity_type}:{entity_id}"
        value = session_data.model_dump_json()
        
        await self.client.setex(key, ttl_seconds, value)
    
    async def get_entity_session(
        self,
        entity_id: str,
        entity_type: str
    ) -> Optional[EntitySessionData]:
        await self.connect()
        
        key = f"session:{entity_type}:{entity_id}"
        data = await self.client.get(key)
        
        if not data:
            return None
        
        try:
            session_dict = json.loads(data)
            return EntitySessionData(**session_dict)
        except (json.JSONDecodeError, ValueError):
            await self.client.delete(key)
            return None
    
    async def get_entity_session_by_id(
        self,
        session_id: str
    ) -> Optional[EntitySessionData]:
        await self.connect()
        
        cursor = 0
        pattern = "session:*"
        
        while True:
            cursor, keys = await self.client.scan(cursor, match=pattern, count=100)
            
            for key in keys:
                data = await self.client.get(key)
                if data:
                    try:
                        session_dict = json.loads(data)
                        if session_dict.get("session_id") == session_id:
                            return EntitySessionData(**session_dict)
                    except (json.JSONDecodeError, ValueError):
                        continue
            
            if cursor == 0:
                break
        
        return None
