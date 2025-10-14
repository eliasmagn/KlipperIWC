"""API endpoints for board definition registry management."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from klipperiwc.models import (
    BoardDefinitionSummary,
    BoardSchemaMetadata,
    BoardValidationResult,
    BoardVersionSummary,
)
from klipperiwc.services.board_registry import (
    BoardRegistryError,
    get_schema_metadata,
    list_board_definitions,
    list_board_versions,
    validate_all_board_definitions,
)

router = APIRouter(prefix="/api/boards", tags=["boards"])


@router.get("/definitions", response_model=list[BoardDefinitionSummary])
async def board_definitions() -> list[BoardDefinitionSummary]:
    """Return all board definitions that validate against the current schema."""
    try:
        return list_board_definitions()
    except BoardRegistryError as exc:  # pragma: no cover - defensive path
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/definitions/validate", response_model=list[BoardValidationResult])
async def board_definitions_validate() -> list[BoardValidationResult]:
    """Validate every board definition file and return detailed results."""
    try:
        return validate_all_board_definitions()
    except BoardRegistryError as exc:  # pragma: no cover - defensive path
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/versions", response_model=list[BoardVersionSummary])
async def board_version_matrix() -> list[BoardVersionSummary]:
    """Group definitions by identifier and surface the available revisions."""
    try:
        return list_board_versions()
    except BoardRegistryError as exc:  # pragma: no cover - defensive path
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/schema", response_model=BoardSchemaMetadata)
async def board_schema_metadata() -> BoardSchemaMetadata:
    """Expose the supported schema version and its on-disk location."""
    try:
        return get_schema_metadata()
    except BoardRegistryError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
