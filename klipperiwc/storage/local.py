"""Local filesystem storage backend."""

from __future__ import annotations

import asyncio
from pathlib import Path

__all__ = ["LocalStorageBackend"]


class LocalStorageBackend:
    """Store assets on the local filesystem."""

    def __init__(self, base_path: str, public_url: str | None = None) -> None:
        self.base_path = Path(base_path)
        self.public_url = public_url.rstrip("/") if public_url else None

    async def save(self, path: str, data: bytes, content_type: str | None = None) -> str:
        target = self.base_path.joinpath(path)

        def _write() -> None:
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("wb") as handle:
                handle.write(data)

        await asyncio.to_thread(_write)
        if self.public_url:
            return f"{self.public_url}/{path.lstrip('/')}"
        return str(target.resolve())
