"""Service helpers to send control commands to a Klipper instance."""

from __future__ import annotations

import json
import logging
import os
from functools import lru_cache
from typing import Any

import httpx

logger = logging.getLogger(__name__)

__all__ = [
    "ControlServiceError",
    "KlipperControlService",
    "get_control_service",
]


class ControlServiceError(RuntimeError):
    """Error raised when a Klipper control command cannot be executed."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int = 502,
        details: Any | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.details = details


class KlipperControlService:
    """Client facade that forwards control commands to the Klipper API."""

    def __init__(
        self,
        base_url: str,
        *,
        api_key: str | None = None,
        timeout: float = 10.0,
        verify_ssl: bool | str = True,
    ) -> None:
        if not base_url:
            raise ValueError("A base URL for the Klipper API must be provided")
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._timeout = timeout
        self._verify_ssl = verify_ssl

    async def start_print(
        self,
        *,
        job_identifier: str | None = None,
        confirm_token: str | None = None,
    ) -> dict[str, Any]:
        """Send a start command to Klipper."""

        payload: dict[str, Any] = {}
        if job_identifier is not None:
            payload["job"] = job_identifier
        if confirm_token is not None:
            payload["confirm_token"] = confirm_token
        return await self._post("/printer/print/start", payload)

    async def stop_print(
        self,
        *,
        reason: str | None = None,
        confirm_token: str | None = None,
    ) -> dict[str, Any]:
        """Send a stop command to Klipper."""

        payload: dict[str, Any] = {}
        if reason:
            payload["reason"] = reason
        if confirm_token is not None:
            payload["confirm_token"] = confirm_token
        return await self._post("/printer/print/stop", payload)

    async def pause_print(
        self,
        *,
        reason: str | None = None,
        confirm_token: str | None = None,
    ) -> dict[str, Any]:
        """Send a pause command to Klipper."""

        payload: dict[str, Any] = {}
        if reason:
            payload["reason"] = reason
        if confirm_token is not None:
            payload["confirm_token"] = confirm_token
        return await self._post("/printer/print/pause", payload)

    async def emergency_stop(
        self,
        *,
        reason: str | None = None,
        confirm_token: str | None = None,
    ) -> dict[str, Any]:
        """Trigger an emergency stop in Klipper."""

        payload: dict[str, Any] = {}
        if reason:
            payload["reason"] = reason
        if confirm_token is not None:
            payload["confirm_token"] = confirm_token
        return await self._post("/printer/emergency_stop", payload)

    async def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        url = path if path.startswith("/") else f"/{path}"
        headers: dict[str, str] = {}
        if self._api_key:
            headers["X-Api-Key"] = self._api_key

        try:
            async with httpx.AsyncClient(
                base_url=self._base_url,
                timeout=self._timeout,
                verify=self._verify_ssl,
            ) as client:
                response = await client.post(url, json=payload or {}, headers=headers)
                response.raise_for_status()
        except httpx.HTTPStatusError as exc:  # pragma: no cover - defensive logging
            logger.warning(
                "Klipper API responded with HTTP %s: %s",
                exc.response.status_code,
                exc.response.text,
            )
            raise ControlServiceError(
                "Klipper API responded with an error",
                status_code=exc.response.status_code,
                details=self._extract_body(exc.response),
            ) from exc
        except httpx.RequestError as exc:  # pragma: no cover - defensive logging
            logger.error("Failed to reach Klipper API: %s", exc)
            raise ControlServiceError("Unable to reach Klipper API") from exc

        return self._extract_body(response)

    @staticmethod
    def _extract_body(response: httpx.Response) -> dict[str, Any]:
        if not response.content:
            return {"status": "ok"}
        content_type = response.headers.get("content-type", "")
        if "json" in content_type:
            try:
                data = response.json()
                if isinstance(data, dict):
                    return data
                return {"status": "ok", "payload": data}
            except json.JSONDecodeError:  # pragma: no cover - defensive logging
                logger.debug("Failed to decode JSON response from Klipper")
        return {"status": "ok", "raw_response": response.text}


@lru_cache(maxsize=1)
def _service_factory() -> KlipperControlService:
    base_url = os.getenv("KLIPPER_API_BASE_URL", "http://localhost:7125")
    api_key = os.getenv("KLIPPER_API_KEY")
    timeout = float(os.getenv("KLIPPER_API_TIMEOUT", "10"))
    verify_env = os.getenv("KLIPPER_API_VERIFY_SSL", "true").lower()
    verify_ssl: bool | str
    if verify_env in {"false", "0", "no"}:
        verify_ssl = False
    elif verify_env in {"true", "1", "yes"}:
        verify_ssl = True
    else:
        verify_ssl = verify_env
    return KlipperControlService(
        base_url,
        api_key=api_key,
        timeout=timeout,
        verify_ssl=verify_ssl,
    )


def get_control_service() -> KlipperControlService:
    """Return a cached control service instance configured via environment variables."""

    return _service_factory()
