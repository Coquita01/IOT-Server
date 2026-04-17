import base64
import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from jose import jwe
from jose.exceptions import JWEError


class JWEHandler:
    def __init__(self, encryption_key: str):
        try:
            key_bytes = base64.b64decode(encryption_key)
        except Exception as e:
            raise ValueError(f"ENCRYPTION_KEY must be valid base64: {e}")
        
        if len(key_bytes) != 32:
            raise ValueError(
                f"ENCRYPTION_KEY must be exactly 32 bytes when decoded, got {len(key_bytes)} bytes"
            )
        
        self.encryption_key = key_bytes
    
    def encrypt(self, claims: Dict[str, Any], ttl_minutes: int = 30) -> str:
        now = datetime.now(timezone.utc)
        exp_timestamp = int((now + timedelta(minutes=ttl_minutes)).timestamp())
        iat_timestamp = int(now.timestamp())
        
        claims_with_timestamps = {
            **claims,
            "exp": exp_timestamp,
            "iat": iat_timestamp,
        }
        
        payload_json = json.dumps(claims_with_timestamps)
        
        encrypted = jwe.encrypt(
            plaintext=payload_json.encode(),
            key=self.encryption_key,
            algorithm="dir",
            encryption="A256GCM",
        )
        
        if isinstance(encrypted, bytes):
            return encrypted.decode()
        return encrypted
    
    def decrypt(self, token: str) -> Dict[str, Any]:
        decrypted = jwe.decrypt(token.encode(), self.encryption_key)
        
        try:
            claims = json.loads(decrypted.decode())
        except json.JSONDecodeError as e:
            raise JWEError(f"Invalid JSON payload in token: {e}")
        
        # Verify expiration internally
        if not self.verify_expiration(claims):
            raise JWEError("Token has expired")
        
        return claims
    
    def verify_expiration(self, claims: Dict[str, Any]) -> bool:
        exp = claims.get("exp")
        if not exp or not isinstance(exp, (int, float)):
            return False
        
        now_timestamp = int(datetime.now(timezone.utc).timestamp())
        return exp > now_timestamp
    
    def encrypt_with_key(
        self,
        data: Dict[str, Any],
        key_session: str,
        ttl_minutes: int = 30
    ) -> str:
        try:
            key_bytes = base64.urlsafe_b64decode(key_session)
        except Exception as e:
            raise ValueError(f"key_session must be valid base64: {e}")
        
        if len(key_bytes) != 32:
            raise ValueError(f"key_session must be 32 bytes, got {len(key_bytes)}")
        
        now = datetime.now(timezone.utc)
        exp_timestamp = int((now + timedelta(minutes=ttl_minutes)).timestamp())
        iat_timestamp = int(now.timestamp())
        
        data_with_timestamps = {
            **data,
            "exp": exp_timestamp,
            "iat": iat_timestamp,
        }
        
        payload_json = json.dumps(data_with_timestamps)
        
        encrypted = jwe.encrypt(
            plaintext=payload_json.encode(),
            key=key_bytes,
            algorithm="dir",
            encryption="A256GCM",
        )
        
        if isinstance(encrypted, bytes):
            return encrypted.decode()
        return encrypted
    
    def decrypt_with_key(self, token: str, key_session: str) -> Dict[str, Any]:
        try:
            key_bytes = base64.urlsafe_b64decode(key_session)
        except Exception as e:
            raise JWEError(f"Invalid key_session: {e}")
        
        if len(key_bytes) != 32:
            raise JWEError(f"key_session must be 32 bytes, got {len(key_bytes)}")
        
        try:
            decrypted = jwe.decrypt(token.encode(), key_bytes)
        except Exception as e:
            raise JWEError(f"Decryption failed: {e}")
        
        try:
            data = json.loads(decrypted.decode())
        except json.JSONDecodeError as e:
            raise JWEError(f"Invalid JSON payload: {e}")
        
        if not self.verify_expiration(data):
            raise JWEError("Token has expired")
        
        return data
    
    @staticmethod
    def compute_hmac(session_id: str, payload: str, key_session: str) -> str:
        try:
            key_bytes = base64.urlsafe_b64decode(key_session)
        except Exception as e:
            raise ValueError(f"Invalid key_session for HMAC: {e}")
        
        message = f"{session_id}:{payload}".encode('utf-8')
        signature = hmac.new(key_bytes, message, hashlib.sha256).digest()
        
        return base64.urlsafe_b64encode(signature).decode().rstrip('=')
    
    @staticmethod
    def verify_hmac(
        session_id: str,
        payload: str,
        tag: str,
        key_session: str
    ) -> bool:
        import secrets
        
        expected_tag = JWEHandler.compute_hmac(session_id, payload, key_session)
        return secrets.compare_digest(tag, expected_tag)
