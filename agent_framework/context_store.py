from typing import Dict, Any, Set, Optional
import threading


class ContextStore:
    """A shared, access-controlled context store for agents.

    Agents can create namespaces (e.g., "planning", "code", "tests") and store
    structured data. Access is controlled via allow-lists per namespace.
    """

    def __init__(self):
        self._data: Dict[str, Dict[str, Any]] = {}
        self._acl_read: Dict[str, Set[str]] = {}
        self._acl_write: Dict[str, Set[str]] = {}
        self._lock = threading.RLock()

    def create_namespace(self, name: str, readers: Optional[Set[str]] = None, writers: Optional[Set[str]] = None) -> None:
        with self._lock:
            if name not in self._data:
                self._data[name] = {}
            self._acl_read[name] = set(readers or set())
            self._acl_write[name] = set(writers or set())

    def grant(self, namespace: str, agent_id: str, read: bool = False, write: bool = False) -> None:
        with self._lock:
            if read:
                self._acl_read.setdefault(namespace, set()).add(agent_id)
            if write:
                self._acl_write.setdefault(namespace, set()).add(agent_id)

    def revoke(self, namespace: str, agent_id: str, read: bool = False, write: bool = False) -> None:
        with self._lock:
            if read and namespace in self._acl_read:
                self._acl_read[namespace].discard(agent_id)
            if write and namespace in self._acl_write:
                self._acl_write[namespace].discard(agent_id)

    def set(self, namespace: str, key: str, value: Any, agent_id: str) -> bool:
        with self._lock:
            if agent_id not in self._acl_write.get(namespace, set()):
                return False
            self._data.setdefault(namespace, {})[key] = value
            return True

    def get(self, namespace: str, key: str, agent_id: str) -> Any:
        with self._lock:
            if agent_id not in self._acl_read.get(namespace, set()):
                return None
            return self._data.get(namespace, {}).get(key)

    def list_namespace(self, namespace: str, agent_id: str) -> Dict[str, Any]:
        with self._lock:
            if agent_id not in self._acl_read.get(namespace, set()):
                return {}
            return dict(self._data.get(namespace, {}))


