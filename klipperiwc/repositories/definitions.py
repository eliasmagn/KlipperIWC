"""Repository helpers for board and printer definition documents."""

from __future__ import annotations

from typing import Iterable, Type

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from klipperiwc.db.models import BoardDefinitionDocument, PrinterDefinitionDocument

__all__ = [
    "DefinitionConflictError",
    "DefinitionNotFoundError",
    "create_board_definition",
    "update_board_definition",
    "list_board_definitions",
    "get_board_definition",
    "create_printer_definition",
    "update_printer_definition",
    "list_printer_definitions",
    "get_printer_definition",
]


class DefinitionConflictError(RuntimeError):
    """Raised when attempting to create a definition with a duplicate slug."""


class DefinitionNotFoundError(RuntimeError):
    """Raised when a requested definition does not exist."""


DefinitionModel = Type[BoardDefinitionDocument | PrinterDefinitionDocument]


def _create_definition(
    session: Session,
    model: DefinitionModel,
    *,
    slug: str,
    name: str,
    description: str | None,
    preview_image_uri: str | None,
    data: dict,
) -> BoardDefinitionDocument | PrinterDefinitionDocument:
    entity = model(
        slug=slug,
        name=name,
        description=description,
        preview_image_uri=preview_image_uri,
        data=data,
    )
    session.add(entity)
    try:
        session.flush()
    except IntegrityError as exc:
        session.rollback()
        raise DefinitionConflictError(f"Definition with slug '{slug}' already exists") from exc
    return entity


def _get_by_slug(
    session: Session, model: DefinitionModel, slug: str
) -> BoardDefinitionDocument | PrinterDefinitionDocument:
    statement = select(model).where(model.slug == slug)
    entity = session.scalar(statement)
    if entity is None:
        raise DefinitionNotFoundError(f"Definition '{slug}' was not found")
    return entity


def _list_definitions(
    session: Session, model: DefinitionModel
) -> Iterable[BoardDefinitionDocument | PrinterDefinitionDocument]:
    statement = select(model).order_by(model.created_at.desc())
    return session.scalars(statement)


def _update_definition(
    session: Session,
    model: DefinitionModel,
    slug: str,
    *,
    name: str | None = None,
    description: str | None = None,
    preview_image_uri: str | None = None,
    data: dict | None = None,
) -> BoardDefinitionDocument | PrinterDefinitionDocument:
    entity = _get_by_slug(session, model, slug)
    if name is not None:
        entity.name = name
    if description is not None:
        entity.description = description
    if preview_image_uri is not None:
        entity.preview_image_uri = preview_image_uri
    if data is not None:
        entity.data = data
    session.flush()
    return entity


def create_board_definition(
    session: Session,
    *,
    slug: str,
    name: str,
    description: str | None,
    preview_image_uri: str | None,
    data: dict,
) -> BoardDefinitionDocument:
    return _create_definition(
        session,
        BoardDefinitionDocument,
        slug=slug,
        name=name,
        description=description,
        preview_image_uri=preview_image_uri,
        data=data,
    )


def update_board_definition(
    session: Session,
    slug: str,
    *,
    name: str | None = None,
    description: str | None = None,
    preview_image_uri: str | None = None,
    data: dict | None = None,
) -> BoardDefinitionDocument:
    return _update_definition(
        session,
        BoardDefinitionDocument,
        slug,
        name=name,
        description=description,
        preview_image_uri=preview_image_uri,
        data=data,
    )


def list_board_definitions(session: Session) -> list[BoardDefinitionDocument]:
    return list(_list_definitions(session, BoardDefinitionDocument))


def get_board_definition(session: Session, slug: str) -> BoardDefinitionDocument:
    return _get_by_slug(session, BoardDefinitionDocument, slug)


def create_printer_definition(
    session: Session,
    *,
    slug: str,
    name: str,
    description: str | None,
    preview_image_uri: str | None,
    data: dict,
) -> PrinterDefinitionDocument:
    return _create_definition(
        session,
        PrinterDefinitionDocument,
        slug=slug,
        name=name,
        description=description,
        preview_image_uri=preview_image_uri,
        data=data,
    )


def update_printer_definition(
    session: Session,
    slug: str,
    *,
    name: str | None = None,
    description: str | None = None,
    preview_image_uri: str | None = None,
    data: dict | None = None,
) -> PrinterDefinitionDocument:
    return _update_definition(
        session,
        PrinterDefinitionDocument,
        slug,
        name=name,
        description=description,
        preview_image_uri=preview_image_uri,
        data=data,
    )


def list_printer_definitions(session: Session) -> list[PrinterDefinitionDocument]:
    return list(_list_definitions(session, PrinterDefinitionDocument))


def get_printer_definition(session: Session, slug: str) -> PrinterDefinitionDocument:
    return _get_by_slug(session, PrinterDefinitionDocument, slug)
