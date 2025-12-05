"""
Global pytest configuration and fixtures.
This file contains shared fixtures and configuration for all tests.
"""
import os
import pytest
from typing import Dict, Any, Generator
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
import time

from tests.utils.firebase_mock import FirebaseMock
from app.share.jwt.domain.payload import UserPayload
from tests.fixtures.workspace_data import (
    WORKSPACE_TEST_DATA, 
    WORKSPACE_CREATE_DATA,
    WORKSPACE_RESPONSE_DATA,
    WORKSPACE_SHARE_DATA,
    WORKSPACE_GUEST_DATA,
    create_workspace_data,
    create_workspace_create_data,
    create_workspace_response_data,
    create_multiple_workspaces
)
from tests.fixtures.user_data import (
    USER_TEST_DATA,
    AUTH_TEST_DATA,
    JWT_PAYLOAD_DATA,
    create_user_data,
    create_user_payload,
    create_multiple_users
)
from tests.utils.test_client import ClientHelper, DatabaseHelper

# Set test environment variables
os.environ["TESTING"] = "true"
os.environ["SKIP_FIREBASE_INIT"] = "true"
os.environ["FIREBASE_DATABASE_URL"] = "https://test-project.firebaseio.com/"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["JWT_ALGORITHM"] = "HS256"


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup test environment configuration."""
    # Set additional test environment variables
    os.environ["LOG_LEVEL"] = "DEBUG"
    os.environ["ENVIRONMENT"] = "test"
    
    yield
    
    # Cleanup after all tests
    pass


@pytest.fixture
def firebase_mock():
    """Provide a Firebase mock instance for database mocking."""
    mock = FirebaseMock()
    
    # Reset mock state before each test
    mock.reset()
    
    # Patch Firebase initialization to use mock
    with patch('app.share.firebase.FirebaseInitializer.initialize'):
        with patch('firebase_admin.db.reference', return_value=mock.reference()):
            yield mock


@pytest.fixture
def test_client(firebase_mock):
    """Provide a test client for FastAPI testing."""
    # Import here to avoid circular imports and ensure environment is set
    from app import app
    
    # Create test client with mocked Firebase
    with patch('firebase_admin.db.reference', return_value=firebase_mock.reference()):
        client = TestClient(app)
        yield client


@pytest.fixture
def authenticated_user():
    """Provide an authenticated user payload for testing."""
    return UserPayload(
        uid="test_user_id",
        email="test@example.com",
        username="testuser",
        phone=None,
        rol="client",  # Use correct enum value
        exp=time.time() + 3600  # Expires in 1 hour
    )


@pytest.fixture
def admin_user():
    """Provide an admin user payload for testing."""
    return UserPayload(
        uid="admin_user_id",
        email="admin@example.com",
        username="adminuser",
        phone=None,
        rol="ADMIN",
        exp=time.time() + 3600  # Expires in 1 hour
    )


@pytest.fixture
def guest_user():
    """Provide a guest user payload for testing."""
    return UserPayload(
        uid="guest_user_id",
        email="guest@example.com",
        username="guestuser",
        phone=None,
        rol="GUEST",
        exp=time.time() + 3600  # Expires in 1 hour
    )


@pytest.fixture
def mock_jwt_token(authenticated_user):
    """Provide a mock JWT token for authentication testing."""
    def _create_mock_token(user_payload: UserPayload = None):
        if user_payload is None:
            user_payload = authenticated_user
        
        # Mock the JWT verification to return the user payload
        with patch('app.share.jwt.infrastructure.verify_access_token.verify_access_token') as mock_verify:
            mock_verify.return_value = user_payload
            yield mock_verify
    
    return _create_mock_token


@pytest.fixture
def mock_admin_token(admin_user):
    """Provide a mock admin JWT token for admin authentication testing."""
    def _create_mock_admin_token(user_payload: UserPayload = None):
        if user_payload is None:
            user_payload = admin_user
        
        # Mock the admin JWT verification to return the admin user payload
        with patch('app.share.jwt.infrastructure.verify_access_token.verify_access_admin_token') as mock_verify:
            mock_verify.return_value = user_payload
            yield mock_verify
    
    return _create_mock_admin_token


@pytest.fixture
def workspace_data():
    """Provide workspace test data fixtures."""
    return WORKSPACE_TEST_DATA


@pytest.fixture
def workspace_create_data():
    """Provide workspace creation test data fixtures."""
    return WORKSPACE_CREATE_DATA


@pytest.fixture
def workspace_response_data():
    """Provide workspace response test data fixtures."""
    return WORKSPACE_RESPONSE_DATA


@pytest.fixture
def workspace_share_data():
    """Provide workspace sharing test data fixtures."""
    return WORKSPACE_SHARE_DATA


@pytest.fixture
def workspace_guest_data():
    """Provide workspace guest management test data fixtures."""
    return WORKSPACE_GUEST_DATA


@pytest.fixture
def user_data():
    """Provide user test data fixtures."""
    return USER_TEST_DATA


@pytest.fixture
def auth_data():
    """Provide authentication test data fixtures."""
    return AUTH_TEST_DATA


@pytest.fixture
def jwt_payload_data():
    """Provide JWT payload test data fixtures."""
    return JWT_PAYLOAD_DATA


@pytest.fixture
def workspace_factory():
    """Provide workspace data factory functions."""
    return {
        'create_workspace': create_workspace_data,
        'create_workspace_create': create_workspace_create_data,
        'create_workspace_response': create_workspace_response_data,
        'create_multiple_workspaces': create_multiple_workspaces
    }


@pytest.fixture
def user_factory():
    """Provide user data factory functions."""
    return {
        'create_user': create_user_data,
        'create_user_payload': create_user_payload,
        'create_multiple_users': create_multiple_users
    }


@pytest.fixture
def api_client(test_client):
    """Provide API client helper for testing."""
    return ClientHelper(test_client)


@pytest.fixture
def firebase_auth_mock(authenticated_user):
    """Mock Firebase Auth for user authentication."""
    from firebase_admin import auth
    from app.share.users.domain.model.user import UserData
    
    # Create a mock user record
    class MockUserRecord:
        def __init__(self, user_payload):
            self.uid = user_payload.uid
            self.email = user_payload.email
            self.display_name = user_payload.username
            self.phone_number = user_payload.phone
            self.custom_claims = {"rol": user_payload.rol}
    
    def mock_get_user(uid):
        if uid == authenticated_user.uid:
            return MockUserRecord(authenticated_user)
        # For other users created in tests
        return MockUserRecord(UserPayload(
            uid=uid,
            email=f"{uid}@test.com",
            username=uid,
            phone=None,
            rol="client",  # Use correct enum value
            exp=time.time() + 3600
        ))
    
    with patch.object(auth, 'get_user', side_effect=mock_get_user):
        yield


@pytest.fixture
def db_helper(firebase_mock, authenticated_user, firebase_auth_mock):
    """Provide database helper for testing."""
    helper = DatabaseHelper(firebase_mock)
    # Automatically setup the authenticated user
    helper.setup_authenticated_user(authenticated_user)
    return helper