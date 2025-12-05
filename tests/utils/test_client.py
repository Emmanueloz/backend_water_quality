"""
Test client utilities for API testing.
"""
from typing import Any, Dict, Optional, Union
from fastapi.testclient import TestClient
from fastapi import Response
from unittest.mock import patch
import json

from app.share.jwt.domain.payload import UserPayload


class ClientHelper:
    """Helper class for API testing with authentication and common operations."""
    
    def __init__(self, test_client: TestClient):
        """Initialize test client helper."""
        self.client = test_client
    
    def create_auth_headers(self, token: str) -> Dict[str, str]:
        """Create authentication headers with Bearer token."""
        return {"Authorization": f"Bearer {token}"}
    
    def make_authenticated_request(self, 
                                  method: str, 
                                  url: str, 
                                  user_payload: UserPayload,
                                  json_data: Optional[Dict[str, Any]] = None,
                                  params: Optional[Dict[str, Any]] = None,
                                  **kwargs) -> Response:
        """Make an authenticated request to the API."""
        from app.share.jwt.infrastructure.verify_access_token import verify_access_token
        from app import app
        
        # Create mock function that returns the user payload
        async def mock_verify_func(credentials=None):
            return user_payload
        
        # Override the dependency in FastAPI
        original_override = app.dependency_overrides.get(verify_access_token)
        app.dependency_overrides[verify_access_token] = mock_verify_func
        
        try:
            headers = self.create_auth_headers("mock_token")
            
            request_kwargs = {
                "headers": headers,
                **kwargs
            }
            
            if json_data is not None:
                request_kwargs["json"] = json_data
            
            if params is not None:
                request_kwargs["params"] = params
            
            return self.client.request(method, url, **request_kwargs)
        finally:
            # Restore original override or remove if there wasn't one
            if original_override is not None:
                app.dependency_overrides[verify_access_token] = original_override
            else:
                app.dependency_overrides.pop(verify_access_token, None)
    
    def make_admin_request(self,
                          method: str,
                          url: str,
                          admin_payload: UserPayload,
                          json_data: Optional[Dict[str, Any]] = None,
                          params: Optional[Dict[str, Any]] = None,
                          **kwargs) -> Response:
        """Make an authenticated admin request to the API."""
        from app.share.jwt.infrastructure.verify_access_token import verify_access_admin_token
        from app import app
        
        # Create mock function that returns the admin payload
        async def mock_verify_func(credentials=None):
            return admin_payload
        
        # Override the dependency in FastAPI
        original_override = app.dependency_overrides.get(verify_access_admin_token)
        app.dependency_overrides[verify_access_admin_token] = mock_verify_func
        
        try:
            headers = self.create_auth_headers("mock_admin_token")
            
            request_kwargs = {
                "headers": headers,
                **kwargs
            }
            
            if json_data is not None:
                request_kwargs["json"] = json_data
            
            if params is not None:
                request_kwargs["params"] = params
            
            return self.client.request(method, url, **request_kwargs)
        finally:
            # Restore original override or remove if there wasn't one
            if original_override is not None:
                app.dependency_overrides[verify_access_admin_token] = original_override
            else:
                app.dependency_overrides.pop(verify_access_admin_token, None)
    
    def get_workspaces(self, user_payload: UserPayload) -> Response:
        """Get workspaces for authenticated user."""
        return self.make_authenticated_request("GET", "/workspaces/", user_payload)
    
    def get_workspace_by_id(self, workspace_id: str, user_payload: UserPayload) -> Response:
        """Get specific workspace by ID."""
        return self.make_authenticated_request("GET", f"/workspaces/{workspace_id}", user_payload)
    
    def create_workspace(self, workspace_data: Dict[str, Any], user_payload: UserPayload) -> Response:
        """Create a new workspace."""
        return self.make_authenticated_request("POST", "/workspaces/", user_payload, json_data=workspace_data)
    
    def update_workspace(self, workspace_id: str, workspace_data: Dict[str, Any], user_payload: UserPayload) -> Response:
        """Update an existing workspace."""
        return self.make_authenticated_request("PUT", f"/workspaces/{workspace_id}", user_payload, json_data=workspace_data)
    
    def delete_workspace(self, workspace_id: str, user_payload: UserPayload) -> Response:
        """Delete a workspace."""
        return self.make_authenticated_request("DELETE", f"/workspaces/{workspace_id}", user_payload)
    
    def get_public_workspace(self, workspace_id: str) -> Response:
        """Get public workspace (no authentication required)."""
        return self.client.get(f"/workspaces/public/{workspace_id}/")
    
    def get_shared_workspaces(self, user_payload: UserPayload) -> Response:
        """Get workspaces shared with user."""
        return self.make_authenticated_request("GET", "/workspaces/share/", user_payload)
    
    def get_workspace_guests(self, workspace_id: str, user_payload: UserPayload) -> Response:
        """Get guests for a workspace."""
        return self.make_authenticated_request("GET", f"/workspaces/{workspace_id}/guest/", user_payload)
    
    def add_workspace_guest(self, workspace_id: str, guest_data: Dict[str, Any], user_payload: UserPayload) -> Response:
        """Add a guest to a workspace."""
        return self.make_authenticated_request("POST", f"/workspaces/{workspace_id}/guest/", user_payload, json_data=guest_data)
    
    def update_workspace_guest(self, workspace_id: str, guest_id: str, guest_data: Dict[str, Any], user_payload: UserPayload) -> Response:
        """Update a workspace guest's permissions."""
        return self.make_authenticated_request("PUT", f"/workspaces/{workspace_id}/guest/{guest_id}", user_payload, json_data=guest_data)
    
    def remove_workspace_guest(self, workspace_id: str, guest_id: str, user_payload: UserPayload) -> Response:
        """Remove a guest from a workspace."""
        return self.make_authenticated_request("DELETE", f"/workspaces/{workspace_id}/guest/{guest_id}", user_payload)
    
    def get_all_workspaces_admin(self, admin_payload: UserPayload) -> Response:
        """Get all workspaces (admin only)."""
        return self.make_admin_request("GET", "/workspaces/all/", admin_payload)


class DatabaseHelper:
    """Helper class for database state verification and setup."""
    
    def __init__(self, firebase_mock):
        """Initialize database test helper."""
        self.firebase_mock = firebase_mock
    
    def setup_workspace_data(self, workspaces: Dict[str, Dict[str, Any]]) -> None:
        """Setup workspace data in Firebase mock."""
        for workspace_id, workspace_data in workspaces.items():
            ref = self.firebase_mock.reference(f"workspaces/{workspace_id}")
            ref.set(workspace_data)
            
            # Also setup user data for the owner if not already exists
            owner_uid = workspace_data.get("owner")
            if owner_uid:
                user_ref = self.firebase_mock.reference(f"users/{owner_uid}")
                if user_ref.get() is None:
                    # Create basic user data
                    user_data = {
                        "uid": owner_uid,
                        "email": f"{owner_uid}@test.com",
                        "username": owner_uid,
                        "rol": "client"  # Use correct enum value
                    }
                    user_ref.set(user_data)
    
    def setup_user_data(self, users: Dict[str, Dict[str, Any]]) -> None:
        """Setup user data in Firebase mock."""
        for user_id, user_data in users.items():
            ref = self.firebase_mock.reference(f"users/{user_id}")
            ref.set(user_data)
    
    def setup_authenticated_user(self, user_payload) -> None:
        """Setup authenticated user data in Firebase mock."""
        user_data = {
            "uid": user_payload.uid,
            "email": user_payload.email,
            "username": user_payload.username,
            "rol": user_payload.rol
        }
        ref = self.firebase_mock.reference(f"users/{user_payload.uid}")
        ref.set(user_data)
    
    def setup_guest_data(self, guest_workspaces: Dict[str, Dict[str, Dict[str, Any]]]) -> None:
        """Setup guest workspace data in Firebase mock."""
        for user_id, workspaces in guest_workspaces.items():
            for workspace_id, guest_data in workspaces.items():
                ref = self.firebase_mock.reference(f"guest_workspaces/{user_id}/{workspace_id}")
                ref.set(guest_data)
    
    def verify_workspace_exists(self, workspace_id: str) -> Dict[str, Any]:
        """Verify that workspace exists and return its data."""
        ref = self.firebase_mock.reference(f"workspaces/{workspace_id}")
        data = ref.get()
        assert data is not None, f"Workspace {workspace_id} should exist"
        return data
    
    def verify_workspace_not_exists(self, workspace_id: str) -> None:
        """Verify that workspace does not exist."""
        ref = self.firebase_mock.reference(f"workspaces/{workspace_id}")
        data = ref.get()
        assert data is None, f"Workspace {workspace_id} should not exist"
    
    def verify_guest_access(self, user_id: str, workspace_id: str, expected_role: str = None) -> Dict[str, Any]:
        """Verify that user has guest access to workspace."""
        ref = self.firebase_mock.reference(f"guest_workspaces/{user_id}/{workspace_id}")
        data = ref.get()
        assert data is not None, f"User {user_id} should have access to workspace {workspace_id}"
        
        if expected_role:
            assert data.get("rol") == expected_role, f"Expected role {expected_role}, got {data.get('rol')}"
        
        return data
    
    def verify_guest_access_removed(self, user_id: str, workspace_id: str) -> None:
        """Verify that user no longer has guest access to workspace."""
        ref = self.firebase_mock.reference(f"guest_workspaces/{user_id}/{workspace_id}")
        data = ref.get()
        assert data is None, f"User {user_id} should not have access to workspace {workspace_id}"
    
    def get_workspace_count(self) -> int:
        """Get total number of workspaces in database."""
        ref = self.firebase_mock.reference("workspaces")
        data = ref.get()
        return len(data) if data else 0
    
    def get_user_workspaces(self, user_id: str) -> Dict[str, Any]:
        """Get all workspaces owned by user."""
        ref = self.firebase_mock.reference("workspaces")
        all_workspaces = ref.get() or {}
        
        user_workspaces = {}
        for workspace_id, workspace_data in all_workspaces.items():
            if workspace_data.get("owner") == user_id:
                user_workspaces[workspace_id] = workspace_data
        
        return user_workspaces
    
    def get_user_guest_workspaces(self, user_id: str) -> Dict[str, Any]:
        """Get all workspaces where user is a guest."""
        ref = self.firebase_mock.reference(f"guest_workspaces/{user_id}")
        return ref.get() or {}
    
    def reset_database(self) -> None:
        """Reset all database data."""
        self.firebase_mock.reset()
    
    def setup_complete_test_scenario(self, 
                                   owner_id: str = "owner_user",
                                   guest_id: str = "guest_user") -> Dict[str, str]:
        """Setup a complete test scenario with owner, guest, and workspaces."""
        # Setup users
        self.setup_user_data({
            owner_id: {
                "email": f"{owner_id}@test.com",
                "username": owner_id,
                "rol": "USER"
            },
            guest_id: {
                "email": f"{guest_id}@test.com", 
                "username": guest_id,
                "rol": "GUEST"
            }
        })
        
        # Setup workspaces
        workspace_ids = {
            "private": "workspace_private_123",
            "public": "workspace_public_456",
            "shared": "workspace_shared_789"
        }
        
        self.setup_workspace_data({
            workspace_ids["private"]: {
                "name": "Private Workspace",
                "type": "private",
                "owner": owner_id
            },
            workspace_ids["public"]: {
                "name": "Public Workspace",
                "type": "public",
                "owner": owner_id
            },
            workspace_ids["shared"]: {
                "name": "Shared Workspace",
                "type": "private",
                "owner": owner_id
            }
        })
        
        # Setup guest access
        self.setup_guest_data({
            guest_id: {
                workspace_ids["shared"]: {
                    "rol": "visitor"
                }
            }
        })
        
        return workspace_ids