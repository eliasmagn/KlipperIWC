"""Tests for the configuration builder API."""

from __future__ import annotations

from fastapi.testclient import TestClient

from klipperiwc.app import create_app


client = TestClient(create_app())


def test_list_presets() -> None:
    response = client.get("/api/configurator/presets")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any(preset["id"] == "voron_trident" for preset in data)


def test_list_component_groups() -> None:
    response = client.get("/api/configurator/component-groups")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any(category["id"] == "toolhead" for category in data)


def test_generate_configuration_with_defaults() -> None:
    response = client.post(
        "/api/configurator/generate",
        json={"printer_preset_id": "ender3_stock", "components": {}},
    )
    assert response.status_code == 200
    payload = response.json()
    config = payload["configuration"]
    assert "[printer]" in config
    assert "kinematics: cartesian" in config
    assert "[extruder]" in config


def test_generate_configuration_with_overrides_and_macros() -> None:
    response = client.post(
        "/api/configurator/generate",
        json={
            "printer_preset_id": "voron_trident",
            "components": {"probe": "bltouch"},
            "parameter_overrides": {"max_velocity": "250", "z_offset": "-0.05"},
            "custom_macros": ["[gcode_macro BED_MESH]", "G28\nBED_MESH_CALIBRATE"],
        },
    )
    assert response.status_code == 200
    payload = response.json()
    config = payload["configuration"]
    assert "[bltouch]" in config
    assert "[user_overrides]" in config
    assert "max_velocity: 250" in config
    assert "BED_MESH_CALIBRATE" in config


def test_generate_configuration_rejects_unknown_preset() -> None:
    response = client.post(
        "/api/configurator/generate",
        json={"printer_preset_id": "unknown", "components": {}},
    )
    assert response.status_code == 404
