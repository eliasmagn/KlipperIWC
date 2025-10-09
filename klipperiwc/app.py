"""Application entrypoint for KlipperIWC."""

from __future__ import annotations

import os
from functools import lru_cache

from fastapi import FastAPI


@lru_cache(maxsize=1)
def create_app() -> FastAPI:
    """Create and configure the FastAPI application instance."""
    app = FastAPI(title="KlipperIWC", description="Klipper Integration Web Console")

    @app.get("/")
    async def healthcheck() -> dict[str, str]:
        """Return a basic healthcheck payload."""
        return {"status": "ok"}

    return app


def main() -> None:
    """Launch the ASGI server using uvicorn."""
    import uvicorn

    app_env = os.getenv("APP_ENV", "development")
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = app_env != "production"

    uvicorn.run(
        "klipperiwc.app:create_app",
        host=host,
        port=port,
        reload=reload,
        factory=True,
        log_level=os.getenv("LOG_LEVEL", "info"),
    )


if __name__ == "__main__":
    main()
