"""Control endpoints to interact with a Klipper installation."""

from __future__ import annotations

from typing import Any, Awaitable, Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from klipperiwc.services.control import (
    ControlServiceError,
    KlipperControlService,
    get_control_service,
)

router = APIRouter(prefix="/api/control", tags=["control"])


class ControlCommandResponse(BaseModel):
    """Standard response returned by control endpoints."""

    acknowledged: bool = Field(True, description="Whether the command was forwarded")
    command: Literal["start", "stop", "pause", "emergency_stop"]
    upstream_response: dict[str, Any] | None = Field(
        default=None,
        description="Original response returned by the Klipper API",
    )


class _BaseControlRequest(BaseModel):
    confirm_token: str | None = Field(
        default=None,
        description="Optional token forwarded to Klipper for confirmation workflows.",
    )


class StartPrintRequest(_BaseControlRequest):
    job_identifier: str | None = Field(
        default=None,
        description="Optional explicit job identifier to hand over to Klipper.",
    )


class StopPrintRequest(_BaseControlRequest):
    reason: str | None = Field(
        default=None,
        description="Optional reason that is forwarded to the backend for logging.",
    )


class PausePrintRequest(_BaseControlRequest):
    reason: str | None = Field(
        default=None,
        description="Optional reason that is forwarded to the backend for logging.",
    )


class EmergencyStopRequest(_BaseControlRequest):
    reason: str | None = Field(
        default=None,
        description="Optional context for the emergency stop request.",
    )


async def _execute_command(
    command: Literal["start", "stop", "pause", "emergency_stop"],
    coroutine: Awaitable[dict[str, Any]],
) -> ControlCommandResponse:
    try:
        result = await coroutine
    except ControlServiceError as exc:
        detail: dict[str, Any] = {"message": str(exc)}
        if exc.details is not None:
            detail["details"] = exc.details
        raise HTTPException(status_code=exc.status_code, detail=detail) from exc
    return ControlCommandResponse(command=command, upstream_response=result)


@router.post("/start", response_model=ControlCommandResponse)
async def start_print(
    payload: StartPrintRequest,
    service: KlipperControlService = Depends(get_control_service),
) -> ControlCommandResponse:
    """Forward a start command to Klipper."""

    return await _execute_command(
        "start",
        service.start_print(
            job_identifier=payload.job_identifier,
            confirm_token=payload.confirm_token,
        ),
    )


@router.post("/stop", response_model=ControlCommandResponse)
async def stop_print(
    payload: StopPrintRequest,
    service: KlipperControlService = Depends(get_control_service),
) -> ControlCommandResponse:
    """Forward a stop command to Klipper."""

    return await _execute_command(
        "stop",
        service.stop_print(
            reason=payload.reason,
            confirm_token=payload.confirm_token,
        ),
    )


@router.post("/pause", response_model=ControlCommandResponse)
async def pause_print(
    payload: PausePrintRequest,
    service: KlipperControlService = Depends(get_control_service),
) -> ControlCommandResponse:
    """Forward a pause command to Klipper."""

    return await _execute_command(
        "pause",
        service.pause_print(
            reason=payload.reason,
            confirm_token=payload.confirm_token,
        ),
    )


@router.post("/emergency-stop", response_model=ControlCommandResponse)
async def emergency_stop(
    payload: EmergencyStopRequest,
    service: KlipperControlService = Depends(get_control_service),
) -> ControlCommandResponse:
    """Trigger an emergency stop via the Klipper API."""

    return await _execute_command(
        "emergency_stop",
        service.emergency_stop(
            reason=payload.reason,
            confirm_token=payload.confirm_token,
        ),
    )
