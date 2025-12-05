"""
Firebase mock utilities for testing.
Provides mock implementations for Firebase Realtime Database operations.
"""
from typing import Any, Dict, Optional, List
import copy
import uuid


class FirebaseMock:
    """Mock implementation of Firebase Realtime Database."""
    
    def __init__(self):
        """Initialize Firebase mock with empty data storage."""
        self._data: Dict[str, Any] = {}
        self._refs: Dict[str, 'FirebaseRefMock'] = {}
    
    def reference(self, path: Optional[str] = None) -> 'FirebaseRefMock':
        """Get a reference to a Firebase path."""
        if path is None:
            path = ""
        
        # Normalize path (remove leading/trailing slashes)
        path = path.strip("/")
        
        # Create or reuse reference
        if path not in self._refs:
            self._refs[path] = FirebaseRefMock(path, self)
        
        return self._refs[path]
    
    def reset(self) -> None:
        """Reset all data and references."""
        self._data.clear()
        self._refs.clear()
    
    def get_data(self) -> Dict[str, Any]:
        """Get a copy of all stored data."""
        return copy.deepcopy(self._data)
    
    def set_data(self, data: Dict[str, Any]) -> None:
        """Set the entire data structure."""
        self._data = copy.deepcopy(data)
    
    def _get_nested_value(self, path: str) -> Any:
        """Get value at nested path."""
        if not path:
            return self._data
        
        keys = path.split("/")
        current = self._data
        
        for key in keys:
            if not isinstance(current, dict) or key not in current:
                return None
            current = current[key]
        
        return current
    
    def _set_nested_value(self, path: str, value: Any) -> None:
        """Set value at nested path."""
        if not path:
            if isinstance(value, dict):
                self._data = value
            else:
                raise ValueError("Root value must be a dictionary")
            return
        
        keys = path.split("/")
        current = self._data
        
        # Navigate to parent of target key
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            elif not isinstance(current[key], dict):
                current[key] = {}
            current = current[key]
        
        # Set the final value
        current[keys[-1]] = value
    
    def _delete_nested_value(self, path: str) -> None:
        """Delete value at nested path."""
        if not path:
            self._data.clear()
            return
        
        keys = path.split("/")
        current = self._data
        
        # Navigate to parent of target key
        for key in keys[:-1]:
            if not isinstance(current, dict) or key not in current:
                return  # Path doesn't exist
            current = current[key]
        
        # Delete the final key
        if isinstance(current, dict) and keys[-1] in current:
            del current[keys[-1]]
    
    def _update_nested_value(self, path: str, updates: Dict[str, Any]) -> None:
        """Update values at nested path."""
        current_value = self._get_nested_value(path)
        
        if current_value is None:
            # Create new dict if path doesn't exist
            self._set_nested_value(path, updates)
        elif isinstance(current_value, dict):
            # Update existing dict
            updated_value = copy.deepcopy(current_value)
            updated_value.update(updates)
            self._set_nested_value(path, updated_value)
        else:
            # Replace non-dict value with updates
            self._set_nested_value(path, updates)
    
    def _generate_push_key(self) -> str:
        """Generate a unique key for push operations."""
        return str(uuid.uuid4()).replace("-", "")[:20]


class FirebaseRefMock:
    """Mock implementation of Firebase database reference."""
    
    def __init__(self, path: str, mock_instance: 'FirebaseMock'):
        """Initialize Firebase reference mock."""
        self._path = path
        self._mock = mock_instance
        self._key = None  # Will be set when created via push()
    
    @property
    def key(self) -> Optional[str]:
        """Get the key of this reference (last segment of path)."""
        if self._key is not None:
            return self._key
        if not self._path:
            return None
        return self._path.split("/")[-1]
    
    @property
    def path(self) -> str:
        """Get the path of this reference."""
        return self._path
    
    def child(self, path: str) -> 'FirebaseRefMock':
        """Get a child reference."""
        if not path:
            return self
        
        # Combine paths
        if self._path:
            child_path = f"{self._path}/{path.strip('/')}"
        else:
            child_path = path.strip("/")
        
        return self._mock.reference(child_path)
    
    def get(self) -> Any:
        """Get the value at this reference."""
        return self._mock._get_nested_value(self._path)
    
    def set(self, value: Any) -> None:
        """Set the value at this reference."""
        self._mock._set_nested_value(self._path, value)
    
    def update(self, values: Dict[str, Any]) -> None:
        """Update values at this reference."""
        self._mock._update_nested_value(self._path, values)
    
    def delete(self) -> None:
        """Delete the value at this reference."""
        self._mock._delete_nested_value(self._path)
    
    def push(self, value: Any) -> 'FirebaseRefMock':
        """Push a new value and return reference to the new location."""
        push_key = self._mock._generate_push_key()
        child_ref = self.child(push_key)
        child_ref._key = push_key  # Set the key for the pushed reference
        child_ref.set(value)
        return child_ref
    
    def order_by_child(self, key: str) -> 'FirebaseQueryMock':
        """Create a query ordered by child key."""
        return FirebaseQueryMock(self, order_by=key)
    
    def order_by_key(self) -> 'FirebaseQueryMock':
        """Create a query ordered by key."""
        return FirebaseQueryMock(self, order_by="$key")
    
    def order_by_value(self) -> 'FirebaseQueryMock':
        """Create a query ordered by value."""
        return FirebaseQueryMock(self, order_by="$value")
    
    def limit_to_first(self, limit: int) -> 'FirebaseQueryMock':
        """Create a query limited to first N results."""
        return FirebaseQueryMock(self, limit_first=limit)
    
    def limit_to_last(self, limit: int) -> 'FirebaseQueryMock':
        """Create a query limited to last N results."""
        return FirebaseQueryMock(self, limit_last=limit)
    
    def equal_to(self, value: Any) -> 'FirebaseQueryMock':
        """Create a query filtered by equal value."""
        return FirebaseQueryMock(self, equal_to=value)
    
    def start_at(self, value: Any) -> 'FirebaseQueryMock':
        """Create a query starting at value."""
        return FirebaseQueryMock(self, start_at=value)
    
    def end_at(self, value: Any) -> 'FirebaseQueryMock':
        """Create a query ending at value."""
        return FirebaseQueryMock(self, end_at=value)


class FirebaseQueryMock:
    """Mock implementation of Firebase query operations."""
    
    def __init__(self, ref_mock: FirebaseRefMock, **query_params):
        """Initialize Firebase query mock."""
        self._ref = ref_mock
        self._order_by = query_params.get('order_by')
        self._equal_to = query_params.get('equal_to')
        self._start_at = query_params.get('start_at')
        self._end_at = query_params.get('end_at')
        self._limit_first = query_params.get('limit_first')
        self._limit_last = query_params.get('limit_last')
    
    def equal_to(self, value: Any) -> 'FirebaseQueryMock':
        """Filter results equal to value."""
        return FirebaseQueryMock(
            self._ref,
            order_by=self._order_by,
            equal_to=value,
            start_at=self._start_at,
            end_at=self._end_at,
            limit_first=self._limit_first,
            limit_last=self._limit_last
        )
    
    def start_at(self, value: Any) -> 'FirebaseQueryMock':
        """Filter results starting at value."""
        return FirebaseQueryMock(
            self._ref,
            order_by=self._order_by,
            equal_to=self._equal_to,
            start_at=value,
            end_at=self._end_at,
            limit_first=self._limit_first,
            limit_last=self._limit_last
        )
    
    def end_at(self, value: Any) -> 'FirebaseQueryMock':
        """Filter results ending at value."""
        return FirebaseQueryMock(
            self._ref,
            order_by=self._order_by,
            equal_to=self._equal_to,
            start_at=self._start_at,
            end_at=value,
            limit_first=self._limit_first,
            limit_last=self._limit_last
        )
    
    def limit_to_first(self, limit: int) -> 'FirebaseQueryMock':
        """Limit results to first N items."""
        return FirebaseQueryMock(
            self._ref,
            order_by=self._order_by,
            equal_to=self._equal_to,
            start_at=self._start_at,
            end_at=self._end_at,
            limit_first=limit,
            limit_last=self._limit_last
        )
    
    def limit_to_last(self, limit: int) -> 'FirebaseQueryMock':
        """Limit results to last N items."""
        return FirebaseQueryMock(
            self._ref,
            order_by=self._order_by,
            equal_to=self._equal_to,
            start_at=self._start_at,
            end_at=self._end_at,
            limit_first=self._limit_first,
            limit_last=limit
        )
    
    def get(self) -> Dict[str, Any]:
        """Execute the query and return results."""
        data = self._ref.get()
        
        if not isinstance(data, dict):
            return {} if data is None else data
        
        # Apply filtering and ordering
        results = self._apply_filters(data)
        results = self._apply_ordering(results)
        results = self._apply_limits(results)
        
        return results
    
    def _apply_filters(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply equal_to, start_at, and end_at filters."""
        if not isinstance(data, dict):
            return data
        
        filtered = {}
        
        for key, value in data.items():
            # Apply equal_to filter
            if self._equal_to is not None:
                if self._order_by == "$key":
                    if key != self._equal_to:
                        continue
                elif self._order_by == "$value":
                    if value != self._equal_to:
                        continue
                elif self._order_by and isinstance(value, dict):
                    if value.get(self._order_by) != self._equal_to:
                        continue
                else:
                    continue
            
            # Apply start_at filter
            if self._start_at is not None:
                if self._order_by == "$key":
                    if key < self._start_at:
                        continue
                elif self._order_by == "$value":
                    if value < self._start_at:
                        continue
                elif self._order_by and isinstance(value, dict):
                    if value.get(self._order_by, "") < self._start_at:
                        continue
            
            # Apply end_at filter
            if self._end_at is not None:
                if self._order_by == "$key":
                    if key > self._end_at:
                        continue
                elif self._order_by == "$value":
                    if value > self._end_at:
                        continue
                elif self._order_by and isinstance(value, dict):
                    if value.get(self._order_by, "") > self._end_at:
                        continue
            
            filtered[key] = value
        
        return filtered
    
    def _apply_ordering(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply ordering to the data."""
        if not isinstance(data, dict) or not self._order_by:
            return data
        
        items = list(data.items())
        
        if self._order_by == "$key":
            items.sort(key=lambda x: x[0])
        elif self._order_by == "$value":
            items.sort(key=lambda x: x[1])
        else:
            # Order by child key
            def get_sort_key(item):
                key, value = item
                if isinstance(value, dict):
                    return value.get(self._order_by, "")
                return ""
            
            items.sort(key=get_sort_key)
        
        return dict(items)
    
    def _apply_limits(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply limit_to_first and limit_to_last."""
        if not isinstance(data, dict):
            return data
        
        items = list(data.items())
        
        if self._limit_first is not None:
            items = items[:self._limit_first]
        elif self._limit_last is not None:
            items = items[-self._limit_last:]
        
        return dict(items)