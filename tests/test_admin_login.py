# Pytest test: simulate admin login using the cryptographic puzzle

import hashlib
import hmac
import os
import time
from base64 import b64encode

import pytest
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding

from app.database.model import Administrator, NonCriticalPersonalData, SensitiveData
from app.shared.middleware.auth.human.puzzle import PuzzlePayload, PuzzleRequest
from app.config import settings

API_URL = "/api/v1/administrators/login"
ADMIN_USERNAME = "admin@iot.com"
ADMIN_PASSWORD = "Admin1234!"


def _build_puzzle_payload(user_key: bytes, server_key: bytes):
    """Build the encrypted puzzle payload exactly as the backend expects."""
    # 1. Generate R2 (32 random bytes)
    r2 = os.urandom(32)

    # 2. Current timestamp as 8-byte big-endian
    ts = int(time.time())
    timestamp_bytes = ts.to_bytes(8, byteorder="big")

    # 3. Compute P2 = HMAC-SHA256(user_key + server_key, R2 + timestamp)
    p2 = hmac.new(
        user_key + server_key,
        r2 + timestamp_bytes,
        hashlib.sha256,
    ).digest()

    # 4. Plaintext = P2 (32) + R2 (32) + timestamp (8) = 72 bytes
    plaintext = p2 + r2 + timestamp_bytes

    # 5. Encrypt with AES-CBC using user_key and PKCS7 padding
    iv = os.urandom(16)
    padder = padding.PKCS7(128).padder()
    padded = padder.update(plaintext) + padder.finalize()
    cipher = Cipher(algorithms.AES(user_key), modes.CBC(iv))
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(padded) + encryptor.finalize()

    return {
        "iv": b64encode(iv).decode(),
        "ciphertext": b64encode(ciphertext).decode(),
    }


@pytest.fixture
def admin_in_db(session):
    """Create only admin record in the test database."""
    personal_data = NonCriticalPersonalData(first_name="Admin", last_name="Master")
    session.add(personal_data)
    session.flush()
    password_hash = hashlib.sha256(ADMIN_PASSWORD.encode()).hexdigest()
    sensitive_data = SensitiveData(
        non_critical_data_id=personal_data.id,
        email=ADMIN_USERNAME,
        password_hash=password_hash,
    )
    session.add(sensitive_data)
    session.flush()
    admin = Administrator(sensitive_data_id=sensitive_data.id, is_master=True)
    session.add(admin)
    session.commit()
    return admin


def test_admin_login_puzzle(client, admin_in_db):
    admin = admin_in_db
    device_id = str(admin.id)

    # Derive same keys used by the backend
    user_key = hashlib.sha256(ADMIN_PASSWORD.encode()).digest()  # 32 bytes
    server_key = hashlib.sha256(
        (settings.SECRET_KEY + "|puzzle_v1").encode("utf-8")
    ).digest()

    encrypted_payload = _build_puzzle_payload(user_key, server_key)

    login_payload = {
        "entity": "administrator",
        "payload": {
            "device_id": device_id,
            "encrypted_payload": encrypted_payload,
        },
    }

    resp = client.post(API_URL, json=login_payload)
    assert resp.status_code == 200, f"Login failed: {resp.status_code} {resp.text}"
    data = resp.json()
    assert "access_token" in data and data["access_token"], "No access_token in response"
