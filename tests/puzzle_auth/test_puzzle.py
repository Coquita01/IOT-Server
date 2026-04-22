
import hashlib
import hmac
import os
import secrets
import time
import pytest
from base64 import b64encode
from unittest.mock import MagicMock
from dataclasses import dataclass

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding

from app.config import settings


# ── Helpers ─────────────────────────────────────────────────────────

def get_server_key():
    return hashlib.sha256(
        (settings.SECRET_KEY + "|puzzle_v1").encode("utf-8")
    ).digest()


def encrypt_aes(plaintext: bytes, key: bytes) -> tuple[bytes, bytes]:
    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    encryptor = cipher.encryptor()
    padder = padding.PKCS7(128).padder()
    padded = padder.update(plaintext) + padder.finalize()
    ciphertext = encryptor.update(padded) + encryptor.finalize()
    return ciphertext, iv


def build_valid_puzzle(key_hex: str) -> MagicMock:
    key = bytes.fromhex(key_hex)
    server_key = get_server_key()
    r2 = os.urandom(32)
    timestamp = int(time.time()).to_bytes(8, byteorder="big")

    p2 = hmac.new(
        key + server_key,
        r2 + timestamp,
        hashlib.sha256,
    ).digest()

    plaintext = p2 + r2 + timestamp
    ciphertext, iv = encrypt_aes(plaintext, key)

    puzzle = MagicMock()
    puzzle.encrypted_payload.ciphertext = b64encode(ciphertext).decode()
    puzzle.encrypted_payload.iv = b64encode(iv).decode()
    return puzzle


def build_expired_puzzle(key_hex: str) -> MagicMock:
    key = bytes.fromhex(key_hex)
    server_key = get_server_key()
    r2 = os.urandom(32)
    timestamp = int(time.time() - 120).to_bytes(8, byteorder="big")

    p2 = hmac.new(
        key + server_key,
        r2 + timestamp,
        hashlib.sha256,
    ).digest()

    plaintext = p2 + r2 + timestamp
    ciphertext, iv = encrypt_aes(plaintext, key)

    puzzle = MagicMock()
    puzzle.encrypted_payload.ciphertext = b64encode(ciphertext).decode()
    puzzle.encrypted_payload.iv = b64encode(iv).decode()
    return puzzle


def build_wrong_key_puzzle() -> tuple[MagicMock, bytes]:
    """Retorna puzzle cifrado con clave incorrecta y la clave incorrecta."""
    wrong_key = os.urandom(32)
    server_key = get_server_key()
    r2 = os.urandom(32)
    timestamp = int(time.time()).to_bytes(8, byteorder="big")

    p2 = hmac.new(
        wrong_key + server_key,
        r2 + timestamp,
        hashlib.sha256,
    ).digest()

    plaintext = p2 + r2 + timestamp
    ciphertext, iv = encrypt_aes(plaintext, wrong_key)

    puzzle = MagicMock()
    puzzle.encrypted_payload.ciphertext = b64encode(ciphertext).decode()
    puzzle.encrypted_payload.iv = b64encode(iv).decode()
    return puzzle


def build_tampered_puzzle(key_hex: str) -> MagicMock:
    key = bytes.fromhex(key_hex)
    r2 = os.urandom(32)
    timestamp = int(time.time()).to_bytes(8, byteorder="big")
    fake_p2 = os.urandom(32)

    plaintext = fake_p2 + r2 + timestamp
    ciphertext, iv = encrypt_aes(plaintext, key)

    puzzle = MagicMock()
    puzzle.encrypted_payload.ciphertext = b64encode(ciphertext).decode()
    puzzle.encrypted_payload.iv = b64encode(iv).decode()
    return puzzle


def build_garbage_puzzle() -> MagicMock:
    puzzle = MagicMock()
    puzzle.encrypted_payload.ciphertext = b64encode(os.urandom(64)).decode()
    puzzle.encrypted_payload.iv = b64encode(os.urandom(16)).decode()
    return puzzle


# ── Mock entities ───────────────────────────────────────────────────

DEVICE_KEY_HEX = secrets.token_hex(32)
APP_KEY_HEX = secrets.token_hex(32)
FAKE_ID = "00000000-0000-0000-0000-000000000001"


@dataclass
class FakeDevice:
    id: str = FAKE_ID
    encryption_key: str | None = DEVICE_KEY_HEX


@dataclass
class FakeApplication:
    id: str = FAKE_ID
    api_key: str | None = APP_KEY_HEX


# ── Tests PuzzleVerifier (base) ─────────────────────────────────────

class TestPuzzleVerifierValid:
    """PuzzleVerifier.verify — puzzle válido."""

    def test_valid_puzzle_returns_true(self):
        from app.shared.middleware.auth.auth_rc.base import PuzzleVerifier

        verifier = PuzzleVerifier()
        key = bytes.fromhex(DEVICE_KEY_HEX)
        puzzle = build_valid_puzzle(DEVICE_KEY_HEX)

        result = verifier.verify(key, puzzle, FAKE_ID)

        assert result["valid"] is True


class TestPuzzleVerifierDecryptionFailed:
    """PuzzleVerifier.verify — clave incorrecta al descifrar."""

    def test_wrong_key_fails(self):
        from app.shared.middleware.auth.auth_rc.base import PuzzleVerifier

        verifier = PuzzleVerifier()
        correct_key = bytes.fromhex(DEVICE_KEY_HEX)
        puzzle = build_wrong_key_puzzle()  # cifrado con otra clave

        result = verifier.verify(correct_key, puzzle, FAKE_ID)

        assert result["valid"] is False
        assert result["error"] == "Authentication failed"


class TestPuzzleVerifierTimestamp:
    """PuzzleVerifier.verify — timestamp expirado."""

    def test_expired_timestamp_fails(self):
        from app.shared.middleware.auth.auth_rc.base import PuzzleVerifier

        verifier = PuzzleVerifier()
        key = bytes.fromhex(DEVICE_KEY_HEX)
        puzzle = build_expired_puzzle(DEVICE_KEY_HEX)

        result = verifier.verify(key, puzzle, FAKE_ID)

        assert result["valid"] is False
        assert result["error"] == "Authentication failed"


class TestPuzzleVerifierTampered:
    """PuzzleVerifier.verify — P2 manipulado."""

    def test_tampered_p2_fails(self):
        from app.shared.middleware.auth.auth_rc.base import PuzzleVerifier

        verifier = PuzzleVerifier()
        key = bytes.fromhex(DEVICE_KEY_HEX)
        puzzle = build_tampered_puzzle(DEVICE_KEY_HEX)

        result = verifier.verify(key, puzzle, FAKE_ID)

        assert result["valid"] is False
        assert result["error"] == "Authentication failed"


class TestPuzzleVerifierGarbage:
    """PuzzleVerifier.verify — payload basura."""

    def test_garbage_payload_fails(self):
        from app.shared.middleware.auth.auth_rc.base import PuzzleVerifier

        verifier = PuzzleVerifier()
        key = bytes.fromhex(DEVICE_KEY_HEX)
        puzzle = build_garbage_puzzle()

        result = verifier.verify(key, puzzle, FAKE_ID)

        assert result["valid"] is False
        assert result["error"] == "Authentication failed"


# ── Tests DeviceAuth ────────────────────────────────────────────────

class TestDeviceAuthValid:
    """DeviceAuth.authenticate — puzzle válido."""

    def test_valid_puzzle(self):
        from app.shared.middleware.auth.auth_rc.device import DeviceAuth

        auth = DeviceAuth()
        device = FakeDevice()
        puzzle = build_valid_puzzle(DEVICE_KEY_HEX)

        result = auth.authenticate(device, puzzle)

        assert result["valid"] is True


class TestDeviceAuthNoKey:
    """DeviceAuth.authenticate — device sin clave."""

    def test_no_key_fails(self):
        from app.shared.middleware.auth.auth_rc.device import DeviceAuth

        auth = DeviceAuth()
        device = FakeDevice(encryption_key=None)
        puzzle = build_valid_puzzle(DEVICE_KEY_HEX)

        result = auth.authenticate(device, puzzle)

        assert result["valid"] is False
        assert result["error"] == "Authentication failed"


class TestDeviceAuthWrongKey:
    """DeviceAuth.authenticate — clave incorrecta."""

    def test_wrong_key_fails(self):
        from app.shared.middleware.auth.auth_rc.device import DeviceAuth

        auth = DeviceAuth()
        device = FakeDevice()
        puzzle = build_wrong_key_puzzle()

        result = auth.authenticate(device, puzzle)

        assert result["valid"] is False
        assert result["error"] == "Authentication failed"


# ── Tests ApplicationAuth ───────────────────────────────────────────

class TestApplicationAuthValid:
    """ApplicationAuth.authenticate — puzzle válido."""

    def test_valid_puzzle(self):
        from app.shared.middleware.auth.auth_rc.application import ApplicationAuth

        auth = ApplicationAuth()
        app = FakeApplication()
        puzzle = build_valid_puzzle(APP_KEY_HEX)

        result = auth.authenticate(app, puzzle)

        assert result["valid"] is True


class TestApplicationAuthNoKey:
    """ApplicationAuth.authenticate — application sin clave."""

    def test_no_key_fails(self):
        from app.shared.middleware.auth.auth_rc.application import ApplicationAuth

        auth = ApplicationAuth()
        app = FakeApplication(api_key=None)
        puzzle = build_valid_puzzle(APP_KEY_HEX)

        result = auth.authenticate(app, puzzle)

        assert result["valid"] is False
        assert result["error"] == "Authentication failed"


class TestApplicationAuthWrongKey:
    """ApplicationAuth.authenticate — clave incorrecta."""

    def test_wrong_key_fails(self):
        from app.shared.middleware.auth.auth_rc.application import ApplicationAuth

        auth = ApplicationAuth()
        app = FakeApplication()
        puzzle = build_wrong_key_puzzle()

        result = auth.authenticate(app, puzzle)

        assert result["valid"] is False
        assert result["error"] == "Authentication failed"
