"""Client abstractions for interacting with a Klipper (Moonraker) API."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

import httpx


class KlipperClient:
    """Async HTTP client for querying printer data from a Klipper installation."""

    def __init__(
        self,
        base_url: str,
        *,
        api_token: str | None = None,
        websocket_url: str | None = None,
        timeout: float = 10.0,
    ) -> None:
        if not base_url:
            raise ValueError("The Klipper base URL must not be empty.")

        self.base_url = base_url.rstrip("/")
        self.websocket_url = websocket_url
        headers: dict[str, str] = {}
        if api_token:
            headers["X-Api-Key"] = api_token

        self._client = httpx.AsyncClient(base_url=self.base_url, headers=headers, timeout=timeout)

    async def __aenter__(self) -> "KlipperClient":
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        """Close the underlying HTTP client."""

        await self._client.aclose()

    async def get_printer_status(self) -> Mapping[str, Any]:
        """Return general information about the printer instance."""

        return await self._get_json("/printer/info")

    async def get_job_status(self) -> Mapping[str, Any]:
        """Return information about the currently active job (if any)."""

        return await self._get_json("/printer/job/status")

    async def get_temperature_readings(
        self,
        objects: Iterable[str] | None = None,
    ) -> Mapping[str, Any]:
        """Return the latest temperature data for the provided printer objects."""

        if objects is None:
            objects = ("extruder", "heater_bed")

        query = {"objects": ",".join(objects)}
        return await self._get_json("/printer/objects/query", params=query)

    async def get_server_status(self) -> Mapping[str, Any]:
        """Return health and version information for the Klipper server."""

        return await self._get_json("/server/info")

    async def _get_json(
        self,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
    ) -> Mapping[str, Any]:
        response = await self._client.get(path, params=params)
        response.raise_for_status()
        return response.json()
