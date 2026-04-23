from fastapi import HTTPException, status


class SessionNotFoundException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )


class SessionAlreadyExistsException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="An active session already exists for this entity",
        )


class InvalidRefreshTokenException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )


class RateLimitExceededException(HTTPException):
    def __init__(self, retry_after: int = 900):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many failed login attempts. Try again in {retry_after // 60} minutes.",
            headers={"Retry-After": str(retry_after)},
        )


class InvalidTokenException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )


class SessionExpiredException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired",
        )


class InvalidTagException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid request signature",
        )


class InvalidEntityIdException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid entity_id format",
        )


class InvalidKeySessionException(HTTPException):
    def __init__(self, reason: str = "Invalid key_session format"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=reason,
        )


class InvalidMetadataException(HTTPException):
    def __init__(self, reason: str = "Invalid metadata"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=reason,
        )
