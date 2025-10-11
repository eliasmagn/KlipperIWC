"""Status aggregation services for the API layer."""

from __future__ import annotations

import asyncio
from typing import Any, Mapping

from .klipper_client import KlipperClient


class StatusProvider:
    """Aggregate structured printer data for the public API."""

    def __init__(self, client: KlipperClient) -> None:
        self._client = client

    async def get_overview(self) -> Mapping[str, Any]:
        """Return a combined snapshot of printer, job and temperature data."""

        printer_task = asyncio.create_task(self._client.get_printer_status())
        job_task = asyncio.create_task(self._client.get_job_status())
        temps_task = asyncio.create_task(self._client.get_temperature_readings())
        server_task = asyncio.create_task(self._client.get_server_status())

        printer, job, temperatures, server = await asyncio.gather(
            printer_task, job_task, temps_task, server_task
        )

        return {
            "printer": printer,
            "job": job,
            "temperatures": temperatures,
            "server": server,
        }

    async def get_temperatures(self) -> Mapping[str, Any]:
        """Return only the temperature portion of the snapshot."""

        return await self._client.get_temperature_readings()

    async def get_job(self) -> Mapping[str, Any]:
        """Return only the job information."""

        return await self._client.get_job_status()
