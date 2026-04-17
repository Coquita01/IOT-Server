"""Custom exceptions for session management."""

from fastapi import HTTPException, status


class SessionNotFoundException(HTTPException):
    """Raised when session is not found in Valkey."""
    
    def __init__(self, user_id: str = None):
        detail = "Session not found"
        if user_id:
            detail = f"Session not found for user {user_id}"
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
        )


class InvalidRefreshTokenException(HTTPException):
    """Raised when refresh token is invalid or expired."""
    
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )


class TokenBlacklistedException(HTTPException):
    """Raised when token is blacklisted (revoked)."""
    
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
        )


class RateLimitExceededException(HTTPException):
    """Raised when rate limit is exceeded."""
    
    def __init__(self, retry_after: int = 900):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many failed login attempts. Try again in {retry_after // 60} minutes.",
            headers={"Retry-After": str(retry_after)},
        )


class InvalidTokenException(HTTPException):
    """Raised when token cannot be decrypted or is malformed."""
    
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )


class SessionExpiredException(HTTPException):
    """Raised when session or token has expired."""
    
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired",
        )


class InvalidTagException(HTTPException):
    """Raised when HMAC tag verification fails."""
    
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid request signature (TAG verification failed)",
        )
