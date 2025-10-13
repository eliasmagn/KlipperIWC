"""Amazon S3 storage backend implementation."""

from __future__ import annotations

import asyncio
import os
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - import hints only
    from botocore.client import BaseClient

__all__ = ["S3StorageBackend"]


class S3StorageBackend:
    """Persist assets in an S3 compatible object store."""

    def __init__(self, bucket: str, region: str | None = None, public_url: str | None = None) -> None:
        self.bucket = bucket
        self.region = region
        self.public_url = public_url.rstrip("/") if public_url else None
        self._client: "BaseClient" | None = None

    def _get_client(self) -> BaseClient:
        if self._client is None:
            try:
                import boto3
            except ImportError as exc:  # pragma: no cover - optional dependency
                raise RuntimeError(
                    "boto3 is required for the S3 storage backend. Install optional dependencies."
                ) from exc
            session_kwargs: dict[str, Any] = {}
            if self.region:
                session_kwargs["region_name"] = self.region
            session = boto3.session.Session(**session_kwargs)
            self._client = session.client(
                "s3",
                endpoint_url=os.getenv("BOARD_ASSET_S3_ENDPOINT"),
            )
        return self._client

    async def save(self, path: str, data: bytes, content_type: str | None = None) -> str:
        client = self._get_client()

        def _upload() -> None:
            put_kwargs = {
                "Bucket": self.bucket,
                "Key": path,
                "Body": data,
            }
            if content_type:
                put_kwargs["ContentType"] = content_type
            client.put_object(**put_kwargs)

        await asyncio.to_thread(_upload)
        if self.public_url:
            return f"{self.public_url}/{path}".rstrip("/")
        region = self.region or client.meta.region_name or ""
        if region:
            return f"https://{self.bucket}.s3.{region}.amazonaws.com/{path}"
        return f"https://{self.bucket}.s3.amazonaws.com/{path}"
