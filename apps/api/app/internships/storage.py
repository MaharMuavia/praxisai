import hashlib
from pathlib import Path


class LocalInternshipStorage:
    """Private, path-traversal-safe storage for local and demo environments."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def _path(self, storage_key: str) -> Path:
        candidate = (self.root / storage_key).resolve()
        if self.root not in candidate.parents:
            raise ValueError("Storage key escapes the private upload root")
        return candidate

    def put(self, storage_key: str, content: bytes) -> str:
        target = self._path(storage_key)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        return hashlib.sha256(content).hexdigest()

    def read(self, storage_key: str) -> bytes:
        return self._path(storage_key).read_bytes()
