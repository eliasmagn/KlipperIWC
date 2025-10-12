"""Websocket gateway responsible for broadcasting status updates."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from fastapi import APIRouter
from starlette.websockets import WebSocket, WebSocketDisconnect, WebSocketState

from klipperiwc.models import PrinterStatus

logger = logging.getLogger(__name__)

router = APIRouter()


class StatusBroadcaster:
    """Manage websocket listeners and fan out status updates."""

    def __init__(self) -> None:
        self._queues: set[asyncio.Queue[PrinterStatus]] = set()
        self._lock = asyncio.Lock()

    @property
    def connection_count(self) -> int:
        """Return the amount of active websocket listeners."""

        return len(self._queues)

    async def connect(self) -> asyncio.Queue[PrinterStatus]:
        """Register a new websocket listener and return its queue."""

        queue: asyncio.Queue[PrinterStatus] = asyncio.Queue(maxsize=1)
        async with self._lock:
            self._queues.add(queue)
        return queue

    async def disconnect(self, queue: asyncio.Queue[PrinterStatus]) -> None:
        """Remove a websocket listener from the broadcast pool."""

        async with self._lock:
            self._queues.discard(queue)

    async def publish(self, status: PrinterStatus) -> None:
        """Send a status update to all registered listeners."""

        async with self._lock:
            queues = list(self._queues)

        for queue in queues:
            try:
                queue.put_nowait(status)
            except asyncio.QueueFull:
                # Keep only the most recent payload for slow consumers.
                try:
                    _ = queue.get_nowait()
                except asyncio.QueueEmpty:  # pragma: no cover - defensive branch
                    pass
                queue.put_nowait(status)

    async def reset(self) -> None:
        """Remove all listeners (primarily for shutdown/test scenarios)."""

        async with self._lock:
            self._queues.clear()


status_broadcaster = StatusBroadcaster()


async def _authenticate(websocket: WebSocket) -> None:
    """Placeholder hook for future authentication handshake."""

    # TODO: Integrate actual authentication in phase 2.
    _ = websocket  # pragma: no cover - placeholder keeps linting quiet


def _client_identifier(websocket: WebSocket) -> str:
    client = websocket.client
    if client is None:
        return "unknown"
    return f"{client.host}:{client.port}"


def _enforce_rate_limit(_client_id: str) -> None:
    """Placeholder hook for future per-client rate limiting."""

    # TODO: Wire up rate limiting in phase 2.


@router.websocket("/ws/status")
async def status_stream(websocket: WebSocket) -> None:
    """Stream printer status updates to connected clients."""

    await _authenticate(websocket)
    client_id = _client_identifier(websocket)
    _enforce_rate_limit(client_id)
    await websocket.accept()
    queue = await status_broadcaster.connect()
    logger.debug("Client %s connected to status stream", client_id)

    try:
        while True:
            status = await queue.get()
            payload: dict[str, Any] = {
                "type": "status",
                "payload": status.model_dump(mode="json"),
            }
            await websocket.send_json(payload)
    except WebSocketDisconnect:
        logger.debug("Client %s disconnected from status stream", client_id)
    finally:
        await status_broadcaster.disconnect(queue)
        if websocket.application_state == WebSocketState.DISCONNECTED:
            logger.debug("Status stream cleaned up for %s", client_id)
        else:  # pragma: no cover - defensive logging
            logger.debug(
                "Status stream cleanup for %s (state=%s)",
                client_id,
                websocket.application_state,
            )
