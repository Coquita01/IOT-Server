"""
Tests for per-key encryption session management.

Tests the three main processes:
1. check_active_session - verify session existence
2. create_entity_session - create session with unique key
3. process_encrypted_request - verify TAG and return key

IMPORTANT: These tests require Docker services running:
    docker-compose up -d valkey
"""

import asyncio
import base64
import secrets
from datetime import datetime, timezone

import pytest
import valkey.asyncio as valkey

from app.shared.session.exceptions import (
    InvalidTagException,
    SessionNotFoundException,
)
from app.shared.session.models import EntitySessionData
from app.shared.session.repository import SessionRepository
from app.shared.session.security import JWEHandler
from app.shared.session.service import SessionService


VALKEY_TEST_URL = "valkey://localhost:6379/1"
TEST_ENCRYPTION_KEY = "MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY="


@pytest.fixture(scope="function")
async def valkey_client():
    client = await valkey.from_url(
        VALKEY_TEST_URL,
        encoding="utf-8",
        decode_responses=True,
    )
    yield client
    await client.flushdb()
    await client.aclose()


@pytest.fixture(scope="function")
async def repository(valkey_client):
    repo = SessionRepository(VALKEY_TEST_URL)
    await repo.connect()
    yield repo
    await repo.close()


@pytest.fixture(scope="function")
async def service(valkey_client):
    svc = SessionService(
        valkey_url=VALKEY_TEST_URL,
        encryption_key=TEST_ENCRYPTION_KEY,
    )
    yield svc
    await svc.close()


@pytest.fixture
def key_session():
    return base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()


@pytest.fixture
def jwe_handler():
    return JWEHandler(TEST_ENCRYPTION_KEY)


class TestCheckActiveSession:
    @pytest.mark.asyncio
    async def test_returns_false_when_no_session_exists(self, service):
        exists = await service.check_active_session("user_999")
        assert exists is False

    @pytest.mark.asyncio
    async def test_returns_true_when_session_exists(self, service, key_session):
        await service.create_entity_session(
            entity_id="user_123",
            key_session=key_session,
            ip="192.168.1.1",
            user_agent="Test Agent"
        )
        
        exists = await service.check_active_session("user_123")
        assert exists is True

    @pytest.mark.asyncio
    async def test_works_with_device_prefix(self, service, key_session):
        await service.create_entity_session(
            entity_id="device_456",
            key_session=key_session,
            ip="192.168.1.2",
            user_agent="Device Agent"
        )
        
        exists = await service.check_active_session("device_456")
        assert exists is True

    @pytest.mark.asyncio
    async def test_works_with_application_prefix(self, service, key_session):
        await service.create_entity_session(
            entity_id="application_789",
            key_session=key_session,
            ip="192.168.1.3",
            user_agent="App Agent"
        )
        
        exists = await service.check_active_session("application_789")
        assert exists is True

    @pytest.mark.asyncio
    async def test_raises_error_for_invalid_prefix(self, service):
        with pytest.raises(ValueError, match="Unknown entity type"):
            await service.check_active_session("invalid_123")

    @pytest.mark.asyncio
    async def test_multiple_entities_independent(self, service, key_session):
        await service.create_entity_session(
            entity_id="user_123",
            key_session=key_session,
            ip="192.168.1.1",
            user_agent="Test"
        )
        
        assert await service.check_active_session("user_123") is True
        assert await service.check_active_session("device_123") is False
        assert await service.check_active_session("user_456") is False


class TestCreateEntitySession:
    @pytest.mark.asyncio
    async def test_creates_session_successfully(self, service, key_session):
        result = await service.create_entity_session(
            entity_id="user_123",
            key_session=key_session,
            ip="192.168.1.1",
            user_agent="Mozilla/5.0"
        )
        
        assert result.session_id is not None
        assert len(result.session_id) > 20
        assert result.encrypted_token is not None
        assert result.key_session == key_session

    @pytest.mark.asyncio
    async def test_session_stored_in_valkey(self, service, repository, key_session):
        await service.create_entity_session(
            entity_id="user_123",
            key_session=key_session,
            ip="192.168.1.1",
            user_agent="Test"
        )
        
        session = await repository.get_entity_session("user_123", "user")
        assert session is not None
        assert session.entity_id == "user_123"
        assert session.entity_type == "user"
        assert session.key_session == key_session

    @pytest.mark.asyncio
    async def test_encrypted_token_is_valid_jwe(self, service, key_session, jwe_handler):
        result = await service.create_entity_session(
            entity_id="user_123",
            key_session=key_session,
            ip="192.168.1.1",
            user_agent="Test"
        )
        
        decrypted = jwe_handler.decrypt_with_key(result.encrypted_token, key_session)
        assert decrypted["session_id"] == result.session_id
        assert decrypted["entity_id"] == "user_123"
        assert decrypted["entity_type"] == "user"

    @pytest.mark.asyncio
    async def test_creates_unique_session_ids(self, service, key_session):
        result1 = await service.create_entity_session(
            entity_id="user_123",
            key_session=key_session,
            ip="192.168.1.1",
            user_agent="Test"
        )
        
        result2 = await service.create_entity_session(
            entity_id="user_456",
            key_session=key_session,
            ip="192.168.1.2",
            user_agent="Test"
        )
        
        assert result1.session_id != result2.session_id

    @pytest.mark.asyncio
    async def test_stores_metadata_correctly(self, service, repository, key_session):
        await service.create_entity_session(
            entity_id="device_789",
            key_session=key_session,
            ip="10.0.0.1",
            user_agent="IoT Device v1.0"
        )
        
        session = await repository.get_entity_session("device_789", "device")
        assert session.ip_address == "10.0.0.1"
        assert session.user_agent == "IoT Device v1.0"
        assert session.created_at is not None
        assert session.last_activity is not None

    @pytest.mark.asyncio
    async def test_raises_error_for_invalid_entity_prefix(self, service, key_session):
        with pytest.raises(ValueError, match="Unknown entity type"):
            await service.create_entity_session(
                entity_id="invalid_123",
                key_session=key_session,
                ip="192.168.1.1",
                user_agent="Test"
            )

    @pytest.mark.asyncio
    async def test_overwrites_existing_session(self, service, repository, key_session):
        key1 = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()
        key2 = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()
        
        result1 = await service.create_entity_session(
            entity_id="user_123",
            key_session=key1,
            ip="192.168.1.1",
            user_agent="Test"
        )
        
        result2 = await service.create_entity_session(
            entity_id="user_123",
            key_session=key2,
            ip="192.168.1.2",
            user_agent="Test 2"
        )
        
        session = await repository.get_entity_session("user_123", "user")
        assert session.session_id == result2.session_id
        assert session.key_session == key2


class TestProcessEncryptedRequest:
    @pytest.mark.asyncio
    async def test_returns_key_session_with_valid_tag(self, service, key_session, jwe_handler):
        result = await service.create_entity_session(
            entity_id="user_123",
            key_session=key_session,
            ip="192.168.1.1",
            user_agent="Test"
        )
        
        pf = "test_encrypted_payload"
        tag = jwe_handler.compute_hmac(result.session_id, pf, key_session)
        
        response = await service.process_encrypted_request(
            session_id=result.session_id,
            tag=tag,
            pf=pf
        )
        
        assert response.key_session == key_session

    @pytest.mark.asyncio
    async def test_raises_exception_for_invalid_tag(self, service, key_session, jwe_handler):
        result = await service.create_entity_session(
            entity_id="user_123",
            key_session=key_session,
            ip="192.168.1.1",
            user_agent="Test"
        )
        
        pf = "test_encrypted_payload"
        invalid_tag = "invalid_tag_here"
        
        with pytest.raises(InvalidTagException):
            await service.process_encrypted_request(
                session_id=result.session_id,
                tag=invalid_tag,
                pf=pf
            )

    @pytest.mark.asyncio
    async def test_raises_exception_for_nonexistent_session(self, service, jwe_handler):
        pf = "test_payload"
        fake_key = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()
        tag = jwe_handler.compute_hmac("nonexistent_session", pf, fake_key)
        
        with pytest.raises(SessionNotFoundException):
            await service.process_encrypted_request(
                session_id="nonexistent_session",
                tag=tag,
                pf=pf
            )

    @pytest.mark.asyncio
    async def test_tag_verification_with_different_payload_fails(self, service, key_session, jwe_handler):
        result = await service.create_entity_session(
            entity_id="user_123",
            key_session=key_session,
            ip="192.168.1.1",
            user_agent="Test"
        )
        
        pf1 = "original_payload"
        pf2 = "modified_payload"
        tag = jwe_handler.compute_hmac(result.session_id, pf1, key_session)
        
        with pytest.raises(InvalidTagException):
            await service.process_encrypted_request(
                session_id=result.session_id,
                tag=tag,
                pf=pf2
            )

    @pytest.mark.asyncio
    async def test_tag_verification_with_different_session_id_fails(self, service, key_session, jwe_handler):
        result1 = await service.create_entity_session(
            entity_id="user_123",
            key_session=key_session,
            ip="192.168.1.1",
            user_agent="Test"
        )
        
        key2 = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()
        result2 = await service.create_entity_session(
            entity_id="user_456",
            key_session=key2,
            ip="192.168.1.2",
            user_agent="Test"
        )
        
        pf = "test_payload"
        tag = jwe_handler.compute_hmac(result1.session_id, pf, key_session)
        
        with pytest.raises(InvalidTagException):
            await service.process_encrypted_request(
                session_id=result2.session_id,
                tag=tag,
                pf=pf
            )


class TestHMACFunctions:
    def test_compute_hmac_generates_signature(self, jwe_handler, key_session):
        tag = jwe_handler.compute_hmac("session_123", "payload_data", key_session)
        
        assert tag is not None
        assert len(tag) > 20
        assert isinstance(tag, str)

    def test_compute_hmac_is_deterministic(self, jwe_handler, key_session):
        tag1 = jwe_handler.compute_hmac("session_123", "payload", key_session)
        tag2 = jwe_handler.compute_hmac("session_123", "payload", key_session)
        
        assert tag1 == tag2

    def test_compute_hmac_different_for_different_inputs(self, jwe_handler, key_session):
        tag1 = jwe_handler.compute_hmac("session_123", "payload1", key_session)
        tag2 = jwe_handler.compute_hmac("session_123", "payload2", key_session)
        
        assert tag1 != tag2

    def test_verify_hmac_accepts_valid_signature(self, jwe_handler, key_session):
        session_id = "session_123"
        payload = "test_payload"
        tag = jwe_handler.compute_hmac(session_id, payload, key_session)
        
        is_valid = jwe_handler.verify_hmac(session_id, payload, tag, key_session)
        assert is_valid is True

    def test_verify_hmac_rejects_invalid_signature(self, jwe_handler, key_session):
        is_valid = jwe_handler.verify_hmac(
            "session_123",
            "payload",
            "invalid_tag",
            key_session
        )
        assert is_valid is False

    def test_verify_hmac_rejects_modified_payload(self, jwe_handler, key_session):
        tag = jwe_handler.compute_hmac("session_123", "original", key_session)
        is_valid = jwe_handler.verify_hmac("session_123", "modified", tag, key_session)
        
        assert is_valid is False


class TestEncryptDecryptWithKey:
    def test_encrypt_with_key_creates_jwe_token(self, jwe_handler, key_session):
        data = {"user_id": "123", "role": "admin"}
        token = jwe_handler.encrypt_with_key(data, key_session, ttl_minutes=30)
        
        assert isinstance(token, str)
        assert token.count(".") == 4

    def test_decrypt_with_key_recovers_data(self, jwe_handler, key_session):
        data = {"user_id": "123", "role": "admin"}
        token = jwe_handler.encrypt_with_key(data, key_session, ttl_minutes=30)
        decrypted = jwe_handler.decrypt_with_key(token, key_session)
        
        assert decrypted["user_id"] == "123"
        assert decrypted["role"] == "admin"

    def test_decrypt_requires_same_key(self, jwe_handler, key_session):
        data = {"user_id": "123"}
        token = jwe_handler.encrypt_with_key(data, key_session, ttl_minutes=30)
        
        wrong_key = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()
        
        with pytest.raises(Exception):
            jwe_handler.decrypt_with_key(token, wrong_key)

    def test_expired_token_raises_error(self, jwe_handler, key_session):
        data = {"user_id": "123"}
        token = jwe_handler.encrypt_with_key(data, key_session, ttl_minutes=-1)
        
        with pytest.raises(Exception, match="expired"):
            jwe_handler.decrypt_with_key(token, key_session)


class TestRepositoryEntitySession:
    @pytest.mark.asyncio
    async def test_store_and_retrieve_entity_session(self, repository, key_session):
        now = datetime.now(timezone.utc)
        session_data = EntitySessionData(
            session_id="session_123",
            entity_id="user_456",
            entity_type="user",
            key_session=key_session,
            ip_address="192.168.1.1",
            user_agent="Test Agent",
            created_at=now,
            last_activity=now
        )
        
        await repository.store_entity_session(
            entity_id="user_456",
            entity_type="user",
            session_data=session_data
        )
        
        retrieved = await repository.get_entity_session("user_456", "user")
        assert retrieved is not None
        assert retrieved.session_id == "session_123"
        assert retrieved.key_session == key_session

    @pytest.mark.asyncio
    async def test_get_entity_session_by_id(self, repository, key_session):
        now = datetime.now(timezone.utc)
        session_data = EntitySessionData(
            session_id="unique_session_id",
            entity_id="device_789",
            entity_type="device",
            key_session=key_session,
            ip_address="10.0.0.1",
            user_agent="IoT",
            created_at=now,
            last_activity=now
        )
        
        await repository.store_entity_session(
            entity_id="device_789",
            entity_type="device",
            session_data=session_data
        )
        
        retrieved = await repository.get_entity_session_by_id("unique_session_id")
        assert retrieved is not None
        assert retrieved.entity_id == "device_789"
        assert retrieved.entity_type == "device"

    @pytest.mark.asyncio
    async def test_get_nonexistent_session_returns_none(self, repository):
        session = await repository.get_entity_session("user_999", "user")
        assert session is None

    @pytest.mark.asyncio
    async def test_get_by_id_nonexistent_returns_none(self, repository):
        session = await repository.get_entity_session_by_id("nonexistent")
        assert session is None


class TestIntegrationFlow:
    @pytest.mark.asyncio
    async def test_complete_session_lifecycle(self, service, jwe_handler):
        key_session = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()
        
        exists_before = await service.check_active_session("user_999")
        assert exists_before is False
        
        result = await service.create_entity_session(
            entity_id="user_999",
            key_session=key_session,
            ip="192.168.1.100",
            user_agent="Integration Test"
        )
        
        exists_after = await service.check_active_session("user_999")
        assert exists_after is True
        
        pf = "confidential_encrypted_data"
        tag = jwe_handler.compute_hmac(result.session_id, pf, key_session)
        
        response = await service.process_encrypted_request(
            session_id=result.session_id,
            tag=tag,
            pf=pf
        )
        
        assert response.key_session == key_session

    @pytest.mark.asyncio
    async def test_different_entity_types_isolated(self, service, jwe_handler):
        key1 = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()
        key2 = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()
        key3 = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()
        
        user_result = await service.create_entity_session(
            "user_123", key1, "192.168.1.1", "User Agent"
        )
        device_result = await service.create_entity_session(
            "device_123", key2, "192.168.1.2", "Device Agent"
        )
        app_result = await service.create_entity_session(
            "application_123", key3, "192.168.1.3", "App Agent"
        )
        
        assert await service.check_active_session("user_123") is True
        assert await service.check_active_session("device_123") is True
        assert await service.check_active_session("application_123") is True
        
        assert user_result.key_session == key1
        assert device_result.key_session == key2
        assert app_result.key_session == key3
