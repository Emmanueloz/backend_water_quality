"""
Integration tests for workspace API endpoints.
Tests the complete workflow from API endpoints to data persistence.
"""
import pytest
from fastapi import status
from unittest.mock import patch

from app.share.jwt.domain.payload import UserPayload
from tests.fixtures.workspace_data import WORKSPACE_CREATE_DATA
from tests.fixtures.user_data import USER_TEST_DATA


class TestWorkspaceAPIEndpoints:
    """Test workspace API endpoints with authentication."""
    
    def test_get_workspaces_with_authentication(self, api_client, db_helper, authenticated_user):
        """Test GET /workspaces endpoint with authentication."""
        # Setup test data
        workspace_id = "test_workspace_123"
        db_helper.setup_workspace_data({
            workspace_id: {
                "name": "Test Workspace",
                "type": "private",
                "owner": authenticated_user.uid
            }
        })
        
        # Make authenticated request
        response = api_client.get_workspaces(authenticated_user)
        
        # Verify response
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert "data" in response_data
        assert len(response_data["data"]) >= 0
    
    def test_get_workspaces_without_authentication(self, test_client):
        """Test GET /workspaces endpoint without authentication returns 401."""
        response = test_client.get("/workspaces/")
        
        # Should return unauthorized (FastAPI returns 401 for missing auth header)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_workspaces_returns_user_owned_workspaces(self, api_client, db_helper, authenticated_user):
        """Test GET /workspaces returns only workspaces owned by the authenticated user."""
        # Setup test data with multiple users and workspaces
        other_user_id = "other_user_123"
        
        db_helper.setup_workspace_data({
            "user_workspace_1": {
                "name": "User Workspace 1",
                "type": "private",
                "owner": authenticated_user.uid
            },
            "user_workspace_2": {
                "name": "User Workspace 2", 
                "type": "public",
                "owner": authenticated_user.uid
            },
            "other_workspace": {
                "name": "Other User Workspace",
                "type": "private",
                "owner": other_user_id
            }
        })
        
        # Make authenticated request
        response = api_client.get_workspaces(authenticated_user)
        
        # Verify response contains only user's workspaces
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        workspaces = response_data["data"]
        
        # Should contain user's workspaces but not other user's workspace
        workspace_names = [ws["name"] for ws in workspaces]
        assert "User Workspace 1" in workspace_names
        assert "User Workspace 2" in workspace_names
        assert "Other User Workspace" not in workspace_names
    
    def test_post_workspaces_create_workspace_success(self, api_client, db_helper, authenticated_user):
        """Test POST /workspaces endpoint for successful workspace creation."""
        # Prepare workspace creation data
        workspace_data = WORKSPACE_CREATE_DATA["valid_create"]
        
        # Make authenticated request to create workspace
        response = api_client.create_workspace(workspace_data, authenticated_user)
        
        # Verify response
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert "data" in response_data
        
        created_workspace = response_data["data"]
        assert created_workspace["name"] == workspace_data["name"]
        assert created_workspace["owner"] == authenticated_user.uid
        assert "id" in created_workspace
        
        # Verify workspace was created in database
        workspace_id = created_workspace["id"]
        db_workspace = db_helper.verify_workspace_exists(workspace_id)
        assert db_workspace["name"] == workspace_data["name"]
        assert db_workspace["owner"] == authenticated_user.uid
    
    def test_post_workspaces_without_authentication(self, test_client):
        """Test POST /workspaces endpoint without authentication returns 401."""
        workspace_data = WORKSPACE_CREATE_DATA["valid_create"]
        
        response = test_client.post("/workspaces/", json=workspace_data)
        
        # Should return unauthorized (FastAPI returns 401 for missing auth header)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_post_workspaces_with_invalid_data(self, api_client, authenticated_user):
        """Test POST /workspaces endpoint with invalid workspace data."""
        # Test with invalid short name
        invalid_data = WORKSPACE_CREATE_DATA["invalid_short_create"]
        
        response = api_client.create_workspace(invalid_data, authenticated_user)
        
        # Should return validation error
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    
    def test_post_workspaces_with_long_name(self, api_client, authenticated_user):
        """Test POST /workspaces endpoint with name too long."""
        # Test with invalid long name
        invalid_data = WORKSPACE_CREATE_DATA["invalid_long_create"]
        
        response = api_client.create_workspace(invalid_data, authenticated_user)
        
        # Should return validation error
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    
    def test_post_workspaces_creates_private_workspace_by_default(self, api_client, db_helper, authenticated_user):
        """Test POST /workspaces creates private workspace when type not specified."""
        # Create workspace without specifying type
        workspace_data = {"name": "Default Type Workspace"}
        
        response = api_client.create_workspace(workspace_data, authenticated_user)
        
        # Verify response
        assert response.status_code == status.HTTP_200_OK
        created_workspace = response.json()["data"]
        
        # Verify workspace is private by default
        workspace_id = created_workspace["id"]
        db_workspace = db_helper.verify_workspace_exists(workspace_id)
        assert db_workspace.get("type", "private") == "private"
    
    def test_put_workspaces_update_workspace_success(self, api_client, db_helper, authenticated_user):
        """Test PUT /workspaces/{id} endpoint for successful workspace update."""
        # Setup existing workspace
        workspace_id = "existing_workspace_123"
        original_data = {
            "name": "Original Workspace",
            "type": "private",
            "owner": authenticated_user.uid
        }
        db_helper.setup_workspace_data({workspace_id: original_data})
        
        # Prepare update data
        update_data = {
            "name": "Updated Workspace Name",
            "type": "public"
        }
        
        # Make authenticated request to update workspace
        response = api_client.update_workspace(workspace_id, update_data, authenticated_user)
        
        # Verify response
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert "data" in response_data
        
        updated_workspace = response_data["data"]
        assert updated_workspace["name"] == update_data["name"]
        assert updated_workspace["owner"] == authenticated_user.uid
        
        # Verify workspace was updated in database
        db_workspace = db_helper.verify_workspace_exists(workspace_id)
        assert db_workspace["name"] == update_data["name"]
    
    def test_put_workspaces_without_authentication(self, test_client):
        """Test PUT /workspaces/{id} endpoint without authentication returns 401."""
        workspace_id = "test_workspace_123"
        update_data = {"name": "Updated Name"}
        
        response = test_client.put(f"/workspaces/{workspace_id}", json=update_data)
        
        # Should return unauthorized (FastAPI returns 401 for missing auth header)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_put_workspaces_update_nonexistent_workspace(self, api_client, authenticated_user):
        """Test PUT /workspaces/{id} endpoint with non-existent workspace ID."""
        nonexistent_id = "nonexistent_workspace_123"
        update_data = {"name": "Updated Name"}
        
        response = api_client.update_workspace(nonexistent_id, update_data, authenticated_user)
        
        # Should return not found or bad request
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND]
    
    def test_put_workspaces_update_workspace_not_owned(self, api_client, db_helper, authenticated_user):
        """Test PUT /workspaces/{id} endpoint when user doesn't own the workspace."""
        # Setup workspace owned by different user
        workspace_id = "other_user_workspace_123"
        other_user_id = "other_user_456"
        
        db_helper.setup_workspace_data({
            workspace_id: {
                "name": "Other User Workspace",
                "type": "private",
                "owner": other_user_id
            }
        })
        
        # Try to update workspace not owned by authenticated user
        update_data = {"name": "Unauthorized Update"}
        response = api_client.update_workspace(workspace_id, update_data, authenticated_user)
        
        # Should return bad request or forbidden
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN]
    
    def test_put_workspaces_with_invalid_update_data(self, api_client, db_helper, authenticated_user):
        """Test PUT /workspaces/{id} endpoint with invalid update data."""
        # Setup existing workspace
        workspace_id = "existing_workspace_123"
        db_helper.setup_workspace_data({
            workspace_id: {
                "name": "Existing Workspace",
                "type": "private", 
                "owner": authenticated_user.uid
            }
        })
        
        # Try to update with invalid data (name too short)
        invalid_update_data = {"name": "AB"}  # Too short
        
        response = api_client.update_workspace(workspace_id, invalid_update_data, authenticated_user)
        
        # Should return validation error
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_CONTENT]


class TestWorkspaceAPIAuthenticationFlow:
    """Test authentication flows for workspace API endpoints."""
    
    def test_workspace_api_with_valid_jwt_token(self, api_client, db_helper, authenticated_user):
        """Test workspace API endpoints work with valid JWT token."""
        # Setup test workspace
        workspace_id = "auth_test_workspace"
        db_helper.setup_workspace_data({
            workspace_id: {
                "name": "Auth Test Workspace",
                "type": "private",
                "owner": authenticated_user.uid
            }
        })
        
        # Test GET endpoint with authentication
        response = api_client.get_workspaces(authenticated_user)
        assert response.status_code == status.HTTP_200_OK
        
        # Test POST endpoint with authentication
        create_data = {"name": "New Auth Workspace"}
        response = api_client.create_workspace(create_data, authenticated_user)
        assert response.status_code == status.HTTP_200_OK
        
        # Test PUT endpoint with authentication
        update_data = {"name": "Updated Auth Workspace"}
        response = api_client.update_workspace(workspace_id, update_data, authenticated_user)
        assert response.status_code == status.HTTP_200_OK
    
    def test_workspace_api_with_expired_token(self, api_client, user_factory):
        """Test workspace API endpoints reject expired JWT tokens."""
        # Create expired user payload
        expired_user = user_factory["create_user_payload"](
            uid="expired_user",
            email="expired@test.com",
            username="expireduser",
            exp_hours=-1  # Expired 1 hour ago
        )
        
        # Mock JWT verification to raise exception for expired token
        with patch('app.share.jwt.infrastructure.verify_access_token.verify_access_token') as mock_verify:
            mock_verify.side_effect = Exception("Token expired")
            
            # Test endpoints should return unauthorized
            response = api_client.get_workspaces(expired_user)
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_workspace_api_with_malformed_token(self, test_client):
        """Test workspace API endpoints reject malformed JWT tokens."""
        headers = {"Authorization": "Bearer malformed.token.here"}
        
        # Test GET endpoint
        response = test_client.get("/workspaces/", headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # Test POST endpoint
        response = test_client.post("/workspaces/", 
                                  json={"name": "Test"}, 
                                  headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # Test PUT endpoint
        response = test_client.put("/workspaces/test_id", 
                                 json={"name": "Test"}, 
                                 headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestWorkspaceAPIDataConsistency:
    """Test data consistency across workspace API operations."""
    
    def test_create_and_retrieve_workspace_consistency(self, api_client, db_helper, authenticated_user):
        """Test that created workspace can be retrieved with consistent data."""
        # Create workspace
        create_data = {"name": "Consistency Test Workspace", "type": "public"}
        create_response = api_client.create_workspace(create_data, authenticated_user)
        
        assert create_response.status_code == status.HTTP_200_OK
        created_workspace = create_response.json()["data"]
        workspace_id = created_workspace["id"]
        
        # Retrieve workspaces list
        list_response = api_client.get_workspaces(authenticated_user)
        assert list_response.status_code == status.HTTP_200_OK
        
        workspaces = list_response.json()["data"]
        found_workspace = next((ws for ws in workspaces if ws["id"] == workspace_id), None)
        
        # Verify consistency
        assert found_workspace is not None
        assert found_workspace["name"] == create_data["name"]
        assert found_workspace["owner"] == authenticated_user.uid
    
    def test_update_and_retrieve_workspace_consistency(self, api_client, db_helper, authenticated_user):
        """Test that updated workspace reflects changes when retrieved."""
        # Setup existing workspace
        workspace_id = "consistency_workspace_123"
        original_data = {
            "name": "Original Name",
            "type": "private",
            "owner": authenticated_user.uid
        }
        db_helper.setup_workspace_data({workspace_id: original_data})
        
        # Update workspace
        update_data = {"name": "Updated Consistency Name"}
        update_response = api_client.update_workspace(workspace_id, update_data, authenticated_user)
        assert update_response.status_code == status.HTTP_200_OK
        
        # Retrieve workspace by ID
        get_response = api_client.get_workspace_by_id(workspace_id, authenticated_user)
        assert get_response.status_code == status.HTTP_200_OK
        
        retrieved_workspace = get_response.json()["data"]
        
        # Verify consistency
        assert retrieved_workspace["name"] == update_data["name"]
        assert retrieved_workspace["id"] == workspace_id
        assert retrieved_workspace["owner"] == authenticated_user.uid
    
    def test_multiple_operations_maintain_data_integrity(self, api_client, db_helper, authenticated_user):
        """Test that multiple API operations maintain data integrity."""
        # Create multiple workspaces
        workspace_names = ["Workspace 1", "Workspace 2", "Workspace 3"]
        created_ids = []
        
        for name in workspace_names:
            create_data = {"name": name}
            response = api_client.create_workspace(create_data, authenticated_user)
            assert response.status_code == status.HTTP_200_OK
            created_ids.append(response.json()["data"]["id"])
        
        # Update one workspace
        update_data = {"name": "Updated Workspace 2"}
        update_response = api_client.update_workspace(created_ids[1], update_data, authenticated_user)
        assert update_response.status_code == status.HTTP_200_OK
        
        # Retrieve all workspaces and verify integrity
        list_response = api_client.get_workspaces(authenticated_user)
        assert list_response.status_code == status.HTTP_200_OK
        
        workspaces = list_response.json()["data"]
        workspace_dict = {ws["id"]: ws for ws in workspaces}
        
        # Verify all created workspaces exist with correct data
        assert created_ids[0] in workspace_dict
        assert workspace_dict[created_ids[0]]["name"] == "Workspace 1"
        
        assert created_ids[1] in workspace_dict
        assert workspace_dict[created_ids[1]]["name"] == "Updated Workspace 2"
        
        assert created_ids[2] in workspace_dict
        assert workspace_dict[created_ids[2]]["name"] == "Workspace 3"
        
        # Verify all workspaces belong to the authenticated user
        for workspace_id in created_ids:
            assert workspace_dict[workspace_id]["owner"] == authenticated_user.uid