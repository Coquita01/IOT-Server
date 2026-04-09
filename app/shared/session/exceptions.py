from fastapi import HTTPException, status


class SessionNotFoundException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No active session. Please login again.",
        )


class InvalidRefreshTokenException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token.",
        )


class SessionCreationException(HTTPException):
    def __init__(self, detail: str = "Failed to create session."):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail,
        )


class TokenBlacklistedException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked.",
        )


class RateLimitExceededException(HTTPException):
    def __init__(self, retry_after: int):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many login attempts. Try again in {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)},
        )
