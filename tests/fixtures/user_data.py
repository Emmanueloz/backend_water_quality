"""
User test data fixtures and factories.
"""
from typing import Dict, Any, List
import time
import uuid
from app.share.jwt.domain.payload import UserPayload


# Static test data for users
USER_TEST_DATA = {
    "owner_user": {
        "uid": "test_user_id",
        "email": "owner@test.com",
        "username": "testowner",
        "phone": "+1234567890",
        "rol": "USER"
    },
    "guest_user": {
        "uid": "guest_user_id",
        "email": "guest@test.com",
        "username": "testguest",
        "phone": None,
        "rol": "GUEST"
    },
    "admin_user": {
        "uid": "admin_user_id",
        "email": "admin@test.com",
        "username": "testadmin",
        "phone": "+1987654321",
        "rol": "ADMIN"
    },
    "manager_user": {
        "uid": "manager_user_id",
        "email": "manager@test.com",
        "username": "testmanager",
        "phone": None,
        "rol": "USER"
    },
    "invalid_user": {
        "uid": "",  # Invalid: empty uid
        "email": "invalid-email",  # Invalid email format
        "username": "",  # Invalid: empty username
        "phone": "invalid-phone",
        "rol": "INVALID_ROLE"
    }
}

# Authentication test data
AUTH_TEST_DATA = {
    "valid_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.test.token",
    "expired_token": "expired.jwt.token",
    "invalid_token": "invalid.token.format",
    "malformed_token": "malformed",
    "empty_token": "",
    "bearer_token": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.test.token"
}

# JWT payload test data
JWT_PAYLOAD_DATA = {
    "valid_payload": {
        "uid": "test_user_id",
        "email": "test@example.com",
        "username": "testuser",
        "phone": None,
        "rol": "USER",
        "exp": time.time() + 3600  # Expires in 1 hour
    },
    "admin_payload": {
        "uid": "admin_user_id",
        "email": "admin@example.com",
        "username": "adminuser",
        "phone": "+1234567890",
        "rol": "ADMIN",
        "exp": time.time() + 3600
    },
    "guest_payload": {
        "uid": "guest_user_id",
        "email": "guest@example.com",
        "username": "guestuser",
        "phone": None,
        "rol": "GUEST",
        "exp": time.time() + 3600
    },
    "expired_payload": {
        "uid": "expired_user_id",
        "email": "expired@example.com",
        "username": "expireduser",
        "phone": None,
        "rol": "USER",
        "exp": time.time() - 3600  # Expired 1 hour ago
    }
}

# User database mock data
USER_DATABASE_DATA = {
    "users": {
        "test_user_id": {
            "email": "owner@test.com",
            "username": "testowner",
            "phone": "+1234567890",
            "rol": "USER"
        },
        "guest_user_id": {
            "email": "guest@test.com",
            "username": "testguest",
            "phone": None,
            "rol": "GUEST"
        },
        "admin_user_id": {
            "email": "admin@test.com",
            "username": "testadmin",
            "phone": "+1987654321",
            "rol": "ADMIN"
        },
        "manager_user_id": {
            "email": "manager@test.com",
            "username": "testmanager",
            "phone": None,
            "rol": "USER"
        }
    }
}


def create_user_data(uid: str = None,
                    email: str = "test@example.com", 
                    username: str = "testuser",
                    phone: str = None,
                    rol: str = "USER") -> Dict[str, Any]:
    """Factory function to create user test data."""
    if uid is None:
        uid = f"user_{uuid.uuid4().hex[:8]}"
    
    return {
        "uid": uid,
        "email": email,
        "username": username,
        "phone": phone,
        "rol": rol
    }


def create_user_payload(uid: str = None,
                       email: str = "test@example.com",
                       username: str = "testuser",
                       phone: str = None,
                       rol: str = "USER",
                       exp_hours: int = 1) -> UserPayload:
    """Factory function to create UserPayload test data."""
    if uid is None:
        uid = f"user_{uuid.uuid4().hex[:8]}"
    
    return UserPayload(
        uid=uid,
        email=email,
        username=username,
        phone=phone,
        rol=rol,
        exp=time.time() + (exp_hours * 3600)
    )


def create_jwt_payload_dict(uid: str = None,
                           email: str = "test@example.com",
                           username: str = "testuser",
                           phone: str = None,
                           rol: str = "USER",
                           exp_hours: int = 1) -> Dict[str, Any]:
    """Factory function to create JWT payload dictionary for testing."""
    if uid is None:
        uid = f"user_{uuid.uuid4().hex[:8]}"
    
    return {
        "uid": uid,
        "email": email,
        "username": username,
        "phone": phone,
        "rol": rol,
        "exp": time.time() + (exp_hours * 3600)
    }


def create_multiple_users(count: int = 3, 
                         base_email: str = "user",
                         domain: str = "test.com") -> List[Dict[str, Any]]:
    """Factory function to create multiple user test data."""
    users = []
    for i in range(count):
        user = create_user_data(
            uid=f"user_{i+1}",
            email=f"{base_email}{i+1}@{domain}",
            username=f"testuser{i+1}",
            phone=f"+123456789{i}" if i % 2 == 0 else None,
            rol="ADMIN" if i == 0 else "USER"
        )
        users.append(user)
    return users


def create_database_user_data(users: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Factory function to create user database mock data structure."""
    if users is None:
        users = [USER_TEST_DATA["owner_user"]]
    
    mock_data = {"users": {}}
    
    for user in users:
        mock_data["users"][user["uid"]] = {
            "email": user["email"],
            "username": user["username"],
            "phone": user.get("phone"),
            "rol": user["rol"]
        }
    
    return mock_data