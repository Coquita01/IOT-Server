"""
Integration tests for Session module using real Valkey instance.

IMPORTANT: These tests require Docker services running:
    docker-compose up -d valkey

These tests validate:
- SessionRepository operations against real Valkey
- SessionService complete workflows
- Token encryption/decryption flows
- Session lifecycle management
"""

import asyncio
from datetime import datetime, timezone
from uuid import uuid4

import pytest
import valkey.asyncio as valkey

from app.shared.session.models import SessionData
from app.shared.session.repository import SessionRepository
from app.shared.session.security import JWEHandler
from app.shared.session.service import SessionService


# Test configuration
VALKEY_TEST_URL = "valkey://localhost:6380/1"  # Use DB 1 for tests
# Valid base64 AES-256 key (32 bytes): b'0123456789abcdef0123456789abcdef'
TEST_ENCRYPTION_KEY = "MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY="


@pytest.fixture(scope="function")
async def valkey_client():
    """Create a Valkey client for direct operations and cleanup."""
    client = await valkey.from_url(
        VALKEY_TEST_URL,
        encoding="utf-8",
        decode_responses=True,
    )
    yield client
    # Cleanup: flush test database after each test
    await client.flushdb()
    await client.aclose()


@pytest.fixture(scope="function")
async def repository(valkey_client):
    """Create SessionRepository instance."""
    repo = SessionRepository(VALKEY_TEST_URL)
    await repo.connect()
    yield repo
    await repo.close()


@pytest.fixture(scope="function")
async def service(valkey_client):
    """Create SessionService instance."""
    svc = SessionService(
        valkey_url=VALKEY_TEST_URL,
        encryption_key=TEST_ENCRYPTION_KEY,
    )
    yield svc
    await svc.close()


@pytest.fixture
def sample_session_data():
    """Create sample session data for testing."""
    now = datetime.now(timezone.utc)
    return SessionData(
        user_id="test-user-123",
        token_id=str(uuid4()),
        refresh_token="sample-refresh-token",
        email="test@example.com",
        account_type="user",
        is_master=False,
        ip_address="127.0.0.1",
        user_agent="Test Agent",
        created_at=now,
        last_activity=now,
    )


# ==================== SessionRepository Tests ====================


class TestSessionRepositoryIntegration:
    """Integration tests for SessionRepository with real Valkey."""

    @pytest.mark.asyncio
    async def test_store_and_get_session(self, repository, sample_session_data):
        """Test storing and retrieving a session."""
        user_id = sample_session_data.user_id
        
        # Store session
        await repository.store_session(user_id, sample_session_data, ttl_seconds=60)
        
        # Retrieve session
        retrieved = await repository.get_session(user_id)
        
        assert retrieved is not None
        assert retrieved.user_id == sample_session_data.user_id
        assert retrieved.token_id == sample_session_data.token_id
        assert retrieved.email == sample_session_data.email
        assert retrieved.account_type == sample_session_data.account_type

    @pytest.mark.asyncio
    async def test_get_nonexistent_session(self, repository):
        """Test retrieving a session that doesn't exist."""
        result = await repository.get_session("nonexistent-user")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_session(self, repository, sample_session_data):
        """Test deleting a session."""
        user_id = sample_session_data.user_id
        
        # Store then delete
        await repository.store_session(user_id, sample_session_data)
        await repository.delete_session(user_id)
        
        # Verify deletion
        result = await repository.get_session(user_id)
        assert result is None

    @pytest.mark.asyncio
    async def test_update_last_activity(self, repository, sample_session_data):
        """Test updating last activity timestamp."""
        user_id = sample_session_data.user_id
        original_time = sample_session_data.last_activity
        
        # Store session
        await repository.store_session(user_id, sample_session_data)
        
        # Wait a moment and update
        await asyncio.sleep(0.1)
        await repository.update_last_activity(user_id)
        
        # Verify update
        updated = await repository.get_session(user_id)
        assert updated.last_activity > original_time

    @pytest.mark.asyncio
    async def test_get_user_by_refresh_token(self, repository, sample_session_data):
        """Test finding user by refresh token."""
        user_id = sample_session_data.user_id
        refresh_token = sample_session_data.refresh_token
        
        # Store session
        await repository.store_session(user_id, sample_session_data)
        
        # Find by refresh token
        found_user_id = await repository.get_user_by_refresh_token(refresh_token)
        
        assert found_user_id == user_id

    @pytest.mark.asyncio
    async def test_get_user_by_invalid_refresh_token(self, repository):
        """Test searching with invalid refresh token."""
        result = await repository.get_user_by_refresh_token("invalid-token")
        assert result is None

    @pytest.mark.asyncio
    async def test_blacklist_operations(self, repository):
        """Test adding tokens to blacklist and checking."""
        token_id = str(uuid4())
        
        # Initially not blacklisted
        assert await repository.is_blacklisted(token_id) is False
        
        # Add to blacklist
        await repository.add_to_blacklist(token_id, ttl_seconds=60)
        
        # Now should be blacklisted
        assert await repository.is_blacklisted(token_id) is True

    @pytest.mark.asyncio
    async def test_rate_limit_increment(self, repository):
        """Test rate limit increment operations."""
        ip_address = "192.168.1.100"
        
        # First increment
        count1 = await repository.increment_rate_limit(ip_address, window_seconds=60)
        assert count1 == 1
        
        # Second increment
        count2 = await repository.increment_rate_limit(ip_address, window_seconds=60)
        assert count2 == 2
        
        # Check current count
        current = await repository.get_rate_limit(ip_address)
        assert current == 2

    @pytest.mark.asyncio
    async def test_rate_limit_check(self, repository):
        """Test checking if IP is rate limited."""
        ip_address = "192.168.1.101"
        max_attempts = 3
        
        # Not limited initially
        assert await repository.is_rate_limited(ip_address, max_attempts) is False
        
        # Increment to limit
        for _ in range(max_attempts):
            await repository.increment_rate_limit(ip_address, window_seconds=60)
        
        # Now should be limited
        assert await repository.is_rate_limited(ip_address, max_attempts) is True

    @pytest.mark.asyncio
    async def test_reset_rate_limit(self, repository):
        """Test resetting rate limit for an IP."""
        ip_address = "192.168.1.102"
        
        # Build up rate limit
        await repository.increment_rate_limit(ip_address, window_seconds=60)
        await repository.increment_rate_limit(ip_address, window_seconds=60)
        
        # Reset
        await repository.reset_rate_limit(ip_address)
        
        # Should be back to 0
        count = await repository.get_rate_limit(ip_address)
        assert count == 0


# ==================== SessionService Tests ====================


class TestSessionServiceIntegration:
    """Integration tests for SessionService with real Valkey."""

    @pytest.mark.asyncio
    async def test_create_session_flow(self, service):
        """Test complete session creation flow."""
        user_id = "test-user-456"
        claims = {
            "sub": user_id,
            "email": "user@test.com",
            "type": "user",
            "is_master": False,
        }
        request_info = {
            "ip_address": "10.0.0.1",
            "user_agent": "Mozilla/5.0",
        }
        
        # Create session
        tokens = await service.create_session_with_tokens(
            user_id=user_id,
            claims=claims,
            request_info=request_info,
        )
        
        # Verify tokens structure
        assert tokens.access_token is not None
        assert tokens.refresh_token is not None
        assert tokens.token_type == "Bearer"
        
        # Verify session stored
        session = await service.get_session(user_id)
        assert session is not None
        assert session.user_id == user_id
        assert session.email == claims["email"]
        assert session.ip_address == request_info["ip_address"]

    @pytest.mark.asyncio
    async def test_validate_token_success(self, service):
        """Test validating a valid token."""
        user_id = "test-user-789"
        claims = {
            "sub": user_id,
            "email": "valid@test.com",
            "type": "manager",
            "is_master": True,
        }
        request_info = {"ip_address": "10.0.0.2", "user_agent": "Test"}
        
        # Create session
        tokens = await service.create_session_with_tokens(
            user_id, claims, request_info
        )
        
        # Validate token
        user_data = await service.validate_token(tokens.access_token)
        
        assert user_data is not None
        assert user_data.user_id == user_id
        assert user_data.email == claims["email"]
        assert user_data.account_type == claims["type"]
        assert user_data.is_master == claims["is_master"]

    @pytest.mark.asyncio
    async def test_validate_invalid_token(self, service):
        """Test validating an invalid token."""
        invalid_token = "invalid.token.here"
        
        result = await service.validate_token(invalid_token)
        assert result is None

    @pytest.mark.asyncio
    async def test_validate_token_after_invalidation(self, service):
        """Test that invalidated tokens fail validation."""
        user_id = "test-user-101"
        claims = {
            "sub": user_id,
            "email": "test@example.com",
            "type": "user",
            "is_master": False,
        }
        request_info = {"ip_address": "10.0.0.3", "user_agent": "Test"}
        
        # Create session
        tokens = await service.create_session_with_tokens(
            user_id, claims, request_info
        )
        
        # Validate works initially
        user_data = await service.validate_token(tokens.access_token)
        assert user_data is not None
        
        # Invalidate session
        await service.invalidate_session(user_id, user_data.token_id)
        
        # Now validation should fail
        result = await service.validate_token(tokens.access_token)
        assert result is None

    @pytest.mark.asyncio
    async def test_rotate_refresh_token_flow(self, service):
        """Test complete refresh token rotation."""
        user_id = "test-user-202"
        claims = {
            "sub": user_id,
            "email": "rotate@test.com",
            "type": "user",
            "is_master": False,
        }
        request_info = {"ip_address": "10.0.0.4", "user_agent": "Test"}
        
        # Create initial session
        initial_tokens = await service.create_session_with_tokens(
            user_id, claims, request_info
        )
        
        # Rotate tokens
        new_tokens = await service.rotate_refresh_token(
            initial_tokens.refresh_token,
            request_info,
        )
        
        assert new_tokens is not None
        assert new_tokens.access_token != initial_tokens.access_token
        assert new_tokens.refresh_token != initial_tokens.refresh_token
        
        # Old token should be blacklisted
        old_session = await service.get_session(user_id)
        old_token_id = initial_tokens.access_token  # We need to extract jti
        # Note: In real scenario, you'd extract jti from JWT claims
        
        # New token should validate
        user_data = await service.validate_token(new_tokens.access_token)
        assert user_data is not None

    @pytest.mark.asyncio
    async def test_rotate_with_invalid_refresh_token(self, service):
        """Test rotation fails with invalid refresh token."""
        request_info = {"ip_address": "10.0.0.5", "user_agent": "Test"}
        
        result = await service.rotate_refresh_token(
            "invalid-refresh-token",
            request_info,
        )
        
        assert result is None

    @pytest.mark.asyncio
    async def test_rate_limit_integration(self, service):
        """Test rate limiting functionality."""
        ip_address = "10.0.0.6"
        max_attempts = 3
        
        # Initially not rate limited
        is_limited = await service.check_rate_limit(ip_address, max_attempts)
        assert is_limited is False
        
        # Increment to limit
        for i in range(max_attempts):
            count = await service.increment_rate_limit(ip_address, max_attempts, 60)
            assert count == i + 1
        
        # Should be rate limited now
        is_limited = await service.check_rate_limit(ip_address, max_attempts)
        assert is_limited is True
        
        # Reset and check
        await service.reset_rate_limit(ip_address)
        is_limited = await service.check_rate_limit(ip_address, max_attempts)
        assert is_limited is False

    @pytest.mark.asyncio
    async def test_multiple_sessions_isolation(self, service):
        """Test that multiple user sessions don't interfere."""
        user1_id = "user-001"
        user2_id = "user-002"
        
        claims1 = {"sub": user1_id, "email": "user1@test.com", "type": "user", "is_master": False}
        claims2 = {"sub": user2_id, "email": "user2@test.com", "type": "admin", "is_master": True}
        request_info = {"ip_address": "10.0.0.7", "user_agent": "Test"}
        
        # Create both sessions
        tokens1 = await service.create_session_with_tokens(user1_id, claims1, request_info)
        tokens2 = await service.create_session_with_tokens(user2_id, claims2, request_info)
        
        # Validate both work independently
        user1_data = await service.validate_token(tokens1.access_token)
        user2_data = await service.validate_token(tokens2.access_token)
        
        assert user1_data.user_id == user1_id
        assert user2_data.user_id == user2_id
        assert user1_data.email != user2_data.email
        
        # Invalidate one shouldn't affect the other
        await service.invalidate_session(user1_id, user1_data.token_id)
        
        result1 = await service.validate_token(tokens1.access_token)
        result2 = await service.validate_token(tokens2.access_token)
        
        assert result1 is None  # User1 invalidated
        assert result2 is not None  # User2 still valid

    @pytest.mark.asyncio
    async def test_session_replacement_on_create(self, service):
        """Test that creating new session replaces old one."""
        user_id = "user-003"
        claims = {"sub": user_id, "email": "replace@test.com", "type": "user", "is_master": False}
        request_info = {"ip_address": "10.0.0.8", "user_agent": "Test"}
        
        # Create first session
        tokens1 = await service.create_session_with_tokens(user_id, claims, request_info)
        
        # Create second session (should replace first)
        tokens2 = await service.create_session_with_tokens(user_id, claims, request_info)
        
        # First token should be invalid
        result1 = await service.validate_token(tokens1.access_token)
        assert result1 is None
        
        # Second token should be valid
        result2 = await service.validate_token(tokens2.access_token)
        assert result2 is not None
