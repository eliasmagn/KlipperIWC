"""Database configuration for KlipperIWC."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase

__all__ = [
    "DATABASE_URL",
    "engine",
    "Base",
]

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DEFAULT_SQLITE_PATH = DATA_DIR / "klipperiwc.sqlite3"

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_SQLITE_PATH}")


class Base(DeclarativeBase):
    """Base class for ORM models."""


_engine_args: Dict[str, Any] = {"future": True, "pool_pre_ping": True}
if DATABASE_URL.startswith("sqlite"):  # pragma: no branch - configuration guard
    _engine_args.setdefault("connect_args", {"check_same_thread": False})

engine = create_engine(DATABASE_URL, **_engine_args)
