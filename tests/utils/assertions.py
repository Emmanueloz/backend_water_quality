"""
Custom assertion helpers for testing.
"""
from typing import Any, Dict, List, Optional, Union
import pytest
from fastapi.testclient import TestClient
from fastapi import Response
from app.share.workspace.domain.model import WorkspaceType, WorkspaceRoles, WorkspaceRolesAll


def assert_workspace_structure(workspace_data: Dict[str, Any], 
                              expected_fields: Optional[List[str]] = None) -> None:
    """Assert that workspace data has the expected structure."""
    default_fields = ["name", "type", "owner"]
    fields_to_check = expected_fields or default_fields
    
    for field in fields_to_check:
        assert field in workspace_data, f"Missing field: {field}"
        assert workspace_data[field] is not None, f"Field {field} should not be None"
    
    # Validate specific field types if present
    if "name" in workspace_data:
        assert isinstance(workspace_data["name"], str), "Workspace name must be a string"
        assert len(workspace_data["name"].strip()) >= 3, "Workspace name must be at least 3 characters"
        assert len(workspace_data["name"].strip()) <= 50, "Workspace name must be at most 50 characters"
    
    if "type" in workspace_data:
        valid_types = [WorkspaceType.PRIVATE, WorkspaceType.PUBLIC, "private", "public"]
        assert workspace_data["type"] in valid_types, f"Invalid workspace type: {workspace_data['type']}"
    
    if "owner" in workspace_data:
        assert isinstance(workspace_data["owner"], str), "Workspace owner must be a string"
        assert len(workspace_data["owner"]) > 0, "Workspace owner cannot be empty"


def assert_workspace_response_structure(response_data: Dict[str, Any],
                                       expected_fields: Optional[List[str]] = None) -> None:
    """Assert that workspace response data has the expected structure."""
    default_fields = ["id", "name", "type", "owner"]
    fields_to_check = expected_fields or default_fields
    
    assert_workspace_structure(response_data, fields_to_check)
    
    if "id" in response_data:
        assert isinstance(response_data["id"], str), "Workspace ID must be a string"
        assert len(response_data["id"]) > 0, "Workspace ID cannot be empty"
    
    if "rol" in response_data:
        valid_roles = list(WorkspaceRoles) + list(WorkspaceRolesAll) + ["visitor", "manager", "administrator", "owner", "unknown"]
        assert response_data["rol"] in valid_roles, f"Invalid workspace role: {response_data['rol']}"


def assert_user_structure(user_data: Dict[str, Any],
                         expected_fields: Optional[List[str]] = None) -> None:
    """Assert that user data has the expected structure."""
    default_fields = ["uid", "email", "username"]
    fields_to_check = expected_fields or default_fields
    
    for field in fields_to_check:
        assert field in user_data, f"Missing field: {field}"
        if field != "phone":  # phone can be None
            assert user_data[field] is not None, f"Field {field} should not be None"
    
    # Validate specific field formats
    if "email" in user_data and user_data["email"]:
        assert "@" in user_data["email"], "Email must contain @ symbol"
    
    if "uid" in user_data:
        assert isinstance(user_data["uid"], str), "User ID must be a string"
        assert len(user_data["uid"]) > 0, "User ID cannot be empty"
    
    if "username" in user_data:
        assert isinstance(user_data["username"], str), "Username must be a string"
        assert len(user_data["username"]) > 0, "Username cannot be empty"


def assert_api_response_structure(response: Union[Response, Dict[str, Any]],
                                 status_code: int = 200,
                                 expected_fields: Optional[List[str]] = None) -> None:
    """Assert that API response has the expected structure."""
    if hasattr(response, "status_code"):
        assert response.status_code == status_code, f"Expected status {status_code}, got {response.status_code}"
        response_json = response.json()
    else:
        assert response.get("status_code") == status_code
        response_json = response
    
    if expected_fields:
        for field in expected_fields:
            assert field in response_json, f"Missing field in response: {field}"


def assert_success_response(response: Union[Response, Dict[str, Any]],
                           expected_data_fields: Optional[List[str]] = None) -> Dict[str, Any]:
    """Assert successful API response and return the data."""
    assert_api_response_structure(response, 200)
    
    response_json = response.json() if hasattr(response, "json") else response
    
    # Check for common success response patterns
    if "data" in response_json:
        data = response_json["data"]
        if expected_data_fields:
            for field in expected_data_fields:
                assert field in data, f"Missing field in response data: {field}"
        return data
    elif "message" in response_json:
        return response_json
    else:
        return response_json


def assert_error_response(response: Union[Response, Dict[str, Any]],
                         expected_status_code: int,
                         expected_error_message: Optional[str] = None) -> None:
    """Assert that error response has the expected structure and content."""
    if hasattr(response, "status_code"):
        assert response.status_code == expected_status_code, f"Expected status {expected_status_code}, got {response.status_code}"
        response_json = response.json()
    else:
        assert response.get("status_code") == expected_status_code
        response_json = response
    
    # Check for error fields
    error_fields = ["error", "detail", "message"]
    has_error_field = any(field in response_json for field in error_fields)
    assert has_error_field, f"Response should contain one of: {error_fields}"
    
    if expected_error_message:
        error_msg = (response_json.get("error") or 
                    response_json.get("detail") or 
                    response_json.get("message"))
        assert expected_error_message.lower() in str(error_msg).lower(), \
            f"Expected '{expected_error_message}' in error message, got: {error_msg}"


def assert_validation_error(response: Union[Response, Dict[str, Any]],
                           field_name: Optional[str] = None) -> None:
    """Assert that response is a validation error (422)."""
    assert_error_response(response, 422)
    
    if field_name:
        response_json = response.json() if hasattr(response, "json") else response
        # FastAPI validation errors have a specific structure
        if "detail" in response_json and isinstance(response_json["detail"], list):
            field_errors = [error.get("loc", []) for error in response_json["detail"]]
            field_found = any(field_name in loc for loc in field_errors)
            assert field_found, f"Expected validation error for field '{field_name}'"


def assert_authentication_error(response: Union[Response, Dict[str, Any]]) -> None:
    """Assert that response is an authentication error (401)."""
    assert_error_response(response, 401)


def assert_authorization_error(response: Union[Response, Dict[str, Any]]) -> None:
    """Assert that response is an authorization error (403)."""
    assert_error_response(response, 403)


def assert_not_found_error(response: Union[Response, Dict[str, Any]]) -> None:
    """Assert that response is a not found error (404)."""
    assert_error_response(response, 404)


def assert_firebase_mock_state(firebase_mock, expected_data: Dict[str, Any]) -> None:
    """Assert that Firebase mock contains the expected data."""
    actual_data = firebase_mock.get_data()
    
    for path, expected_value in expected_data.items():
        keys = path.split("/")
        current = actual_data
        
        for key in keys:
            assert key in current, f"Missing key '{key}' in path '{path}'"
            current = current[key]
        
        assert current == expected_value, f"Expected {expected_value} at path '{path}', got {current}"


def assert_firebase_mock_path_exists(firebase_mock, path: str) -> None:
    """Assert that a specific path exists in Firebase mock."""
    ref = firebase_mock.reference(path)
    data = ref.get()
    assert data is not None, f"Path '{path}' should exist in Firebase mock"


def assert_firebase_mock_path_not_exists(firebase_mock, path: str) -> None:
    """Assert that a specific path does not exist in Firebase mock."""
    ref = firebase_mock.reference(path)
    data = ref.get()
    assert data is None, f"Path '{path}' should not exist in Firebase mock"


def assert_firebase_mock_called_with(mock_ref, method: str, *args, **kwargs) -> None:
    """Assert that Firebase mock was called with specific arguments."""
    if hasattr(mock_ref, method):
        mock_method = getattr(mock_ref, method)
        if hasattr(mock_method, "assert_called_with"):
            mock_method.assert_called_with(*args, **kwargs)


def assert_repository_method_called(mock_repo, method: str, call_count: int = 1) -> None:
    """Assert that repository method was called the expected number of times."""
    if hasattr(mock_repo, method):
        mock_method = getattr(mock_repo, method)
        if hasattr(mock_method, "call_count"):
            assert mock_method.call_count == call_count, \
                f"Expected {call_count} calls to {method}, got {mock_method.call_count}"


def assert_list_contains_items(items: List[Any], 
                              expected_count: Optional[int] = None,
                              item_validator: Optional[callable] = None) -> None:
    """Assert that list contains expected items."""
    assert isinstance(items, list), "Expected a list"
    
    if expected_count is not None:
        assert len(items) == expected_count, f"Expected {expected_count} items, got {len(items)}"
    
    if item_validator:
        for i, item in enumerate(items):
            try:
                item_validator(item)
            except AssertionError as e:
                raise AssertionError(f"Item at index {i} failed validation: {e}")


def assert_workspace_permissions(workspace_data: Dict[str, Any],
                                user_id: str,
                                expected_role: Union[WorkspaceRoles, WorkspaceRolesAll, str]) -> None:
    """Assert that workspace has correct permissions for user."""
    if "owner" in workspace_data and workspace_data["owner"] == user_id:
        expected_role = WorkspaceRolesAll.OWNER
    
    if "rol" in workspace_data:
        actual_role = workspace_data["rol"]
        assert actual_role == expected_role, \
            f"Expected role {expected_role} for user {user_id}, got {actual_role}"


def assert_database_consistency(firebase_mock, 
                               workspace_id: str,
                               expected_workspace_data: Dict[str, Any]) -> None:
    """Assert that database state is consistent after operations."""
    # Check workspace exists
    workspace_ref = firebase_mock.reference(f"workspaces/{workspace_id}")
    workspace_data = workspace_ref.get()
    
    assert workspace_data is not None, f"Workspace {workspace_id} should exist"
    
    for key, expected_value in expected_workspace_data.items():
        assert workspace_data.get(key) == expected_value, \
            f"Expected {key}={expected_value}, got {workspace_data.get(key)}"