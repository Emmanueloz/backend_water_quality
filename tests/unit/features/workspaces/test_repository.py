"""
Unit tests for workspace repository implementation.
Tests repository interface methods with mocked Firebase dependencies.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import List

from app.features.workspaces.infrastructure.repo_impl import WorkspaceRepositoryImpl
from app.features.workspaces.domain.model import (
    Workspace,
    WorkspaceCreate,
    WorkspaceResponse,
    WorkspaceShareResponse,
    WorkspacePublicResponse,
    WorskspacePagination
)
from app.share.workspace.domain.model import (
    WorkspaceType,
    WorkspaceRoles,
    WorkspaceRolesAll,
    WorkspaceRef
)
from app.share.users.domain.model.user import UserData
from app.share.users.domain.enum.roles import Roles


@pytest.fixture
def mock_workspace_access():
    """Mock WorkspaceAccess dependency."""
    return Mock()

@pytest.fixture
def mock_user_repo():
    """Mock UserRepository dependency."""
    return Mock()

@pytest.fixture
def repository(mock_workspace_access, mock_user_repo):
    """Create WorkspaceRepositoryImpl instance with mocked dependencies."""
    return WorkspaceRepositoryImpl(
        access=mock_workspace_access,
        user_repo=mock_user_repo
    )

@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return UserData(
        uid="test_user_id",
        email="test@example.com",
        username="testuser",
        rol=Roles.CLIENT
    )

@pytest.fixture
def sample_workspace_ref():
    """Sample WorkspaceRef for testing."""
    mock_ref = Mock()
    return WorkspaceRef(
        ref=mock_ref,
        rol=WorkspaceRolesAll.OWNER,
        is_public=False
    )

@pytest.fixture
def pagination():
    """Default pagination for testing."""
    return WorskspacePagination(limit=10, index=None)


class TestWorkspaceRepositoryImpl:
    """Test cases for WorkspaceRepositoryImpl class."""
    
    def test_repository_creation(self, repository):
        """Test that repository can be created with mocked dependencies."""
        assert repository is not None
        assert isinstance(repository, WorkspaceRepositoryImpl)


class TestGetPerUser:
    """Test cases for get_per_user method."""

    @patch('firebase_admin.db.reference')
    def test_get_per_user_returns_user_workspaces(self, mock_db_ref, repository, mock_user_repo, sample_user_data, pagination):
        """Test get_per_user returns workspaces owned by user."""
        # Arrange
        owner_uid = "test_user_id"
        mock_workspaces_ref = Mock()
        mock_query = Mock()
        
        # Mock Firebase query chain
        mock_db_ref.return_value.child.return_value = mock_workspaces_ref
        mock_workspaces_ref.order_by_child.return_value = mock_query
        mock_query.equal_to.return_value = mock_query
        mock_query.get.return_value = {
            "workspace_123": {
                "name": "Test Workspace",
                "type": "private",
                "owner": owner_uid
            },
            "workspace_456": {
                "name": "Another Workspace", 
                "type": "public",
                "owner": owner_uid
            }
        }
        
        # Mock user repository
        mock_user_repo.get_by_uid.return_value = sample_user_data
        
        # Act
        result = repository.get_per_user(owner_uid, pagination)
        
        # Assert
        assert len(result) == 2
        assert all(isinstance(workspace, WorkspaceResponse) for workspace in result)
        assert result[0].name == "Test Workspace"
        assert result[0].owner == owner_uid
        assert result[0].rol == WorkspaceRolesAll.OWNER
        assert result[1].name == "Another Workspace"
        
        # Verify Firebase calls
        mock_db_ref.assert_called_once()
        mock_workspaces_ref.order_by_child.assert_called_once_with("owner")
        mock_query.equal_to.assert_called_once_with(owner_uid)

    @patch('firebase_admin.db.reference')
    def test_get_per_user_empty_result(self, mock_db_ref, repository, mock_user_repo, pagination):
        """Test get_per_user returns empty list when user has no workspaces."""
        # Arrange
        owner_uid = "user_with_no_workspaces"
        mock_workspaces_ref = Mock()
        mock_query = Mock()
        
        mock_db_ref.return_value.child.return_value = mock_workspaces_ref
        mock_workspaces_ref.order_by_child.return_value = mock_query
        mock_query.equal_to.return_value = mock_query
        mock_query.get.return_value = {}
        
        # Act
        result = repository.get_per_user(owner_uid, pagination)
        
        # Assert
        assert result == []
        mock_query.get.assert_called_once()

    @patch('firebase_admin.db.reference')
    def test_get_per_user_none_result(self, mock_db_ref, repository, mock_user_repo, pagination):
        """Test get_per_user handles None result from Firebase."""
        # Arrange
        owner_uid = "test_user_id"
        mock_workspaces_ref = Mock()
        mock_query = Mock()
        
        mock_db_ref.return_value.child.return_value = mock_workspaces_ref
        mock_workspaces_ref.order_by_child.return_value = mock_query
        mock_query.equal_to.return_value = mock_query
        mock_query.get.return_value = None
        
        # Act
        result = repository.get_per_user(owner_uid, pagination)
        
        # Assert
        assert result == []


class TestGetById:
    """Test cases for get_by_id method."""

    def test_get_by_id_owner_access(self, repository, mock_workspace_access, sample_workspace_ref):
        """Test get_by_id returns workspace when user is owner."""
        # Arrange
        workspace_id = "workspace_123"
        owner_uid = "test_user_id"
        
        # Mock workspace access
        sample_workspace_ref.ref.get.return_value = {
            "name": "Test Workspace",
            "type": "private",
            "owner": owner_uid
        }
        sample_workspace_ref.rol = WorkspaceRolesAll.OWNER
        mock_workspace_access.get_ref.return_value = sample_workspace_ref
        
        # Act
        result = repository.get_by_id(workspace_id, owner_uid)
        
        # Assert
        assert isinstance(result, WorkspaceResponse)
        assert result.id == workspace_id
        assert result.name == "Test Workspace"
        assert result.owner == owner_uid
        assert result.type == "private"
        assert result.rol == WorkspaceRolesAll.OWNER
        
        # Verify workspace access call
        mock_workspace_access.get_ref.assert_called_once_with(
            workspace_id=workspace_id,
            user=owner_uid,
            roles=[
                WorkspaceRoles.VISITOR,
                WorkspaceRoles.MANAGER,
                WorkspaceRoles.ADMINISTRATOR,
            ],
            is_public=True,
        )

    def test_get_by_id_public_workspace_visitor(self, repository, mock_workspace_access, sample_workspace_ref):
        """Test get_by_id returns public workspace for visitor with limited data."""
        # Arrange
        workspace_id = "workspace_456"
        visitor_uid = "visitor_user_id"
        
        # Mock workspace access for public workspace
        sample_workspace_ref.ref.get.return_value = {
            "name": "Public Workspace",
            "type": "public",
            "owner": "owner_user_id"
        }
        sample_workspace_ref.rol = WorkspaceRoles.VISITOR
        mock_workspace_access.get_ref.return_value = sample_workspace_ref
        
        # Act
        result = repository.get_by_id(workspace_id, visitor_uid)
        
        # Assert
        assert isinstance(result, WorkspaceResponse)
        assert result.id == workspace_id
        assert result.name == "Public Workspace"
        assert result.owner is None  # Owner hidden for public workspace visitors
        assert result.type == "public"
        assert result.rol == WorkspaceRoles.VISITOR

    def test_get_by_id_guest_access(self, repository, mock_workspace_access, sample_workspace_ref):
        """Test get_by_id returns workspace for guest user with proper role."""
        # Arrange
        workspace_id = "workspace_789"
        guest_uid = "guest_user_id"
        
        # Mock workspace access for guest
        sample_workspace_ref.ref.get.return_value = {
            "name": "Shared Workspace",
            "type": "private",
            "owner": "owner_user_id"
        }
        sample_workspace_ref.rol = WorkspaceRoles.MANAGER
        mock_workspace_access.get_ref.return_value = sample_workspace_ref
        
        # Act
        result = repository.get_by_id(workspace_id, guest_uid)
        
        # Assert
        assert isinstance(result, WorkspaceResponse)
        assert result.id == workspace_id
        assert result.name == "Shared Workspace"
        assert result.owner == "owner_user_id"
        assert result.type == "private"
        assert result.rol == WorkspaceRoles.MANAGER


class TestCreate:
    """Test cases for create method."""

    @patch('firebase_admin.db.reference')
    def test_create_workspace_success(self, mock_db_ref, repository):
        """Test create method successfully creates new workspace."""
        # Arrange
        workspace_data = Workspace(
            name="New Test Workspace",
            owner="test_user_id",
            type=WorkspaceType.PRIVATE
        )
        
        # Mock Firebase push operation
        mock_workspaces_ref = Mock()
        mock_new_ref = Mock()
        mock_new_ref.key = "new_workspace_123"
        
        mock_db_ref.return_value.child.return_value = mock_workspaces_ref
        mock_workspaces_ref.push.return_value = mock_new_ref
        
        # Act
        result = repository.create(workspace_data)
        
        # Assert
        assert isinstance(result, WorkspaceResponse)
        assert result.id == "new_workspace_123"
        assert result.name == "New Test Workspace"
        assert result.owner == "test_user_id"
        assert result.type == WorkspaceType.PRIVATE
        
        # Verify Firebase calls
        mock_db_ref.assert_called_once()
        mock_workspaces_ref.push.assert_called_once_with(workspace_data.model_dump())

    @patch('firebase_admin.db.reference')
    def test_create_public_workspace(self, mock_db_ref, repository):
        """Test create method creates public workspace."""
        # Arrange
        workspace_data = Workspace(
            name="Public Workspace",
            owner="test_user_id",
            type=WorkspaceType.PUBLIC
        )
        
        # Mock Firebase push operation
        mock_workspaces_ref = Mock()
        mock_new_ref = Mock()
        mock_new_ref.key = "public_workspace_456"
        
        mock_db_ref.return_value.child.return_value = mock_workspaces_ref
        mock_workspaces_ref.push.return_value = mock_new_ref
        
        # Act
        result = repository.create(workspace_data)
        
        # Assert
        assert isinstance(result, WorkspaceResponse)
        assert result.id == "public_workspace_456"
        assert result.type == WorkspaceType.PUBLIC
        
        # Verify workspace data was pushed correctly
        expected_data = {
            "name": "Public Workspace",
            "owner": "test_user_id",
            "type": WorkspaceType.PUBLIC
        }
        mock_workspaces_ref.push.assert_called_once_with(expected_data)


class TestUpdate:
    """Test cases for update method."""

    def test_update_workspace_success(self, repository, mock_workspace_access, sample_workspace_ref):
        """Test update method successfully updates workspace with admin permissions."""
        # Arrange
        workspace_id = "workspace_123"
        owner_uid = "test_user_id"
        update_data = WorkspaceCreate(
            name="Updated Workspace Name",
            type=WorkspaceType.PUBLIC
        )
        
        # Mock workspace access for admin role
        sample_workspace_ref.ref.update = Mock()
        sample_workspace_ref.ref.get.return_value = {
            "name": "Updated Workspace Name",
            "type": "public",
            "owner": owner_uid
        }
        mock_workspace_access.get_ref.return_value = sample_workspace_ref
        
        # Act
        result = repository.update(workspace_id, update_data, owner_uid)
        
        # Assert
        assert isinstance(result, WorkspaceResponse)
        assert result.id == workspace_id
        assert result.name == "Updated Workspace Name"
        assert result.type == "public"
        assert result.owner == owner_uid
        
        # Verify workspace access call with admin role requirement
        mock_workspace_access.get_ref.assert_called_once_with(
            workspace_id=workspace_id,
            user=owner_uid,
            roles=[WorkspaceRoles.ADMINISTRATOR]
        )
        
        # Verify update was called
        expected_update_data = {
            "name": "Updated Workspace Name",
            "type": WorkspaceType.PUBLIC
        }
        sample_workspace_ref.ref.update.assert_called_once_with(expected_update_data)

    def test_update_workspace_permission_validation(self, repository, mock_workspace_access):
        """Test update method validates admin permissions."""
        # Arrange
        workspace_id = "workspace_123"
        non_admin_uid = "guest_user_id"
        update_data = WorkspaceCreate(
            name="Unauthorized Update",
            type=WorkspaceType.PRIVATE
        )
        
        # Mock workspace access to raise permission error
        from fastapi import HTTPException
        mock_workspace_access.get_ref.side_effect = HTTPException(
            status_code=403,
            detail="No tiene acceso a la workspace con ID: workspace_123"
        )
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            repository.update(workspace_id, update_data, non_admin_uid)
        
        assert exc_info.value.status_code == 403
        assert "No tiene acceso" in str(exc_info.value.detail)


class TestDelete:
    """Test cases for delete method."""

    def test_delete_workspace_success(self, repository, mock_workspace_access, sample_workspace_ref):
        """Test delete method successfully removes workspace with owner permissions."""
        # Arrange
        workspace_id = "workspace_123"
        owner_uid = "test_user_id"
        
        # Mock workspace access and deletion
        sample_workspace_ref.ref.get.return_value = {
            "name": "Workspace to Delete",
            "type": "private",
            "owner": owner_uid
        }
        sample_workspace_ref.ref.delete = Mock()
        mock_workspace_access.get_ref.return_value = sample_workspace_ref
        
        # Act
        result = repository.delete(workspace_id, owner_uid)
        
        # Assert
        assert result is True
        
        # Verify workspace access call
        mock_workspace_access.get_ref.assert_called_once_with(
            workspace_id=workspace_id,
            user=owner_uid
        )
        
        # Verify delete was called
        sample_workspace_ref.ref.delete.assert_called_once()

    def test_delete_workspace_not_found(self, repository, mock_workspace_access, sample_workspace_ref):
        """Test delete method returns False when workspace doesn't exist."""
        # Arrange
        workspace_id = "nonexistent_workspace"
        owner_uid = "test_user_id"
        
        # Mock workspace access returning None data
        sample_workspace_ref.ref.get.return_value = None
        mock_workspace_access.get_ref.return_value = sample_workspace_ref
        
        # Act
        result = repository.delete(workspace_id, owner_uid)
        
        # Assert
        assert result is False
        
        # Verify delete was not called
        sample_workspace_ref.ref.delete.assert_not_called()

    def test_delete_workspace_ownership_verification(self, repository, mock_workspace_access):
        """Test delete method verifies workspace ownership."""
        # Arrange
        workspace_id = "workspace_123"
        non_owner_uid = "unauthorized_user_id"
        
        # Mock workspace access to raise permission error
        from fastapi import HTTPException
        mock_workspace_access.get_ref.side_effect = HTTPException(
            status_code=403,
            detail="No tiene acceso a la workspace con ID: workspace_123"
        )
        
        # Act
        result = repository.delete(workspace_id, non_owner_uid)
        
        # Assert
        assert result is False

    def test_delete_workspace_exception_handling(self, repository, mock_workspace_access, sample_workspace_ref):
        """Test delete method handles exceptions gracefully."""
        # Arrange
        workspace_id = "workspace_123"
        owner_uid = "test_user_id"
        
        # Mock workspace access to raise unexpected exception
        sample_workspace_ref.ref.get.side_effect = Exception("Database connection error")
        mock_workspace_access.get_ref.return_value = sample_workspace_ref
        
        # Act
        result = repository.delete(workspace_id, owner_uid)
        
        # Assert
        assert result is False


class TestGetWorkspacesShares:
    """Test cases for get_workspaces_shares method."""

    @patch('firebase_admin.db.reference')
    def test_get_workspaces_shares_success(self, mock_db_ref, repository, mock_workspace_access, mock_user_repo, sample_user_data, pagination):
        """Test get_workspaces_shares returns shared workspaces for guest user."""
        # Arrange
        guest_uid = "guest_user_id"
        
        # Mock Firebase guest workspaces reference and query chain
        mock_guest_ref = Mock()
        mock_query = Mock()
        mock_limited_query = Mock()
        
        mock_db_ref.return_value.child.return_value.child.return_value = mock_guest_ref
        mock_guest_ref.order_by_key.return_value = mock_query
        mock_query.limit_to_first.return_value = mock_limited_query
        
        mock_limited_query.get.return_value = {
            "workspace_123": {"rol": "visitor"},
            "workspace_456": {"rol": "manager"}
        }
        
        # Mock workspace access for each shared workspace
        mock_workspace_ref_1 = Mock()
        mock_workspace_ref_1.ref.get.return_value = {
            "name": "Shared Workspace 1",
            "type": "private",
            "owner": "owner_user_id"
        }
        mock_workspace_ref_1.user = sample_user_data
        mock_workspace_ref_1.owner = UserData(
            uid="owner_user_id",
            email="owner@example.com",
            username="owner",
            rol=Roles.CLIENT
        )
        mock_workspace_ref_1.rol = WorkspaceRoles.VISITOR
        
        mock_workspace_ref_2 = Mock()
        mock_workspace_ref_2.ref.get.return_value = {
            "name": "Shared Workspace 2",
            "type": "private",
            "owner": "owner_user_id"
        }
        mock_workspace_ref_2.user = sample_user_data
        mock_workspace_ref_2.owner = UserData(
            uid="owner_user_id",
            email="owner@example.com",
            username="owner",
            rol=Roles.CLIENT
        )
        mock_workspace_ref_2.rol = WorkspaceRoles.MANAGER
        
        # Mock workspace access calls
        mock_workspace_access.get_ref.side_effect = [
            mock_workspace_ref_1,
            mock_workspace_ref_2
        ]
        
        # Act
        result = repository.get_workspaces_shares(guest_uid, pagination)
        
        # Assert
        assert len(result) == 2
        assert all(isinstance(workspace, WorkspaceShareResponse) for workspace in result)
        
        # Verify first shared workspace
        assert result[0].id == "workspace_123"
        assert result[0].name == "Shared Workspace 1"
        assert result[0].owner == "owner_user_id"
        assert result[0].guest == sample_user_data.email
        assert result[0].rol == WorkspaceRoles.VISITOR
        
        # Verify second shared workspace
        assert result[1].id == "workspace_456"
        assert result[1].name == "Shared Workspace 2"
        assert result[1].rol == WorkspaceRoles.MANAGER
        
        # Verify workspace access calls
        assert mock_workspace_access.get_ref.call_count == 2

    @patch('firebase_admin.db.reference')
    def test_get_workspaces_shares_no_shared_workspaces(self, mock_db_ref, repository, pagination):
        """Test get_workspaces_shares returns empty list when user has no shared workspaces."""
        # Arrange
        guest_uid = "user_with_no_shares"
        
        # Mock Firebase guest workspaces reference returning None
        mock_guest_ref = Mock()
        mock_query = Mock()
        mock_limited_query = Mock()
        
        mock_db_ref.return_value.child.return_value.child.return_value = mock_guest_ref
        mock_guest_ref.order_by_key.return_value = mock_query
        mock_query.limit_to_first.return_value = mock_limited_query
        mock_limited_query.get.return_value = None
        
        # Act
        result = repository.get_workspaces_shares(guest_uid, pagination)
        
        # Assert
        assert result == []

    @patch('firebase_admin.db.reference')
    def test_get_workspaces_shares_with_invalid_workspace(self, mock_db_ref, repository, mock_workspace_access, pagination):
        """Test get_workspaces_shares handles invalid workspace references gracefully."""
        # Arrange
        guest_uid = "guest_user_id"
        
        # Mock Firebase guest workspaces reference
        mock_guest_ref = Mock()
        mock_query = Mock()
        mock_limited_query = Mock()
        
        mock_db_ref.return_value.child.return_value.child.return_value = mock_guest_ref
        mock_guest_ref.order_by_key.return_value = mock_query
        mock_query.limit_to_first.return_value = mock_limited_query
        
        mock_limited_query.get.return_value = {
            "valid_workspace": {"rol": "visitor"},
            "invalid_workspace": {"rol": "manager"}
        }
        
        # Mock workspace access - first call succeeds, second returns None
        mock_workspace_ref = Mock()
        mock_workspace_ref.ref.get.return_value = {
            "name": "Valid Workspace",
            "type": "private",
            "owner": "owner_user_id"
        }
        mock_workspace_ref.user = UserData(
            uid="guest_user_id",
            email="guest@example.com",
            username="guest",
            rol=Roles.CLIENT
        )
        mock_workspace_ref.owner = UserData(
            uid="owner_user_id",
            email="owner@example.com",
            username="owner",
            rol=Roles.CLIENT
        )
        mock_workspace_ref.rol = WorkspaceRoles.VISITOR
        
        mock_workspace_access.get_ref.side_effect = [
            mock_workspace_ref,  # Valid workspace
            None  # Invalid workspace
        ]
        
        # Act
        result = repository.get_workspaces_shares(guest_uid, pagination)
        
        # Assert
        assert len(result) == 1
        assert result[0].id == "valid_workspace"
        assert result[0].name == "Valid Workspace"

    @patch('firebase_admin.db.reference')
    def test_get_workspaces_shares_guest_access_verification(self, mock_db_ref, repository, mock_workspace_access, pagination):
        """Test get_workspaces_shares verifies guest access permissions."""
        # Arrange
        guest_uid = "guest_user_id"
        
        # Mock Firebase guest workspaces reference
        mock_guest_ref = Mock()
        mock_query = Mock()
        mock_limited_query = Mock()
        
        mock_db_ref.return_value.child.return_value.child.return_value = mock_guest_ref
        mock_guest_ref.order_by_key.return_value = mock_query
        mock_query.limit_to_first.return_value = mock_limited_query
        
        mock_limited_query.get.return_value = {
            "workspace_123": {"rol": "visitor"}
        }
        
        # Mock workspace access to return None (no access)
        mock_workspace_access.get_ref.return_value = None
        
        # Act
        result = repository.get_workspaces_shares(guest_uid, pagination)
        
        # Assert - Should return empty list when no access
        assert result == []
        
        # Assert - Verify workspace access call with correct parameters
        mock_workspace_access.get_ref.assert_called_with(
            workspace_id="workspace_123",
            user=guest_uid,
            roles=[
                WorkspaceRoles.VISITOR,
                WorkspaceRoles.MANAGER,
                WorkspaceRoles.ADMINISTRATOR,
            ],
            is_null=True,
            owner_limit_data=True,
        )

class TestRepositoryErrorHandling:
    """Test cases for repository error handling scenarios."""

    def test_get_by_id_invalid_workspace_id(self, repository, mock_workspace_access):
        """Test get_by_id raises HTTPException for invalid workspace ID."""
        # Arrange
        invalid_workspace_id = "nonexistent_workspace"
        user_uid = "test_user_id"
        
        # Mock workspace access to raise 404 error
        from fastapi import HTTPException
        mock_workspace_access.get_ref.side_effect = HTTPException(
            status_code=404,
            detail=f"No existe workspace con ID: {invalid_workspace_id}"
        )
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            repository.get_by_id(invalid_workspace_id, user_uid)
        
        assert exc_info.value.status_code == 404
        assert "No existe workspace" in str(exc_info.value.detail)
        assert invalid_workspace_id in str(exc_info.value.detail)

    def test_get_by_id_permission_denied(self, repository, mock_workspace_access):
        """Test get_by_id raises HTTPException when user lacks permissions."""
        # Arrange
        workspace_id = "private_workspace"
        unauthorized_user_uid = "unauthorized_user"
        
        # Mock workspace access to raise 403 error
        from fastapi import HTTPException
        mock_workspace_access.get_ref.side_effect = HTTPException(
            status_code=403,
            detail=f"No tiene acceso a la workspace con ID: {workspace_id}"
        )
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            repository.get_by_id(workspace_id, unauthorized_user_uid)
        
        assert exc_info.value.status_code == 403
        assert "No tiene acceso" in str(exc_info.value.detail)
        assert workspace_id in str(exc_info.value.detail)

    def test_update_permission_denied_non_admin(self, repository, mock_workspace_access):
        """Test update raises HTTPException when user is not admin."""
        # Arrange
        workspace_id = "workspace_123"
        non_admin_uid = "regular_user_id"
        update_data = WorkspaceCreate(
            name="Unauthorized Update",
            type=WorkspaceType.PRIVATE
        )
        
        # Mock workspace access to raise 403 error for non-admin
        from fastapi import HTTPException
        mock_workspace_access.get_ref.side_effect = HTTPException(
            status_code=403,
            detail="No tiene acceso a la workspace con ID: workspace_123"
        )
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            repository.update(workspace_id, update_data, non_admin_uid)
        
        assert exc_info.value.status_code == 403
        assert "No tiene acceso" in str(exc_info.value.detail)

    def test_update_invalid_workspace_id(self, repository, mock_workspace_access):
        """Test update raises HTTPException for invalid workspace ID."""
        # Arrange
        invalid_workspace_id = "nonexistent_workspace"
        admin_uid = "admin_user_id"
        update_data = WorkspaceCreate(
            name="Update Nonexistent",
            type=WorkspaceType.PRIVATE
        )
        
        # Mock workspace access to raise 404 error
        from fastapi import HTTPException
        mock_workspace_access.get_ref.side_effect = HTTPException(
            status_code=404,
            detail=f"No existe workspace con ID: {invalid_workspace_id}"
        )
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            repository.update(invalid_workspace_id, update_data, admin_uid)
        
        assert exc_info.value.status_code == 404
        assert "No existe workspace" in str(exc_info.value.detail)

    @patch('firebase_admin.db.reference')
    def test_get_per_user_database_connection_error(self, mock_db_ref, repository, mock_user_repo, pagination):
        """Test get_per_user handles database connection errors gracefully."""
        # Arrange
        owner_uid = "test_user_id"
        
        # Mock Firebase to raise connection error
        mock_db_ref.side_effect = Exception("Firebase connection failed")
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            repository.get_per_user(owner_uid, pagination)
        
        assert "Firebase connection failed" in str(exc_info.value)

    @patch('firebase_admin.db.reference')
    def test_create_database_connection_error(self, mock_db_ref, repository):
        """Test create handles database connection errors gracefully."""
        # Arrange
        workspace_data = Workspace(
            name="Test Workspace",
            owner="test_user_id",
            type=WorkspaceType.PRIVATE
        )
        
        # Mock Firebase to raise connection error
        mock_db_ref.side_effect = Exception("Firebase connection failed")
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            repository.create(workspace_data)
        
        assert "Firebase connection failed" in str(exc_info.value)

    @patch('firebase_admin.db.reference')
    def test_get_workspaces_shares_database_error(self, mock_db_ref, repository, pagination):
        """Test get_workspaces_shares handles database errors gracefully."""
        # Arrange
        guest_uid = "guest_user_id"
        
        # Mock Firebase to raise database error
        mock_db_ref.side_effect = Exception("Database query failed")
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            repository.get_workspaces_shares(guest_uid, pagination)
        
        assert "Database query failed" in str(exc_info.value)

    @patch('firebase_admin.db.reference')
    def test_get_all_database_connection_simulation(self, mock_db_ref, repository, mock_user_repo, pagination):
        """Test get_all method handles database connection errors."""
        # Arrange
        # Mock Firebase to raise connection error
        mock_db_ref.side_effect = Exception("Database connection timeout")
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            repository.get_all(pagination)
        
        assert "Database connection timeout" in str(exc_info.value)