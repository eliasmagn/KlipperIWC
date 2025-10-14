"""Utilities for managing and validating board definition files."""

from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Iterable

from jsonschema import Draft202012Validator
from pydantic import ValidationError

from klipperiwc.models import (
    BoardDefinition,
    BoardDefinitionSummary,
    BoardSchemaMetadata,
    BoardValidationResult,
    BoardVersionSummary,
)

__all__ = [
    "BoardRegistryError",
    "list_board_definitions",
    "list_board_versions",
    "validate_board_definition_file",
    "validate_all_board_definitions",
    "get_schema_metadata",
]

_SCHEMA_FILENAME = "board-definition.schema.json"


class BoardRegistryError(RuntimeError):
    """Raised when the registry configuration is invalid or unreadable."""


def _resolve_repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _resolve_schema_path(schema_path: Path | None = None) -> Path:
    if schema_path is not None:
        return schema_path
    env_value = os.getenv("BOARD_DEFINITION_SCHEMA")
    if env_value:
        return Path(env_value)
    return _resolve_repo_root() / "schemas" / _SCHEMA_FILENAME


def _resolve_registry_root(root_path: Path | None = None) -> Path:
    if root_path is not None:
        return root_path
    env_value = os.getenv("BOARD_DEFINITION_ROOT")
    if env_value:
        return Path(env_value)
    return _resolve_repo_root() / "board-definitions"


@lru_cache(maxsize=8)
def _load_schema(schema_path: str) -> dict:
    path = Path(schema_path)
    if not path.exists():
        raise BoardRegistryError(f"Board definition schema not found at {path}")
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except json.JSONDecodeError as exc:
        raise BoardRegistryError(f"Invalid JSON schema at {path}: {exc}") from exc


def _get_validator(schema: dict) -> Draft202012Validator:
    return Draft202012Validator(schema)


def _iter_definition_files(root: Path) -> Iterable[Path]:
    if not root.exists():
        return []
    if root.is_file():
        return [root]
    return sorted(
        (path for path in root.rglob("*.json") if path.is_file()),
        key=lambda item: item.as_posix(),
    )


def get_schema_metadata(schema_path: Path | None = None) -> BoardSchemaMetadata:
    resolved_path = _resolve_schema_path(schema_path)
    schema = _load_schema(str(resolved_path))
    version = schema.get("x-klipperiwc-version")
    if not version:
        raise BoardRegistryError(
            "Schema is missing the 'x-klipperiwc-version' annotation required for version tracking"
        )
    description = schema.get("description")
    return BoardSchemaMetadata(version=version, path=str(resolved_path), description=description)


def validate_board_definition_file(
    file_path: Path,
    *,
    schema_path: Path | None = None,
    schema: dict | None = None,
) -> BoardValidationResult:
    resolved_schema_path = _resolve_schema_path(schema_path)
    schema = schema or _load_schema(str(resolved_schema_path))
    validator = _get_validator(schema)
    try:
        with file_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except FileNotFoundError:
        return BoardValidationResult(
            path=str(file_path),
            is_valid=False,
            errors=["File not found"],
        )
    except json.JSONDecodeError as exc:
        return BoardValidationResult(
            path=str(file_path),
            is_valid=False,
            errors=[f"Invalid JSON: {exc}"],
        )

    schema_errors: list[str] = []
    for error in sorted(validator.iter_errors(payload), key=lambda err: (list(err.path), err.message)):
        location = "/".join(str(part) for part in error.path) or "<root>"
        schema_errors.append(f"{location}: {error.message}")

    if schema_errors:
        return BoardValidationResult(
            path=str(file_path),
            is_valid=False,
            schema_version=payload.get("schema_version"),
            errors=schema_errors,
        )

    try:
        definition = BoardDefinition.model_validate(payload)
    except ValidationError as exc:
        pydantic_errors = [
            f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}" for error in exc.errors()
        ]
        return BoardValidationResult(
            path=str(file_path),
            is_valid=False,
            schema_version=payload.get("schema_version"),
            errors=pydantic_errors,
        )

    supported_version = schema.get("x-klipperiwc-version")
    if supported_version and definition.schema_version != supported_version:
        return BoardValidationResult(
            path=str(file_path),
            is_valid=False,
            schema_version=definition.schema_version,
            errors=[
                (
                    f"Definition schema_version {definition.schema_version} is not supported; "
                    f"expected {supported_version}"
                )
            ],
        )

    summary = BoardDefinitionSummary.from_definition(definition, path=file_path)
    return BoardValidationResult(
        path=str(file_path),
        is_valid=True,
        schema_version=definition.schema_version,
        summary=summary,
    )


def validate_all_board_definitions(
    root_path: Path | None = None,
    *,
    schema_path: Path | None = None,
) -> list[BoardValidationResult]:
    root = _resolve_registry_root(root_path)
    resolved_schema_path = _resolve_schema_path(schema_path)
    schema = _load_schema(str(resolved_schema_path))
    results: list[BoardValidationResult] = []
    for definition_path in _iter_definition_files(root):
        results.append(
            validate_board_definition_file(
                Path(definition_path),
                schema_path=resolved_schema_path,
                schema=schema,
            )
        )
    return results


def list_board_definitions(
    root_path: Path | None = None,
    *,
    schema_path: Path | None = None,
) -> list[BoardDefinitionSummary]:
    results = validate_all_board_definitions(root_path, schema_path=schema_path)
    summaries = [result.summary for result in results if result.is_valid and result.summary]
    summaries = [summary for summary in summaries if summary is not None]
    return sorted(summaries, key=lambda item: (item.identifier, item.revision))


def list_board_versions(
    root_path: Path | None = None,
    *,
    schema_path: Path | None = None,
) -> list[BoardVersionSummary]:
    summaries = list_board_definitions(root_path, schema_path=schema_path)
    grouped: dict[str, list[BoardDefinitionSummary]] = {}
    for summary in summaries:
        grouped.setdefault(summary.identifier, []).append(summary)
    version_summaries = [
        BoardVersionSummary.from_summaries(identifier, items) for identifier, items in grouped.items()
    ]
    return sorted(version_summaries, key=lambda item: item.identifier)
