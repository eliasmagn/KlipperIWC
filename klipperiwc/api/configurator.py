"""API endpoints for the Klipper configuration builder."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from klipperiwc.models.configurator import (
    ComponentCategory,
    ConfigGenerationRequest,
    ConfigGenerationResponse,
    PrinterPreset,
)
from klipperiwc.configurator import (
    COMPONENT_CATEGORIES,
    PRESETS,
    build_configuration,
    get_category,
    get_preset,
)

router = APIRouter(prefix="/api/configurator", tags=["configurator"])


@router.get("/presets", response_model=list[PrinterPreset])
async def list_presets() -> list[PrinterPreset]:
    """Return all available printer presets."""

    return PRESETS


@router.get("/component-groups", response_model=list[ComponentCategory])
async def list_component_groups() -> list[ComponentCategory]:
    """Return configurable component categories."""

    return COMPONENT_CATEGORIES


@router.post("/generate", response_model=ConfigGenerationResponse)
async def generate_configuration(payload: ConfigGenerationRequest) -> ConfigGenerationResponse:
    """Create a Klipper configuration from the provided selection."""

    preset = get_preset(payload.printer_preset_id)
    if preset is None:
        raise HTTPException(status_code=404, detail="Unknown printer preset")

    categories = {category.id: category for category in COMPONENT_CATEGORIES}
    for category_id in payload.components:
        if get_category(category_id) is None:
            raise HTTPException(status_code=400, detail=f"Unknown component category: {category_id}")

    config, warnings = build_configuration(
        preset=preset,
        components=payload.components,
        custom_macros=payload.custom_macros,
        overrides=payload.parameter_overrides,
    )

    return ConfigGenerationResponse(configuration=config, warnings=warnings)
