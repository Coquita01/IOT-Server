import hashlib
import hmac
import logging
import time
from base64 import b64decode
from uuid import UUID, uuid4

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings
from app.shared.session.service import SessionService
from sqlmodel import Session
from app.database.model import Administrator, Manager, User
from app.domain.user.schemas import PuzzlePayload, PuzzleRequest
from app.domain.auth.security import decode_access_token
import app.database as database_module

logger = logging.getLogger(__name__)

TIMESTAMP_WINDOW = 60  # tolerance window in seconds

 # Module-level engine reference, patched in tests
engine = None

_MODEL_MAP = {
    "administrator": Administrator,
    "manager": Manager,
    "user": User,
}


class Human(BaseHTTPMiddleware):
    """Middleware that resolves JWT Bearer tokens into account context."""

    async def dispatch(self, request: Request, call_next):
        # Asignar una sesión de base de datos a request.state.db
        db_engine = engine or database_module.engine
        session = Session(db_engine)
        request.state.db = session
        try:
            auth_header = request.headers.get("Authorization")

            if auth_header and auth_header.lower().startswith("bearer "):
                token = auth_header[7:]
                try:
                    payload = decode_access_token(token)
                    account_type = payload.get("type")
                    account_id = payload.get("sub")
                    email = payload.get("email")
                    is_master = payload.get("is_master", False)

                    model = _MODEL_MAP.get(account_type)
                    if model and account_id:
                        with Session(db_engine) as temp_session:
                            account = temp_session.get(model, UUID(account_id))
                            if account:
                                request.state.current_account = {
                                    "account_id": str(account.id),
                                    "sensitive_data_id": str(account.sensitive_data_id),
                                    "account_type": account_type,
                                    "email": email,
                                    "is_master": is_master,
                                }
                except Exception:
                    pass

            response = await call_next(request)
            return response
        finally:
            session.close()


class HumanCryptoManager:
    """Cryptographic puzzle verifier for human user authentication."""

    def __init__(self, session: Session, session_service: SessionService):
        self.session = session
        self.session_service = session_service
        self.server_key = hashlib.sha256(
            (settings.SECRET_KEY + "|puzzle_v1").encode("utf-8")
        ).digest()

    def _get_user_key(self, user: User) -> bytes | None:
        if not user.password_hash:
            return None
        # Use the first 32 bytes of the hash as AES key
        return bytes.fromhex(user.password_hash[:64])

    def _decrypt_payload(self, payload: PuzzlePayload, user_key: bytes) -> bytes:
        ciphertext = b64decode(payload.ciphertext)
        iv = b64decode(payload.iv)
        cipher = Cipher(algorithms.AES(user_key), modes.CBC(iv))
        decryptor = cipher.decryptor()
        padded = decryptor.update(ciphertext) + decryptor.finalize()
        unpadder = padding.PKCS7(128).unpadder()
        return unpadder.update(padded) + unpadder.finalize()

    async def authenticate(self, puzzle: PuzzleRequest, request_info: dict, entity: str = "user"):
        # Seleccionar el modelo según entity
        model_map = {
            "user": User,
            "admin": Administrator,
            "administrator": Administrator,
            "manager": Manager,
        }
        model = model_map.get(entity, User)
        account = self.session.get(model, puzzle.device_id)
        if not account:
            logger.warning(f"Puzzle failed: {entity} {puzzle.device_id} not found")
            return {"valid": False, "error": "Authentication failed"}

        # 2. Check if active
        if not getattr(account, "is_active", True):
            logger.warning(f"Puzzle failed: {entity} {puzzle.device_id} inactive")
            return {"valid": False, "error": "Authentication failed"}

        # 3. Active session
        session = await self.session_service.get_session(str(puzzle.device_id))
        if session:
            return {"valid": False, "error": "Authentication failed"}

        # 4. Get user_key (usa la relación sensitive_data)
        sensitive = getattr(account, "sensitive_data", None)
        if not sensitive or not sensitive.password_hash:
            logger.warning(f"Puzzle failed: {entity} {puzzle.device_id} no password_hash")
            return {"valid": False, "error": "Authentication failed"}
        user_key = bytes.fromhex(sensitive.password_hash[:64])

        # 5. Decrypt payload
        try:
            decrypted = self._decrypt_payload(puzzle.encrypted_payload, user_key)
        except Exception:
            logger.warning(f"Puzzle failed for {entity} {puzzle.device_id}: decryption failed")
            return {"valid": False, "error": "Authentication failed"}

        # 6. Split components: P2 (32) + R2 (32) + timestamp (8) = 72 bytes
        if len(decrypted) < 72:
            logger.warning(f"Puzzle failed for {entity} {puzzle.device_id}: invalid payload length")
            return {"valid": False, "error": "Authentication failed"}

        p2_received = decrypted[:32]
        r2 = decrypted[32:64]
        timestamp_bytes = decrypted[64:72]

        # 7. Verify timestamp
        ts_now = time.time()
        ts_puzzle = int.from_bytes(timestamp_bytes, byteorder="big")
        if abs(ts_puzzle - ts_now) > TIMESTAMP_WINDOW:
            logger.warning(f"Puzzle failed for {entity} {puzzle.device_id}: timestamp expired")
            return {"valid": False, "error": "Authentication failed"}

        # 8. Recalculate P2
        p2_expected = hmac.new(
            user_key + self.server_key,
            r2 + timestamp_bytes,
            hashlib.sha256,
        ).digest()

        # 9. Compare (timing-safe)
        if hmac.compare_digest(p2_received, p2_expected):
            tokens = await self.session_service.create_session_with_tokens(
                user_id=str(account.id),
                claims={
                    "sub": str(account.id),
                    "type": entity,
                    "name": getattr(account, "name", ""),
                },
                request_info=request_info
            )
            return {
                "valid": True,
                "access_token": tokens.access_token,
                "refresh_token": tokens.refresh_token,
                "token_type": tokens.token_type,
                "user_id": str(account.id),
            }
        else:
            logger.warning(f"Puzzle failed for {entity} {puzzle.device_id}: P2 mismatch")
            return {"valid": False, "error": "Authentication failed"}
