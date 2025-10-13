"""API routers for KlipperIWC."""

from .board_assets import router as board_assets_router
from .dashboard import router as dashboard_router
from .status import router as status_router

__all__ = ["status_router", "board_assets_router", "dashboard_router"]
