"""API tests covering the board asset workflow."""

from __future__ import annotations

import os
import tempfile

temp_db = tempfile.NamedTemporaryFile(prefix="board-assets-db-", suffix=".sqlite3", delete=False)
os.environ["DATABASE_URL"] = f"sqlite:///{temp_db.name}"
temp_db.close()

from fastapi.testclient import TestClient

os.environ.setdefault("BOARD_ASSET_STORAGE_BACKEND", "local")
temp_dir = tempfile.mkdtemp(prefix="board-assets-test-")
os.environ.setdefault("BOARD_ASSET_LOCAL_PATH", temp_dir)
os.environ.setdefault("BOARD_ASSET_UPLOAD_TOKEN", "upload-token")
os.environ.setdefault("BOARD_ASSET_MODERATION_TOKEN", "moderator-token")

from klipperiwc.app import create_app  # noqa: E402  (import after env configuration)

client = TestClient(create_app())


def _upload_asset(name: str, *, visibility: str = "public") -> dict[str, object]:
    files = {
        "file": (f"{name}.svg", f"<svg id='{name}'></svg>".encode("utf-8"), "image/svg+xml"),
    }
    response = client.post(
        "/api/board-assets/",
        files=files,
        data={"title": name, "visibility": visibility},
        headers={"X-Board-Assets-Key": "upload-token"},
    )
    assert response.status_code == 201
    return response.json()


def test_board_asset_listing_requires_auth_for_pending() -> None:
    created = _upload_asset("first")

    response = client.get("/api/board-assets/")
    assert response.status_code == 200
    assert response.json() == []

    response = client.patch(
        f"/api/board-assets/{created['id']}/moderation",
        json={"status": "approved"},
        headers={"X-Board-Assets-Moderator": "moderator-token"},
    )
    assert response.status_code == 200

    response = client.get("/api/board-assets/")
    assert response.status_code == 200
    listed_ids = [entry["id"] for entry in response.json()]
    assert created["id"] in listed_ids

    forbidden = client.get("/api/board-assets/", params={"status_filter": "pending"})
    assert forbidden.status_code == 403

    pending = _upload_asset("second")
    moderator_view = client.get(
        "/api/board-assets/",
        params={"status_filter": "pending"},
        headers={"X-Board-Assets-Moderator": "moderator-token"},
    )
    assert moderator_view.status_code == 200
    pending_ids = [entry["id"] for entry in moderator_view.json()]
    assert pending["id"] in pending_ids

    uploader_view = client.get(
        "/api/board-assets/",
        params={"status_filter": "pending"},
        headers={"X-Board-Assets-Key": "upload-token"},
    )
    assert uploader_view.status_code == 200
    uploader_pending_ids = [entry["id"] for entry in uploader_view.json()]
    assert pending["id"] in uploader_pending_ids
