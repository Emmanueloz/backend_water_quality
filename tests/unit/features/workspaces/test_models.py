import pytest
from pydantic import ValidationError

from app.features.workspaces.domain.model import (
    Workspace,
    WorkspaceCreate,
    WorkspaceResponse,
    WorkspaceShareResponse,
    GuestResponse,
    WorkspacePublicResponse,
    WorkspaceGuestCreate,
    WorkspaceGuestUpdate,
    WorkspaceGuestDelete,
    WorkspaceConnectionPayload,
)
from app.share.workspace.domain.model import WorkspaceType, WorkspaceRoles, WorkspaceRolesAll
from app.share.users.domain.model.user import UserData
from app.share.users.domain.enum.roles import Roles


class TestWorkspaceCreate:
    """Test WorkspaceCreate model field validation"""

    def test_valid_workspace_create(self):
        """Test creating a valid workspace"""
        workspace_data = {
            "name": "Test Workspace",
            "type": WorkspaceType.PRIVATE
        }
        workspace = WorkspaceCreate(**workspace_data)
        
        assert workspace.name == "Test Workspace"
        assert workspace.type == WorkspaceType.PRIVATE

    def test_workspace_create_default_type(self):
        """Test workspace creation with default type"""
        workspace = WorkspaceCreate(name="Test Workspace")
        
        assert workspace.name == "Test Workspace"
        assert workspace.type == WorkspaceType.PRIVATE

    def test_workspace_create_public_type(self):
        """Test workspace creation with public type"""
        workspace = WorkspaceCreate(name="Public Workspace", type=WorkspaceType.PUBLIC)
        
        assert workspace.name == "Public Workspace"
        assert workspace.type == WorkspaceType.PUBLIC

    def test_workspace_name_too_short(self):
        """Test workspace name validation - too short"""
        with pytest.raises(ValidationError) as exc_info:
            WorkspaceCreate(name="ab")
        
        error = exc_info.value.errors()[0]
        assert "El nombre del workspace debe tener al menos 3 caracteres" in str(error["ctx"]["error"])

    def test_workspace_name_too_long(self):
        """Test workspace name validation - too long"""
        long_name = "a" * 51  # 51 characters
        with pytest.raises(ValidationError) as exc_info:
            WorkspaceCreate(name=long_name)
        
        error = exc_info.value.errors()[0]
        assert "El nombre del workspace no puede tener más de 50 caracteres" in str(error["ctx"]["error"])

    def test_workspace_name_with_whitespace(self):
        """Test workspace name validation with whitespace"""
        workspace = WorkspaceCreate(name="  Valid Name  ")
        assert workspace.name == "  Valid Name  "

    def test_workspace_name_only_whitespace_too_short(self):
        """Test workspace name validation - only whitespace that's too short"""
        with pytest.raises(ValidationError) as exc_info:
            WorkspaceCreate(name="  ")
        
        error = exc_info.value.errors()[0]
        assert "El nombre del workspace debe tener al menos 3 caracteres" in str(error["ctx"]["error"])

    def test_workspace_name_minimum_valid_length(self):
        """Test workspace name with minimum valid length"""
        workspace = WorkspaceCreate(name="abc")
        assert workspace.name == "abc"

    def test_workspace_name_maximum_valid_length(self):
        """Test workspace name with maximum valid length"""
        max_name = "a" * 50  # 50 characters
        workspace = WorkspaceCreate(name=max_name)
        assert workspace.name == max_name


class TestWorkspace:
    """Test Workspace model serialization/deserialization"""

    def test_valid_workspace_model(self):
        """Test creating a valid workspace model"""
        workspace_data = {
            "name": "Test Workspace",
            "owner": "user123",
            "type": WorkspaceType.PRIVATE
        }
        workspace = Workspace(**workspace_data)
        
        assert workspace.name == "Test Workspace"
        assert workspace.owner == "user123"
        assert workspace.type == WorkspaceType.PRIVATE

    def test_workspace_model_default_type(self):
        """Test workspace model with default type"""
        workspace = Workspace(name="Test Workspace", owner="user123")
        
        assert workspace.name == "Test Workspace"
        assert workspace.owner == "user123"
        assert workspace.type == WorkspaceType.PRIVATE

    def test_workspace_model_no_owner(self):
        """Test workspace model without owner"""
        workspace = Workspace(name="Test Workspace", owner=None)
        
        assert workspace.name == "Test Workspace"
        assert workspace.owner is None
        assert workspace.type == WorkspaceType.PRIVATE

    def test_workspace_model_serialization(self):
        """Test workspace model serialization to dict"""
        workspace = Workspace(
            name="Test Workspace",
            owner="user123",
            type=WorkspaceType.PUBLIC
        )
        
        workspace_dict = workspace.model_dump()
        expected = {
            "name": "Test Workspace",
            "owner": "user123",
            "type": "public"
        }
        
        assert workspace_dict == expected

    def test_workspace_model_deserialization(self):
        """Test workspace model deserialization from dict"""
        workspace_dict = {
            "name": "Test Workspace",
            "owner": "user123",
            "type": "private"
        }
        
        workspace = Workspace(**workspace_dict)
        
        assert workspace.name == "Test Workspace"
        assert workspace.owner == "user123"
        assert workspace.type == WorkspaceType.PRIVATE

class TestWorkspaceResponse:
    """Test WorkspaceResponse model construction"""

    def test_workspace_response_creation(self):
        """Test creating a WorkspaceResponse model"""
        user_data = UserData(
            uid="user123",
            username="testuser",
            email="test@example.com",
            rol=Roles.CLIENT
        )
        
        workspace_response = WorkspaceResponse(
            id="workspace123",
            name="Test Workspace",
            owner="user123",
            type=WorkspaceType.PRIVATE,
            user=user_data,
            rol=WorkspaceRolesAll.OWNER
        )
        
        assert workspace_response.id == "workspace123"
        assert workspace_response.name == "Test Workspace"
        assert workspace_response.owner == "user123"
        assert workspace_response.type == WorkspaceType.PRIVATE
        assert workspace_response.user == user_data
        assert workspace_response.rol == WorkspaceRolesAll.OWNER

    def test_workspace_response_default_values(self):
        """Test WorkspaceResponse with default values"""
        workspace_response = WorkspaceResponse(
            id="workspace123",
            name="Test Workspace",
            owner="user123"
        )
        
        assert workspace_response.id == "workspace123"
        assert workspace_response.name == "Test Workspace"
        assert workspace_response.owner == "user123"
        assert workspace_response.type == WorkspaceType.PRIVATE  # Default from parent
        assert workspace_response.user is None  # Default
        assert workspace_response.rol == WorkspaceRolesAll.UNKNOWN  # Default

    def test_workspace_response_with_workspace_role(self):
        """Test WorkspaceResponse with workspace role"""
        workspace_response = WorkspaceResponse(
            id="workspace123",
            name="Test Workspace",
            owner="user123",
            rol=WorkspaceRoles.ADMINISTRATOR
        )
        
        assert workspace_response.rol == WorkspaceRoles.ADMINISTRATOR

    def test_workspace_response_inheritance(self):
        """Test WorkspaceResponse inherits from Workspace"""
        workspace_response = WorkspaceResponse(
            id="workspace123",
            name="Test Workspace",
            owner="user123",
            type=WorkspaceType.PUBLIC
        )
        
        # Should have all Workspace fields
        assert hasattr(workspace_response, 'name')
        assert hasattr(workspace_response, 'owner')
        assert hasattr(workspace_response, 'type')
        # Plus additional fields
        assert hasattr(workspace_response, 'id')
        assert hasattr(workspace_response, 'user')
        assert hasattr(workspace_response, 'rol')

    def test_workspace_response_serialization(self):
        """Test WorkspaceResponse serialization"""
        user_data = UserData(
            uid="user123",
            username="testuser",
            email="test@example.com",
            rol=Roles.CLIENT
        )
        
        workspace_response = WorkspaceResponse(
            id="workspace123",
            name="Test Workspace",
            owner="user123",
            type=WorkspaceType.PUBLIC,
            user=user_data,
            rol=WorkspaceRolesAll.OWNER
        )
        
        serialized = workspace_response.model_dump()
        
        assert serialized["id"] == "workspace123"
        assert serialized["name"] == "Test Workspace"
        assert serialized["owner"] == "user123"
        assert serialized["type"] == "public"
        assert serialized["rol"] == "owner"
        assert "user" in serialized
        assert serialized["user"]["uid"] == "user123"


class TestWorkspaceShareResponse:
    """Test WorkspaceShareResponse model functionality"""

    def test_workspace_share_response_creation(self):
        """Test creating a WorkspaceShareResponse model"""
        user_data = UserData(
            uid="user123",
            username="testuser",
            email="test@example.com",
            rol=Roles.CLIENT
        )
        
        workspace_share = WorkspaceShareResponse(
            id="workspace123",
            name="Shared Workspace",
            owner="owner123",
            type=WorkspaceType.PRIVATE,
            user=user_data,
            rol=WorkspaceRoles.VISITOR,
            guest="guest123"
        )
        
        assert workspace_share.id == "workspace123"
        assert workspace_share.name == "Shared Workspace"
        assert workspace_share.owner == "owner123"
        assert workspace_share.type == WorkspaceType.PRIVATE
        assert workspace_share.user == user_data
        assert workspace_share.rol == WorkspaceRoles.VISITOR
        assert workspace_share.guest == "guest123"

    def test_workspace_share_response_inheritance(self):
        """Test WorkspaceShareResponse inherits from WorkspaceResponse"""
        workspace_share = WorkspaceShareResponse(
            id="workspace123",
            name="Shared Workspace",
            owner="owner123",
            guest="guest123"
        )
        
        # Should have all WorkspaceResponse fields
        assert hasattr(workspace_share, 'id')
        assert hasattr(workspace_share, 'name')
        assert hasattr(workspace_share, 'owner')
        assert hasattr(workspace_share, 'type')
        assert hasattr(workspace_share, 'user')
        assert hasattr(workspace_share, 'rol')
        # Plus additional field
        assert hasattr(workspace_share, 'guest')

    def test_workspace_share_response_serialization(self):
        """Test WorkspaceShareResponse serialization"""
        workspace_share = WorkspaceShareResponse(
            id="workspace123",
            name="Shared Workspace",
            owner="owner123",
            type=WorkspaceType.PUBLIC,
            rol=WorkspaceRoles.MANAGER,
            guest="guest123"
        )
        
        serialized = workspace_share.model_dump()
        
        assert serialized["id"] == "workspace123"
        assert serialized["name"] == "Shared Workspace"
        assert serialized["owner"] == "owner123"
        assert serialized["type"] == "public"
        assert serialized["rol"] == "manager"
        assert serialized["guest"] == "guest123"


class TestGuestResponse:
    """Test GuestResponse model"""

    def test_guest_response_creation(self):
        """Test creating a GuestResponse model"""
        guest = GuestResponse(
            uid="guest123",
            email="guest@example.com",
            username="guestuser",
            rol=WorkspaceRoles.VISITOR
        )
        
        assert guest.uid == "guest123"
        assert guest.email == "guest@example.com"
        assert guest.username == "guestuser"
        assert guest.rol == WorkspaceRoles.VISITOR

    def test_guest_response_all_roles(self):
        """Test GuestResponse with different roles"""
        roles_to_test = [
            WorkspaceRoles.VISITOR,
            WorkspaceRoles.MANAGER,
            WorkspaceRoles.ADMINISTRATOR
        ]
        
        for role in roles_to_test:
            guest = GuestResponse(
                uid="guest123",
                email="guest@example.com",
                username="guestuser",
                rol=role
            )
            assert guest.rol == role


class TestWorkspacePublicResponse:
    """Test WorkspacePublicResponse model"""

    def test_workspace_public_response_creation(self):
        """Test creating a WorkspacePublicResponse model"""
        public_workspace = WorkspacePublicResponse(
            id="workspace123",
            name="Public Workspace",
            rol=WorkspaceRoles.VISITOR
        )
        
        assert public_workspace.id == "workspace123"
        assert public_workspace.name == "Public Workspace"
        assert public_workspace.rol == WorkspaceRoles.VISITOR

    def test_workspace_public_response_serialization(self):
        """Test WorkspacePublicResponse serialization"""
        public_workspace = WorkspacePublicResponse(
            id="workspace123",
            name="Public Workspace",
            rol=WorkspaceRoles.VISITOR
        )
        
        serialized = public_workspace.model_dump()
        expected = {
            "id": "workspace123",
            "name": "Public Workspace",
            "rol": "visitor"
        }
        
        assert serialized == expected


class TestWorkspaceGuestModels:
    """Test workspace guest-related models"""

    def test_workspace_guest_create(self):
        """Test WorkspaceGuestCreate model"""
        guest_create = WorkspaceGuestCreate(
            guest="guest123",
            rol=WorkspaceRoles.VISITOR
        )
        
        assert guest_create.guest == "guest123"
        assert guest_create.rol == WorkspaceRoles.VISITOR

    def test_workspace_guest_update(self):
        """Test WorkspaceGuestUpdate model"""
        guest_update = WorkspaceGuestUpdate(rol=WorkspaceRoles.MANAGER)
        
        assert guest_update.rol == WorkspaceRoles.MANAGER

    def test_workspace_guest_delete(self):
        """Test WorkspaceGuestDelete model"""
        guest_delete = WorkspaceGuestDelete(
            workspace_id="workspace123",
            user="user123",
            guest="guest123"
        )
        
        assert guest_delete.workspace_id == "workspace123"
        assert guest_delete.user == "user123"
        assert guest_delete.guest == "guest123"


class TestWorkspaceConnectionPayload:
    """Test WorkspaceConnectionPayload model"""

    def test_workspace_connection_payload_creation(self):
        """Test creating a WorkspaceConnectionPayload model"""
        payload = WorkspaceConnectionPayload(
            id_workspace="workspace123",
            id_meter="meter456",
            exp=1234567890.0
        )
        
        assert payload.id_workspace == "workspace123"
        assert payload.id_meter == "meter456"
        assert payload.exp == 1234567890.0

    def test_workspace_connection_payload_serialization(self):
        """Test WorkspaceConnectionPayload serialization"""
        payload = WorkspaceConnectionPayload(
            id_workspace="workspace123",
            id_meter="meter456",
            exp=1234567890.0
        )
        
        serialized = payload.model_dump()
        expected = {
            "id_workspace": "workspace123",
            "id_meter": "meter456",
            "exp": 1234567890.0
        }
        
        assert serialized == expected