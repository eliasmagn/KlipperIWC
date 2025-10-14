"""Repository package for database persistence helpers."""

from .definitions import (
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
from .status_history import (
    create_status_history,
    delete_older_than,
    delete_status_history,
    get_status_history,
    list_status_history,
    update_status_history,
)

__all__ = [
    "DefinitionConflictError",
    "DefinitionNotFoundError",
    "create_board_definition",
    "create_printer_definition",
    "get_board_definition",
    "get_printer_definition",
    "list_board_definitions",
    "list_printer_definitions",
    "update_board_definition",
    "update_printer_definition",
    "create_status_history",
    "delete_older_than",
    "delete_status_history",
    "get_status_history",
    "list_status_history",
    "update_status_history",
]
