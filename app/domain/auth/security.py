from datetime import datetime, timedelta, timezone
from uuid import uuid4

import bcrypt
from jose import jwe, JWSError
from fastapi import HTTPException, status

from app.config import settings


def verify_password(plain_password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), password_hash.encode())


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def create_access_token(data: dict, token_id: str | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    
    if token_id is None:
        token_id = str(uuid4())
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "jti": token_id,
    })
    
    import json
    payload_json = json.dumps(to_encode, default=str)
    
    if settings.USE_ENCRYPTED_JWT:
        encrypted = jwe.encrypt(
            plaintext=payload_json.encode(),
            key=settings.ENCRYPTION_KEY.encode()[:32],
            algorithm="dir",
            encryption="A256GCM",
        )
        return encrypted.decode() if isinstance(encrypted, bytes) else encrypted
    else:
        import jwt
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    try:
        if settings.USE_ENCRYPTED_JWT:
            decrypted = jwe.decrypt(token.encode(), settings.ENCRYPTION_KEY.encode()[:32])
            import json
            payload = json.loads(decrypted.decode())
            
            exp = payload.get("exp")
            if exp and isinstance(exp, (int, float)):
                if datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc):
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Token has expired",
                    )
            
            return payload
        else:
            import jwt
            return jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM],
            )
    except (JWSError, Exception) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from exc