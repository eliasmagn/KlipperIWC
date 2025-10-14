"""API tests for the definition document registry."""

from __future__ import annotations

import os
import tempfile

from fastapi.testclient import TestClient

# Ensure an isolated SQLite database for the test module
_temp_db = tempfile.NamedTemporaryFile(prefix="definitions-", suffix=".sqlite3", delete=False)
os.environ["DATABASE_URL"] = f"sqlite:///{_temp_db.name}"
_temp_db.close()

from klipperiwc.app import create_app  # noqa: E402  (import after env configuration)

client = TestClient(create_app())


def test_board_definition_crud_roundtrip() -> None:
    payload = {
        "slug": "voron-24",
        "name": "Voron 2.4 Board",
        "description": "Community board layout",
        "preview_image_url": "https://example.com/boards/voron-24.png",
        "data": {"schema_version": "1.0.0", "connectors": []},
    }

    response = client.post("/api/definitions/boards", json=payload)
    assert response.status_code == 201
    created = response.json()
    assert created["slug"] == payload["slug"]
    assert created["preview_image_url"] == payload["preview_image_url"]

    listing = client.get("/api/definitions/boards")
    assert listing.status_code == 200
    assert any(entry["slug"] == payload["slug"] for entry in listing.json())

    detail = client.get(f"/api/definitions/boards/{payload['slug']}")
    assert detail.status_code == 200
    assert detail.json()["name"] == payload["name"]

    update = client.put(
        f"/api/definitions/boards/{payload['slug']}",
        json={"name": "Voron 2.4 Rev B", "data": {"schema_version": "1.0.0", "connectors": ["X"]}},
    )
    assert update.status_code == 200
    updated = update.json()
    assert updated["name"] == "Voron 2.4 Rev B"
    assert updated["data"]["connectors"] == ["X"]

    conflict = client.post("/api/definitions/boards", json=payload)
    assert conflict.status_code == 409


def test_printer_definition_crud_roundtrip() -> None:
    payload = {
        "slug": "trident-300",
        "name": "Voron Trident 300",
        "description": "CoreXY printer setup",
        "data": {"kinematics": "corexy", "build_volume": [300, 300, 250]},
    }

    response = client.post("/api/definitions/printers", json=payload)
    assert response.status_code == 201
    created = response.json()
    assert created["slug"] == payload["slug"]

    listing = client.get("/api/definitions/printers")
    assert listing.status_code == 200
    assert [entry["slug"] for entry in listing.json()] == [payload["slug"]]

    detail = client.get(f"/api/definitions/printers/{payload['slug']}")
    assert detail.status_code == 200
    assert detail.json()["description"] == payload["description"]

    updated = client.put(
        f"/api/definitions/printers/{payload['slug']}",
        json={"description": "CoreXY printer setup with CAN"},
    )
    assert updated.status_code == 200
    assert updated.json()["description"] == "CoreXY printer setup with CAN"

    missing = client.get("/api/definitions/printers/unknown")
    assert missing.status_code == 404
