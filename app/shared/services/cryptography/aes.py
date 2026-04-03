import base64
import hashlib
import os
from typing import Any
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from app.shared.services.cryptography.base import (
    BaseCryptography,
    CryptoKey,
    Payload,
)
from app.shared.services.cryptography.json_serializer import JsonSerializer


class AesCbcCryptography(BaseCryptography):
    _BLOCK_SIZE: int = 16

    def __derive_key(self, key: CryptoKey) -> bytes:
        secret = key.secret
        if len(secret) == 64:
            try:
                return bytes.fromhex(secret)
            except ValueError:
                pass
        return hashlib.sha256(secret.encode(key.encoding)).digest()

    def __apply_pkcs7_padding(self, data: bytes) -> bytes:
        padding_length = self._BLOCK_SIZE - (len(data) % self._BLOCK_SIZE)
        return data + bytes([padding_length] * padding_length)

    def __remove_pkcs7_padding(self, data: bytes) -> bytes:
        padding_length = data[-1]
        return data[:-padding_length]

    def _encrypt_raw(self, raw: str, key: CryptoKey) -> Payload:
        aes_key = self.__derive_key(key)
        iv = os.urandom(self._BLOCK_SIZE)

        cipher = Cipher(
            algorithms.AES(aes_key),
            modes.CBC(iv),
            backend=default_backend(),
        )
        encryptor = cipher.encryptor()

        padded = self.__apply_pkcs7_padding(raw.encode(key.encoding))
        ciphertext = encryptor.update(padded) + encryptor.finalize()

        iv_b64 = base64.b64encode(iv).decode("utf-8")
        ct_b64 = base64.b64encode(ciphertext).decode("utf-8")

        return Payload(pl=f"{iv_b64}:{ct_b64}")

    def _decrypt_raw(self, payload: Payload, key: CryptoKey) -> str:
        aes_key = self.__derive_key(key)

        iv_b64, ct_b64 = payload.pl.split(":", 1)

        iv = base64.b64decode(iv_b64)
        ciphertext = base64.b64decode(ct_b64)

        cipher = Cipher(
            algorithms.AES(aes_key),
            modes.CBC(iv),
            backend=default_backend(),
        )
        decryptor = cipher.decryptor()

        padded = decryptor.update(ciphertext) + decryptor.finalize()
        raw_bytes = self.__remove_pkcs7_padding(padded)

        return raw_bytes.decode(key.encoding)


def create_aes_cryptography() -> AesCbcCryptography:
    return AesCbcCryptography(serializer=JsonSerializer())


if __name__ == "__main__":
    crypto = create_aes_cryptography()

    key = CryptoKey(secret="my_super_secret_key_2026")

    data: dict[str, Any] = {
        "name": "John",
        "age": 30,
        "city": "Madrid",
        "active": True,
    }

    print(f"Original text  : {data}")

    payload = crypto.encrypt(data, key)
    print(f"Encrypted payload: {payload.pl}")

    decrypted = crypto.decrypt(payload, key)
    print(f"Decrypted text : {decrypted}")

    print(f"Data matches   : {data == decrypted}")

    print("\n--- Hex key compatibility ---")
    hex_key = CryptoKey(secret=hashlib.sha256("1234567890".encode()).hexdigest())
    payload2 = crypto.encrypt(data, hex_key)
    decrypted2 = crypto.decrypt(payload2, hex_key)
    print(f"Data matches (hex key): {data == decrypted2}")
