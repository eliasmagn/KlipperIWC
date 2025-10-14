"""Pydantic models representing structured board definitions."""

from __future__ import annotations

import re
from enum import Enum
from pathlib import Path
from typing import Iterable, Optional

from pydantic import (
    AnyUrl,
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    PositiveInt,
    field_validator,
    model_validator,
)


_SEMVER_PATTERN = re.compile(
    r"^(0|[1-9]\\d*)\\.(0|[1-9]\\d*)\\.(0|[1-9]\\d*)(?:-[0-9A-Za-z-.]+)?(?:\\+[0-9A-Za-z-.]+)?$"
)


class PinIORole(str, Enum):
    """Supported electrical roles for connector pins."""

    INPUT = "input"
    OUTPUT = "output"
    INOUT = "inout"
    POWER = "power"
    GROUND = "ground"
    NC = "nc"
    TEST = "test"


class BoardResource(BaseModel):
    """Reference to an external resource that complements a board definition."""

    type: str = Field(..., min_length=1, description="Kind of the resource (datasheet, schematic, cad, ...)")
    name: str = Field(..., min_length=1, description="Human readable resource name")
    uri: AnyUrl = Field(..., description="Link or URI pointing to the resource")

    model_config = ConfigDict(extra="forbid")


class BoardPinDefinition(BaseModel):
    """Detailed information for a single pin on a connector."""

    number: PositiveInt = Field(..., description="Position or index of the pin within the connector")
    signal: str = Field(..., min_length=1, description="Primary signal or function provided by the pin")
    name: Optional[str] = Field(None, description="Optional display label for the pin")
    io: Optional[PinIORole] = Field(
        None, description="Electrical role of the pin (input, output, power, etc.)"
    )
    voltage: Optional[str] = Field(None, description="Nominal voltage level or range")
    notes: Optional[str] = Field(None, description="Free-form notes or constraints")
    aliases: list[str] = Field(
        default_factory=list,
        description="Alternative labels that may appear on silkscreen or documentation",
    )

    model_config = ConfigDict(extra="forbid")

    @field_validator("aliases")
    @classmethod
    def _ensure_unique_aliases(cls, value: list[str]) -> list[str]:
        unique_aliases = list(dict.fromkeys(alias.strip() for alias in value if alias.strip()))
        if len(unique_aliases) != len(value):
            raise ValueError("aliases must be unique and non-empty when provided")
        return unique_aliases


class BoardConnectorDefinition(BaseModel):
    """A connector containing one or more pins."""

    id: str = Field(
        ...,
        pattern=r"^[A-Za-z0-9_.-]+$",
        description="Local identifier of the connector (e.g. J1, P2)",
    )
    name: str = Field(..., min_length=1, description="Display name of the connector")
    type: str = Field(..., min_length=1, description="Form factor or function of the connector")
    orientation: Optional[str] = Field(
        None, description="Orientation hint such as top/bottom/left/right"
    )
    description: Optional[str] = Field(
        None, description="Optional text describing the connector location or purpose"
    )
    pins: list[BoardPinDefinition] = Field(
        ..., min_length=1, description="Ordered list of pins belonging to the connector"
    )

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def _ensure_unique_pin_numbers(self) -> "BoardConnectorDefinition":
        numbers = [pin.number for pin in self.pins]
        if len(numbers) != len(set(numbers)):
            raise ValueError("pin numbers must be unique within a connector")
        return self


class BoardMetadata(BaseModel):
    """Descriptive metadata for a board definition."""

    identifier: str = Field(
        ...,
        pattern=r"^[A-Za-z0-9_.-]+$",
        description="Stable identifier used to reference the board",
    )
    name: str = Field(..., min_length=1, description="Human readable board name")
    manufacturer: str = Field(
        ..., min_length=1, description="Name of the board manufacturer or maintainer"
    )
    revision: str = Field(
        ..., min_length=1, description="Hardware revision or compatibility tag"
    )
    summary: Optional[str] = Field(None, description="Short abstract describing the board")
    documentation_url: Optional[HttpUrl] = Field(
        None, description="Link to the official board documentation"
    )
    tags: list[str] = Field(default_factory=list, description="Classification tags for the board")

    model_config = ConfigDict(extra="forbid")

    @field_validator("tags")
    @classmethod
    def _normalize_tags(cls, value: list[str]) -> list[str]:
        tags = [tag.strip() for tag in value if tag.strip()]
        if len(tags) != len(set(tags)):
            raise ValueError("tags must be unique and non-empty when provided")
        return tags


class BoardDefinition(BaseModel):
    """Full board definition including connectors, pins and metadata."""

    schema_version: str = Field(
        ...,
        description="Semantic version of the schema the definition conforms to",
        pattern=_SEMVER_PATTERN.pattern,
    )
    metadata: BoardMetadata
    connectors: list[BoardConnectorDefinition] = Field(
        ..., min_length=1, description="Connectors exposed by the board"
    )
    resources: list[BoardResource] = Field(
        default_factory=list,
        description="Supplementary resources such as datasheets or CAD models",
    )

    model_config = ConfigDict(extra="forbid")

    @field_validator("schema_version")
    @classmethod
    def _validate_schema_version(cls, value: str) -> str:
        if not _SEMVER_PATTERN.match(value):
            raise ValueError("schema_version must follow semantic versioning (MAJOR.MINOR.PATCH)")
        return value

    @model_validator(mode="after")
    def _ensure_unique_connectors(self) -> "BoardDefinition":
        connector_ids = [connector.id for connector in self.connectors]
        if len(connector_ids) != len(set(connector_ids)):
            raise ValueError("connector identifiers must be unique within a board definition")
        return self


class BoardDefinitionSummary(BaseModel):
    """Reduced view of a board definition for list endpoints."""

    identifier: str
    name: str
    manufacturer: str
    revision: str
    schema_version: str
    connectors: int = Field(..., ge=1, description="Number of connectors described by the definition")
    path: Optional[str] = Field(None, description="Source file path of the definition")
    tags: list[str] = Field(default_factory=list, description="Tags associated with the board")

    model_config = ConfigDict(extra="forbid")

    @classmethod
    def from_definition(
        cls, definition: BoardDefinition, *, path: str | Path | None = None
    ) -> "BoardDefinitionSummary":
        resolved_path = str(path) if path is not None else None
        return cls(
            identifier=definition.metadata.identifier,
            name=definition.metadata.name,
            manufacturer=definition.metadata.manufacturer,
            revision=definition.metadata.revision,
            schema_version=definition.schema_version,
            connectors=len(definition.connectors),
            path=resolved_path,
            tags=list(definition.metadata.tags),
        )


class BoardVersionSummary(BaseModel):
    """Aggregated revision information for a board identifier."""

    identifier: str
    name: str
    manufacturer: str
    revisions: list[str]
    latest_revision: str

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def _ensure_revision_order(self) -> "BoardVersionSummary":
        if not self.revisions:
            raise ValueError("revisions must contain at least one entry")
        unique_revisions = list(dict.fromkeys(self.revisions))
        unique_revisions.sort()
        self.revisions = unique_revisions
        self.latest_revision = unique_revisions[-1]
        return self

    @classmethod
    def from_summaries(
        cls, identifier: str, summaries: Iterable[BoardDefinitionSummary]
    ) -> "BoardVersionSummary":
        summaries = list(summaries)
        if not summaries:
            raise ValueError("summaries must not be empty")
        name = summaries[0].name
        manufacturer = summaries[0].manufacturer
        revisions = [summary.revision for summary in summaries]
        return cls(
            identifier=identifier,
            name=name,
            manufacturer=manufacturer,
            revisions=revisions,
            latest_revision=summaries[0].revision,
        )


class BoardValidationResult(BaseModel):
    """Result of validating a board definition file."""

    path: str
    is_valid: bool
    schema_version: Optional[str] = None
    errors: list[str] = Field(default_factory=list)
    summary: Optional[BoardDefinitionSummary] = None

    model_config = ConfigDict(extra="forbid")


class BoardSchemaMetadata(BaseModel):
    """Information about the currently supported board definition schema."""

    version: str
    path: str
    description: Optional[str] = None

    model_config = ConfigDict(extra="forbid")
