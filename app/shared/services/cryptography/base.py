from typing import Any
from abc import ABC, abstractmethod
from pydantic import BaseModel, field_validator


class Payload(BaseModel):
    pl: str

    @field_validator("pl")
    @classmethod
    def must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("pl cannot be empty")
        return v


class CryptoKey(BaseModel):
    secret: str
    encoding: str = "utf-8"

    @field_validator("secret")
    @classmethod
    def minimum_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("The key must have at least 8 characters")
        return v


class ISerializer(ABC):
    @abstractmethod
    def serialize(self, obj: Any) -> str: ...

    @abstractmethod
    def deserialize(self, raw: str) -> Any: ...


class ICryptography(ABC):
    @abstractmethod
    def encrypt(self, obj: dict[str, Any], key: CryptoKey) -> Payload: ...

    @abstractmethod
    def decrypt(self, payload: Payload, key: CryptoKey) -> dict[str, Any]: ...


class BaseCryptography(ICryptography):
    def __init__(self, serializer: ISerializer):
        self.__serializer = serializer

    def encrypt(self, obj: dict[str, Any], key: CryptoKey) -> Payload:
        raw = self.__serializer.serialize(obj)
        return self._encrypt_raw(raw, key)

    def decrypt(self, payload: Payload, key: CryptoKey) -> dict[str, Any]:
        raw = self._decrypt_raw(payload, key)
        return self.__serializer.deserialize(raw)

    @abstractmethod
    def _encrypt_raw(self, raw: str, key: CryptoKey) -> Payload: ...

    @abstractmethod
    def _decrypt_raw(self, payload: Payload, key: CryptoKey) -> str: ...
