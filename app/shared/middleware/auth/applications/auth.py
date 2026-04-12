import hashlib
import hmac
import logging
import time
from base64 import b64decode
from uuid import UUID

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding

from app.config import settings
from app.domain.application.schemas import PuzzlePayload, PuzzleRequest

from app.shared.session.service import SessionService
from sqlmodel import Session


from app.database.model import Application

logger = logging.getLogger(__name__)

TIMESTAMP_WINDOW = 60  # segundos de tolerancia


class CryptoManager:
    """Verificador de puzzle criptográfico para autenticación de application."""

    def __init__(self, session: Session, session_service: SessionService):
        self.session = session
        self.session_service = session_service
        self.server_key = hashlib.sha256(
            (settings.SECRET_KEY + "|puzzle_v1").encode("utf-8")
        ).digest()

    def _get_api_key(self, application: Application) -> bytes | None:
        if not application.api_key:
            return None
        return bytes.fromhex(application.api_key)
    
    def _decrypt_payload(self, payload: PuzzlePayload, api_key: bytes) -> bytes:
        ciphertext = b64decode(payload.ciphertext)
        iv = b64decode(payload.iv)
        cipher = Cipher(algorithms.AES(api_key), modes.CBC(iv))
        decryptor = cipher.decryptor()
        padded = decryptor.update(ciphertext) + decryptor.finalize()
        unpadder = padding.PKCS7(128).unpadder()
        return unpadder.update(padded) + unpadder.finalize()

    async def authenticate(self, puzzle: PuzzleRequest, request_info: dict):
        # 1. Buscar application
        application = self.session.get(Application, puzzle.application_id)
        if not application:
            logger.warning(f"Puzzle failed: application {puzzle.application_id} not found")
            return {"valid": False, "error": "Authentication failed"}

        # 2. Verificar activo
        if not application.is_active:
            logger.warning(f"Puzzle failed: application {puzzle.application_id} inactive")
            return {"valid": False, "error": "Authentication failed"}

        # 3. Sesión activa
        session = await self.session_service.get_session(str(puzzle.application_id))
        if session:
            return {"valid": False, "error": "Authentication failed"}


        #4.- obtener api_key
        api_key = self._get_api_key(application)
        if not api_key:
            logger.warning(f"Puzzle failed: application {puzzle.application_id} no api_key")
            return {"valid": False, "error": "Authentication failed"}

        # 5. Descifrar payload
        try:
            decrypted = self._decrypt_payload(puzzle.encrypted_payload, api_key)
        except Exception:
            logger.warning(f"Puzzle failed for application {puzzle.application_id}: decryption failed")
            return {"valid": False, "error": "Authentication failed"}

        # 6.- Separar componentes: P2 (32) + R2 (32) + timestamp (8) = 72 bytes
        if len(decrypted) < 72:
            logger.warning(f"Puzzle failed for application {puzzle.application_id}: invalid payload length")
            return {"valid": False, "error": "Authentication failed"}

        p2_received = decrypted[:32]
        r2 = decrypted[32:64]
        timestamp_bytes = decrypted[64:72]

        # 7. Verificar timestamp
        ts_now = time.time()
        ts_puzzle = int.from_bytes(timestamp_bytes, byteorder="big")
        if abs(ts_puzzle - ts_now) > TIMESTAMP_WINDOW:
            logger.warning(f"Puzzle failed for application {puzzle.application_id}: timestamp expired")
            return {"valid": False, "error": "Authentication failed"}

        # 8. Recalcular P2
        p2_expected = hmac.new(
            api_key + self.server_key,
            r2 + timestamp_bytes,
            hashlib.sha256,
        ).digest()

        # 9. Comparar (timing-safe)
        if hmac.compare_digest(p2_received, p2_expected):
            tokens = await self.session_service.create_session_with_tokens(
                user_id=str(puzzle.application_id),
                claims={
                    "sub": str(application.id),
                    "type": "application",
                    "name": application.name,
                },
                request_info=request_info
            )
    
            return {
                "valid": True,
                "access_token": tokens.access_token,
                "refresh_token": tokens.refresh_token,
                "token_type": tokens.token_type,
                "application_id": str(application.id),
            }
        else:
            logger.warning(f"Puzzle failed for application {puzzle.application_id}: P2 mismatch")
            return {"valid": False, "error": "Authentication failed"}