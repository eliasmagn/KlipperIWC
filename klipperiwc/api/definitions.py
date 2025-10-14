"""API endpoints for storing board and printer definition documents."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from klipperiwc.db.session import get_session
from klipperiwc.models import DefinitionCreate, DefinitionResponse, DefinitionUpdate
from klipperiwc.repositories import (
    DefinitionConflictError,
    DefinitionNotFoundError,
    create_board_definition,
    create_printer_definition,
    get_board_definition,
    get_printer_definition,
    list_board_definitions,
    list_printer_definitions,
    update_board_definition,
    update_printer_definition,
)

router = APIRouter(prefix="/api/definitions", tags=["definitions"])


def _serialize(document) -> DefinitionResponse:
    return DefinitionResponse(
        id=document.id,
        slug=document.slug,
        name=document.name,
        description=document.description,
        preview_image_url=document.preview_image_uri,
        data=document.data,
        created_at=document.created_at,
        updated_at=document.updated_at,
    )


@router.post("/boards", response_model=DefinitionResponse, status_code=status.HTTP_201_CREATED)
def create_board_definition_endpoint(
    payload: DefinitionCreate, session: Session = Depends(get_session)
) -> DefinitionResponse:
    try:
        document = create_board_definition(
            session,
            slug=payload.slug,
            name=payload.name,
            description=payload.description,
            preview_image_uri=str(payload.preview_image_url) if payload.preview_image_url else None,
            data=payload.data,
        )
        session.commit()
        session.refresh(document)
    except DefinitionConflictError as exc:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return _serialize(document)


@router.get("/boards", response_model=list[DefinitionResponse])
def list_board_definitions_endpoint(session: Session = Depends(get_session)) -> list[DefinitionResponse]:
    documents = list_board_definitions(session)
    return [_serialize(document) for document in documents]


@router.get("/boards/{slug}", response_model=DefinitionResponse)
def get_board_definition_endpoint(slug: str, session: Session = Depends(get_session)) -> DefinitionResponse:
    try:
        document = get_board_definition(session, slug)
    except DefinitionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return _serialize(document)


@router.put("/boards/{slug}", response_model=DefinitionResponse)
def update_board_definition_endpoint(
    slug: str, payload: DefinitionUpdate, session: Session = Depends(get_session)
) -> DefinitionResponse:
    try:
        document = update_board_definition(
            session,
            slug,
            name=payload.name,
            description=payload.description,
            preview_image_uri=str(payload.preview_image_url) if payload.preview_image_url else None,
            data=payload.data,
        )
        session.commit()
        session.refresh(document)
    except DefinitionNotFoundError as exc:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return _serialize(document)


@router.post("/printers", response_model=DefinitionResponse, status_code=status.HTTP_201_CREATED)
def create_printer_definition_endpoint(
    payload: DefinitionCreate, session: Session = Depends(get_session)
) -> DefinitionResponse:
    try:
        document = create_printer_definition(
            session,
            slug=payload.slug,
            name=payload.name,
            description=payload.description,
            preview_image_uri=str(payload.preview_image_url) if payload.preview_image_url else None,
            data=payload.data,
        )
        session.commit()
        session.refresh(document)
    except DefinitionConflictError as exc:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return _serialize(document)


@router.get("/printers", response_model=list[DefinitionResponse])
def list_printer_definitions_endpoint(session: Session = Depends(get_session)) -> list[DefinitionResponse]:
    documents = list_printer_definitions(session)
    return [_serialize(document) for document in documents]


@router.get("/printers/{slug}", response_model=DefinitionResponse)
def get_printer_definition_endpoint(slug: str, session: Session = Depends(get_session)) -> DefinitionResponse:
    try:
        document = get_printer_definition(session, slug)
    except DefinitionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return _serialize(document)


@router.put("/printers/{slug}", response_model=DefinitionResponse)
def update_printer_definition_endpoint(
    slug: str, payload: DefinitionUpdate, session: Session = Depends(get_session)
) -> DefinitionResponse:
    try:
        document = update_printer_definition(
            session,
            slug,
            name=payload.name,
            description=payload.description,
            preview_image_uri=str(payload.preview_image_url) if payload.preview_image_url else None,
            data=payload.data,
        )
        session.commit()
        session.refresh(document)
    except DefinitionNotFoundError as exc:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return _serialize(document)
