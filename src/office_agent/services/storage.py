from pathlib import Path
from typing import Protocol
class StorageBackend(Protocol):
    async def put(self, key: str, content: bytes) -> str: ...
    async def get(self, key: str) -> bytes: ...
    async def exists(self, key: str) -> bool: ...
    async def delete(self, key: str) -> None: ...
class LocalFileStorage:
    def __init__(self, root: Path): self.root = root; self.root.mkdir(parents=True, exist_ok=True)
    def _path(self, key):
        path = (self.root / key).resolve()
        if self.root.resolve() not in path.parents: raise ValueError("Invalid storage key")
        return path
    async def put(self, key, content):
        path = self._path(key); path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(content); return key
    async def get(self, key): return self._path(key).read_bytes()
    async def exists(self, key): return self._path(key).exists()
    async def delete(self, key):
        path = self._path(key)
        if path.exists(): path.unlink()
