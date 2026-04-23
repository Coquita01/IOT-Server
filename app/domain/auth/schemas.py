import re

from pydantic import BaseModel, ConfigDict, Field, field_validator


PASSWORD_COMPLEXITY_RE = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9])\S{8,128}$"
)


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    email: str = Field(min_length=6, max_length=254)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        email = value.strip().lower()
        if "@" not in email or email.startswith("@") or email.endswith("@"):
            raise ValueError("invalid email")
        return email


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    account_type: str
    is_master: bool = False


class ChangePasswordRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, value: str) -> str:
        password = value.strip()

        if not PASSWORD_COMPLEXITY_RE.fullmatch(password):
            raise ValueError(
                "password must include uppercase, lowercase, number and special character"
            )

        return password


class MessageResponse(BaseModel):
    message: str