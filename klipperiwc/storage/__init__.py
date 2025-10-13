"""Storage backends for board asset uploads."""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Protocol

from .local import LocalStorageBackend
from .s3 import S3StorageBackend

__all__ = ["StorageBackend", "get_storage_backend"]


class StorageBackend(Protocol):
    """Protocol describing storage backend operations."""

    async def save(self, path: str, data: bytes, content_type: str | None = None) -> str:
        """Persist *data* at *path* and return a storage specific URI."""


@lru_cache(maxsize=1)
def get_storage_backend() -> StorageBackend:
    """Return the configured storage backend instance."""

    backend = os.getenv("BOARD_ASSET_STORAGE_BACKEND", "local").lower()
    if backend == "local":
        base_path = os.getenv("BOARD_ASSET_LOCAL_PATH", "./var/board-assets")
        public_url = os.getenv("BOARD_ASSET_LOCAL_PUBLIC_URL")
        return LocalStorageBackend(base_path=base_path, public_url=public_url)
    if backend == "s3":
        bucket = os.getenv("BOARD_ASSET_S3_BUCKET")
        if not bucket:
            raise RuntimeError("BOARD_ASSET_S3_BUCKET must be configured for S3 storage")
        region = os.getenv("BOARD_ASSET_S3_REGION")
        public_url = os.getenv("BOARD_ASSET_S3_PUBLIC_URL")
        return S3StorageBackend(bucket=bucket, region=region, public_url=public_url)
    raise RuntimeError(f"Unsupported storage backend: {backend}")
