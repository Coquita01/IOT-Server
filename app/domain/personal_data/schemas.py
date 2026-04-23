import re
from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.shared.base_domain.schemas import BaseSchemaResponse


PASSWORD_COMPLEXITY_RE = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9])\S{8,128}$"
)

CURP_RE = re.compile(
    r"^[A-Z][AEIOUX][A-Z]{2}"
    r"\d{2}(0[1-9]|1[0-2])"
    r"(0[1-9]|[12]\d|3[01])"
    r"[HM]"
    r"(AS|BC|BS|CC|CL|CM|CS|CH|DF|DG|GT|GR|HG|JC|MC|MN|MS|NT|NL|OC|PL|QT|QR|SP|SL|SR|TC|TS|TL|VZ|YN|ZS|NE)"
    r"[B-DF-HJ-NP-TV-Z]{3}"
    r"[A-Z0-9]\d$"
)

RFC_RE = re.compile(
    r"^(?:[A-Z&Ñ]{3}|[A-Z&Ñ]{4})"
    r"\d{2}(0[1-9]|1[0-2])"
    r"(0[1-9]|[12]\d|3[01])"
    r"[A-Z0-9]{3}$"
)

CURP_ALPHABET = "0123456789ABCDEFGHIJKLMNÑOPQRSTUVWXYZ"
MINIMUM_AGE = 18


def calculate_curp_check_digit(curp17: str) -> str:
    total = 0
    for index, char in enumerate(curp17):
        value = CURP_ALPHABET.index(char)
        weight = 18 - index
        total += value * weight

    digit = 10 - (total % 10)
    return "0" if digit == 10 else str(digit)


def validate_birth_date_rules(value: datetime) -> datetime:
    birth = value.date()
    today = date.today()

    if birth > today:
        raise ValueError("birth_date cannot be in the future")

    age = today.year - birth.year - (
        (today.month, today.day) < (birth.month, birth.day)
    )

    if age < MINIMUM_AGE:
        raise ValueError("user must be at least 18 years old")

    return value


class NonCriticalPersonalDataCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    first_name: str = Field(min_length=2, max_length=60)
    last_name: str = Field(min_length=2, max_length=60)
    second_last_name: str = Field(min_length=2, max_length=60)
    phone: str = Field(pattern=r"^\+?[0-9]{10,15}$")
    address: str = Field(min_length=5, max_length=150)
    city: str = Field(min_length=2, max_length=80)
    state: str = Field(min_length=2, max_length=80)
    postal_code: str
    birth_date: datetime

    @field_validator("postal_code")
    @classmethod
    def validate_postal_code(cls, value: str) -> str:
        postal_code = value.strip()

        if not re.fullmatch(r"^\d{5}$", postal_code):
            raise ValueError("postal_code must contain exactly 5 digits")

        if not 1000 <= int(postal_code) <= 99999:
            raise ValueError("postal_code must be between 01000 and 99999")

        return postal_code

    @field_validator("birth_date")
    @classmethod
    def validate_birth_date(cls, value: datetime) -> datetime:
        return validate_birth_date_rules(value)


class NonCriticalPersonalDataUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    first_name: str | None = Field(default=None, min_length=2, max_length=60)
    last_name: str | None = Field(default=None, min_length=2, max_length=60)
    second_last_name: str | None = Field(default=None, min_length=2, max_length=60)
    phone: str | None = Field(default=None, pattern=r"^\+?[0-9]{10,15}$")
    address: str | None = Field(default=None, min_length=5, max_length=150)
    city: str | None = Field(default=None, min_length=2, max_length=80)
    state: str | None = Field(default=None, min_length=2, max_length=80)
    postal_code: str | None = None
    birth_date: datetime | None = None
    is_active: bool | None = None

    @field_validator("postal_code")
    @classmethod
    def validate_postal_code(cls, value: str | None) -> str | None:
        if value is None:
            return None

        postal_code = value.strip()

        if not re.fullmatch(r"^\d{5}$", postal_code):
            raise ValueError("postal_code must contain exactly 5 digits")

        if not 1000 <= int(postal_code) <= 99999:
            raise ValueError("postal_code must be between 01000 and 99999")

        return postal_code

    @field_validator("birth_date")
    @classmethod
    def validate_birth_date(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        return validate_birth_date_rules(value)


class NonCriticalPersonalDataResponse(BaseSchemaResponse):
    first_name: str
    last_name: str
    second_last_name: str | None = None
    is_active: bool


class SensitiveDataCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    non_critical_data_id: UUID | None = None
    email: str = Field(min_length=6, max_length=254)
    password: str = Field(min_length=8, max_length=128)
    curp: str
    rfc: str

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        email = value.strip().lower()
        if "@" not in email or email.startswith("@") or email.endswith("@"):
            raise ValueError("invalid email")
        return email

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        password = value.strip()

        if not PASSWORD_COMPLEXITY_RE.fullmatch(password):
            raise ValueError(
                "password must include uppercase, lowercase, number and special character"
            )

        return password

    @field_validator("curp")
    @classmethod
    def validate_curp(cls, value: str) -> str:
        curp = value.strip().upper()

        if not CURP_RE.fullmatch(curp):
            raise ValueError("invalid CURP format")

        expected_digit = calculate_curp_check_digit(curp[:17])
        if curp[-1] != expected_digit:
            raise ValueError("invalid CURP check digit")

        return curp

    @field_validator("rfc")
    @classmethod
    def validate_rfc(cls, value: str) -> str:
        rfc = value.strip().upper()

        if not RFC_RE.fullmatch(rfc):
            raise ValueError("invalid RFC format")

        return rfc


class SensitiveDataUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    non_critical_data_id: UUID | None = None
    email: str | None = Field(default=None, min_length=6, max_length=254)
    password: str | None = Field(default=None, min_length=8, max_length=128)
    curp: str | None = None
    rfc: str | None = None

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str | None) -> str | None:
        if value is None:
            return None

        email = value.strip().lower()
        if "@" not in email or email.startswith("@") or email.endswith("@"):
            raise ValueError("invalid email")

        return email

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str | None) -> str | None:
        if value is None:
            return None

        password = value.strip()

        if not PASSWORD_COMPLEXITY_RE.fullmatch(password):
            raise ValueError(
                "password must include uppercase, lowercase, number and special character"
            )

        return password

    @field_validator("curp")
    @classmethod
    def validate_curp(cls, value: str | None) -> str | None:
        if value is None:
            return None

        curp = value.strip().upper()

        if not CURP_RE.fullmatch(curp):
            raise ValueError("invalid CURP format")

        expected_digit = calculate_curp_check_digit(curp[:17])
        if curp[-1] != expected_digit:
            raise ValueError("invalid CURP check digit")

        return curp

    @field_validator("rfc")
    @classmethod
    def validate_rfc(cls, value: str | None) -> str | None:
        if value is None:
            return None

        rfc = value.strip().upper()

        if not RFC_RE.fullmatch(rfc):
            raise ValueError("invalid RFC format")

        return rfc


class PersonalDataCreate(NonCriticalPersonalDataCreate, SensitiveDataCreate):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    sensitive_data_id: UUID | None = None


class PersonalDataUpdate(NonCriticalPersonalDataUpdate, SensitiveDataUpdate):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)