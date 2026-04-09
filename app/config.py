import secrets
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    APP_NAME: str = "IoT Backend"
    DEBUG: bool = False

    SECRET_KEY: str = "change-me-in-env"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    ENCRYPTION_KEY: str = secrets.token_urlsafe(32)
    USE_ENCRYPTED_JWT: bool = True

    VALKEY_HOST: str = "localhost"
    VALKEY_PORT: int = 6379
    VALKEY_DB: int = 0
    VALKEY_PASSWORD: str | None = None

    REFRESH_TOKEN_EXPIRE_DAYS: int = 3
    MAX_LOGIN_ATTEMPTS: int = 3
    RATE_LIMIT_WINDOW_MINUTES: int = 15

    IP_STRICT_MODE: bool = False
    USER_AGENT_STRICT: bool = False
    SINGLE_USE_REFRESH: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()