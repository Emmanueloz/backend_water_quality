"""
Workspace test data fixtures and factories.
"""
from typing import Dict, Any, List
import uuid
import time
from app.share.workspace.domain.model import WorkspaceType, WorkspaceRoles, WorkspaceRolesAll


# Static test data for workspaces
WORKSPACE_TEST_DATA = {
    "valid_workspace": {
        "name": "Test Workspace",
        "type": WorkspaceType.PRIVATE,
        "owner": "test_user_id"
    },
    "public_workspace": {
        "name": "Public Test Workspace",
        "type": WorkspaceType.PUBLIC,
        "owner": "test_user_id"
    },
    "minimal_valid_workspace": {
        "name": "Min",  # Minimum 3 characters
        "type": WorkspaceType.PRIVATE,
        "owner": "test_user_id"
    },
    "max_length_workspace": {
        "name": "A" * 50,  # Maximum 50 characters
        "type": WorkspaceType.PRIVATE,
        "owner": "test_user_id"
    },
    "invalid_short_name": {
        "name": "AB",  # Too short (less than 3 characters)
        "type": WorkspaceType.PRIVATE,
        "owner": "test_user_id"
    },
    "invalid_long_name": {
        "name": "A" * 51,  # Too long (more than 50 characters)
        "type": WorkspaceType.PRIVATE,
        "owner": "test_user_id"
    },
    "invalid_empty_name": {
        "name": "",  # Empty name
        "type": WorkspaceType.PRIVATE,
        "owner": "test_user_id"
    },
    "invalid_whitespace_name": {
        "name": "   ",  # Only whitespace
        "type": WorkspaceType.PRIVATE,
        "owner": "test_user_id"
    }
}

# Workspace creation test data (for API requests)
WORKSPACE_CREATE_DATA = {
    "valid_create": {
        "name": "New Test Workspace",
        "type": WorkspaceType.PRIVATE
    },
    "public_create": {
        "name": "New Public Workspace",
        "type": WorkspaceType.PUBLIC
    },
    "minimal_create": {
        "name": "Min"
    },  # type defaults to PRIVATE
    "invalid_short_create": {
        "name": "AB",
        "type": WorkspaceType.PRIVATE
    },
    "invalid_long_create": {
        "name": "A" * 51,
        "type": WorkspaceType.PRIVATE
    }
}

# Workspace response test data
WORKSPACE_RESPONSE_DATA = {
    "basic_response": {
        "id": "workspace_123",
        "name": "Test Workspace",
        "type": WorkspaceType.PRIVATE,
        "owner": "test_user_id",
        "user": None,
        "rol": WorkspaceRolesAll.OWNER
    },
    "public_response": {
        "id": "workspace_456",
        "name": "Public Workspace",
        "type": WorkspaceType.PUBLIC,
        "owner": "test_user_id",
        "user": None,
        "rol": WorkspaceRolesAll.OWNER
    },
    "guest_response": {
        "id": "workspace_789",
        "name": "Shared Workspace",
        "type": WorkspaceType.PRIVATE,
        "owner": "owner_user_id",
        "user": None,
        "rol": WorkspaceRoles.VISITOR
    }
}

# Workspace sharing test data
WORKSPACE_SHARE_DATA = {
    "visitor_access": {
        "workspace_id": "test_workspace_id",
        "guest_user_id": "guest_user_id",
        "rol": WorkspaceRoles.VISITOR
    },
    "manager_access": {
        "workspace_id": "test_workspace_id",
        "guest_user_id": "manager_user_id",
        "rol": WorkspaceRoles.MANAGER
    },
    "admin_access": {
        "workspace_id": "test_workspace_id",
        "guest_user_id": "admin_user_id",
        "rol": WorkspaceRoles.ADMINISTRATOR
    }
}

# Guest management test data
WORKSPACE_GUEST_DATA = {
    "create_visitor": {
        "guest": "guest_user_id",
        "rol": WorkspaceRoles.VISITOR
    },
    "create_manager": {
        "guest": "manager_user_id",
        "rol": WorkspaceRoles.MANAGER
    },
    "create_admin": {
        "guest": "admin_user_id",
        "rol": WorkspaceRoles.ADMINISTRATOR
    },
    "update_role": {
        "rol": WorkspaceRoles.MANAGER
    },
    "delete_guest": {
        "workspace_id": "test_workspace_id",
        "user": "owner_user_id",
        "guest": "guest_user_id"
    }
}

# Database mock data structure
WORKSPACE_DATABASE_DATA = {
    "workspaces": {
        "workspace_123": {
            "name": "Test Workspace",
            "type": "private",
            "owner": "test_user_id"
        },
        "workspace_456": {
            "name": "Public Workspace",
            "type": "public",
            "owner": "test_user_id"
        },
        "workspace_789": {
            "name": "Shared Workspace",
            "type": "private",
            "owner": "owner_user_id"
        }
    },
    "guest_workspaces": {
        "guest_user_id": {
            "workspace_789": {
                "rol": "visitor"
            }
        },
        "manager_user_id": {
            "workspace_789": {
                "rol": "manager"
            }
        }
    }
}


def create_workspace_data(name: str = "Test Workspace", 
                         workspace_type: WorkspaceType = WorkspaceType.PRIVATE,
                         owner: str = "test_user_id") -> Dict[str, Any]:
    """Factory function to create workspace test data."""
    return {
        "name": name,
        "type": workspace_type,
        "owner": owner
    }


def create_workspace_create_data(name: str = "Test Workspace",
                                workspace_type: WorkspaceType = WorkspaceType.PRIVATE) -> Dict[str, Any]:
    """Factory function to create workspace creation request data."""
    return {
        "name": name,
        "type": workspace_type
    }


def create_workspace_response_data(workspace_id: str = None,
                                  name: str = "Test Workspace",
                                  workspace_type: WorkspaceType = WorkspaceType.PRIVATE,
                                  owner: str = "test_user_id",
                                  rol: WorkspaceRolesAll = WorkspaceRolesAll.OWNER) -> Dict[str, Any]:
    """Factory function to create workspace response test data."""
    if workspace_id is None:
        workspace_id = f"workspace_{uuid.uuid4().hex[:8]}"
    
    return {
        "id": workspace_id,
        "name": name,
        "type": workspace_type,
        "owner": owner,
        "user": None,
        "rol": rol
    }


def create_workspace_guest_data(guest_uid: str = "guest_user_id",
                               rol: WorkspaceRoles = WorkspaceRoles.VISITOR) -> Dict[str, Any]:
    """Factory function to create workspace guest creation data."""
    return {
        "guest": guest_uid,
        "rol": rol
    }


def create_guest_response_data(uid: str = "guest_user_id",
                              email: str = "guest@test.com",
                              username: str = "guestuser",
                              rol: WorkspaceRoles = WorkspaceRoles.VISITOR) -> Dict[str, Any]:
    """Factory function to create guest response data."""
    return {
        "uid": uid,
        "email": email,
        "username": username,
        "rol": rol
    }


def create_multiple_workspaces(count: int = 3, 
                              owner: str = "test_user_id") -> List[Dict[str, Any]]:
    """Factory function to create multiple workspace test data."""
    workspaces = []
    for i in range(count):
        workspace = create_workspace_data(
            name=f"Test Workspace {i+1}",
            workspace_type=WorkspaceType.PRIVATE if i % 2 == 0 else WorkspaceType.PUBLIC,
            owner=owner
        )
        workspaces.append(workspace)
    return workspaces


def create_database_mock_data(workspaces: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Factory function to create database mock data structure."""
    if workspaces is None:
        workspaces = [WORKSPACE_TEST_DATA["valid_workspace"]]
    
    mock_data = {
        "workspaces": {},
        "guest_workspaces": {}
    }
    
    for i, workspace in enumerate(workspaces):
        workspace_id = f"workspace_{i+1}"
        mock_data["workspaces"][workspace_id] = {
            "name": workspace["name"],
            "type": workspace["type"].value if hasattr(workspace["type"], 'value') else workspace["type"],
            "owner": workspace["owner"]
        }
    
    return mock_data