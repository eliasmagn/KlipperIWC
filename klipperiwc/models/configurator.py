"""Pydantic models for the configuration builder API."""

from __future__ import annotations

from typing import Dict, List

from pydantic import BaseModel, Field


class ComponentOption(BaseModel):
    """Selectable option within a component category."""

    id: str = Field(..., description="Unique identifier for the option")
    label: str = Field(..., description="Human readable name")
    description: str = Field(..., description="Short explanation of what the option represents")
    config_snippet: str = Field(
        "", description="Klipper configuration snippet that will be merged into the final file"
    )


class ComponentCategory(BaseModel):
    """Group of related component options."""

    id: str
    label: str
    description: str
    options: List[ComponentOption]


class PrinterPreset(BaseModel):
    """Base printer template with default selections."""

    id: str
    name: str
    description: str
    base_template: str = Field(..., description="Base Klipper configuration template")
    default_components: Dict[str, str] = Field(
        default_factory=dict, description="Mapping of component category id to default option id"
    )


class ConfigGenerationRequest(BaseModel):
    """Request payload for creating a configuration file."""

    printer_preset_id: str = Field(..., description="Selected printer preset identifier")
    components: Dict[str, str] = Field(
        default_factory=dict,
        description="Mapping from component category id to selected option id",
    )
    parameter_overrides: Dict[str, str] | None = Field(
        default=None,
        description="Optional dictionary of manual override values added as a section",
    )
    custom_macros: List[str] | None = Field(
        default=None,
        description="Optional list of custom macros appended to the configuration",
    )


class ConfigGenerationResponse(BaseModel):
    """Response containing the generated configuration and potential warnings."""

    configuration: str
    warnings: List[str] = Field(default_factory=list)

