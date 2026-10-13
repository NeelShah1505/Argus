import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional


class BaseObjectStore(ABC):
    @abstractmethod
    def put_bytes(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        """Store bytes under key and return storage URI or key."""
        pass

    @abstractmethod
    def get_bytes(self, key: str) -> Optional[bytes]:
        """Retrieve stored bytes for key or return None."""
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if key exists in storage."""
        pass


class LocalObjectStore(BaseObjectStore):
    """
    Filesystem-backed object store.
    Guarantees fast, reproducible offline execution for tests and local dev.
    """

    def __init__(self, base_dir: str = ".argus_storage"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _resolve_path(self, key: str) -> Path:
        safe_key = key.lstrip("/")
        return self.base_dir / safe_key

    def put_bytes(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        target_path = self._resolve_path(key)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_bytes(data)
        return str(key)

    def get_bytes(self, key: str) -> Optional[bytes]:
        target_path = self._resolve_path(key)
        if not target_path.exists() or not target_path.is_file():
            return None
        return target_path.read_bytes()

    def exists(self, key: str) -> bool:
        target_path = self._resolve_path(key)
        return target_path.exists() and target_path.is_file()


_default_store: Optional[BaseObjectStore] = None


def get_object_store() -> BaseObjectStore:
    global _default_store
    if _default_store is None:
        storage_path = os.getenv("ARGUS_STORAGE_DIR", ".argus_storage")
        _default_store = LocalObjectStore(base_dir=storage_path)
    return _default_store
