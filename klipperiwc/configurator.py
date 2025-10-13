"""Domain logic for generating Klipper configuration files."""

from __future__ import annotations

from textwrap import dedent
from typing import Tuple

from klipperiwc.models.configurator import (
    ComponentCategory,
    ComponentOption,
    PrinterPreset,
)

PRESETS: list[PrinterPreset] = [
    PrinterPreset(
        id="voron_trident",
        name="Voron Trident",
        description="CoreXY printer with triple Z automatic leveling.",
        base_template=dedent(
            """
            [printer]
            kinematics: corexy
            max_velocity: 300
            max_accel: 6000
            max_z_velocity: 15
            max_z_accel: 150

            [mcu]
            serial: /dev/serial/by-id/usb-Klipper_uC_voron-if00

            [stepper_x]
            step_pin: PB13
            dir_pin: PB12
            enable_pin: !PB14
            rotation_distance: 40
            microsteps: 32
            endstop_pin: tmc5160_stepper_x:virtual_endstop
            position_min: 0
            position_endstop: 300
            position_max: 300
            homing_speed: 100
            homing_retract_dist: 0

            [stepper_y]
            step_pin: PB10
            dir_pin: PB2
            enable_pin: !PB11
            rotation_distance: 40
            microsteps: 32
            endstop_pin: tmc5160_stepper_y:virtual_endstop
            position_min: 0
            position_endstop: 300
            position_max: 300
            homing_speed: 100
            homing_retract_dist: 0

            [stepper_z]
            step_pin: PC6
            dir_pin: !PC7
            enable_pin: !PC8
            rotation_distance: 8
            microsteps: 32
            endstop_pin: probe:z_virtual_endstop
            position_max: 250
            homing_speed: 12

            [quad_gantry_level]
            gantry_corners:
                -60,-10
                360,370
            points:
                40,40
                40,260
                260,260
                260,40
            speed: 150
            horizontal_move_z: 10
            retries: 3
            retry_tolerance: 0.01
            max_adjust: 10
            """
        ),
        default_components={
            "toolhead": "stealthburner_ebrushless",
            "controller": "octopus_pro",
            "probe": "euclid",
            "bed_surface": "wham_bam_flex",
        },
    ),
    PrinterPreset(
        id="ender3_stock",
        name="Creality Ender-3 (Stock)",
        description="Affordable cartesian printer with stock components.",
        base_template=dedent(
            """
            [printer]
            kinematics: cartesian
            max_velocity: 150
            max_accel: 2000
            max_z_velocity: 10
            max_z_accel: 100

            [mcu]
            serial: /dev/serial/by-id/usb-Klipper_Ender_3-if00

            [stepper_x]
            step_pin: PB9
            dir_pin: !PB8
            enable_pin: !PA15
            rotation_distance: 40
            microsteps: 16
            endstop_pin: ^PA5
            position_endstop: 0
            position_max: 235

            [stepper_y]
            step_pin: PB7
            dir_pin: PB6
            enable_pin: !PB5
            rotation_distance: 40
            microsteps: 16
            endstop_pin: ^PA6
            position_endstop: 0
            position_max: 235

            [stepper_z]
            step_pin: PB3
            dir_pin: !PB4
            enable_pin: !PB10
            rotation_distance: 8
            microsteps: 16
            endstop_pin: ^PA7
            position_endstop: 0
            position_max: 250
            """
        ),
        default_components={
            "toolhead": "stock_hotend",
            "controller": "creality_v4_2_2",
            "probe": "none",
            "bed_surface": "glass",
        },
    ),
]

COMPONENT_CATEGORIES: list[ComponentCategory] = [
    ComponentCategory(
        id="toolhead",
        label="Toolhead",
        description="Select the extruder and hotend assembly for your printer.",
        options=[
            ComponentOption(
                id="stealthburner_ebrushless",
                label="Voron Stealthburner (Ebb Brushless)",
                description="High-flow hotend with CW2 extruder and brushless fan control.",
                config_snippet=dedent(
                    """
                    [extruder]
                    step_pin: PD2
                    dir_pin: PD4
                    enable_pin: !PD3
                    rotation_distance: 22.678
                    gear_ratio: 50:10
                    microsteps: 32
                    nozzle_diameter: 0.4
                    filament_diameter: 1.75
                    heater_pin: PD5
                    sensor_type: PT1000
                    sensor_pin: PA3
                    min_temp: 0
                    max_temp: 300

                    [fan]
                    pin: PD6
                    """
                ),
            ),
            ComponentOption(
                id="stock_hotend",
                label="Stock Hotend",
                description="Standard MK8-style hotend with PTFE-lined heatbreak.",
                config_snippet=dedent(
                    """
                    [extruder]
                    step_pin: PB1
                    dir_pin: !PB0
                    enable_pin: !PC3
                    rotation_distance: 34.406
                    microsteps: 16
                    nozzle_diameter: 0.4
                    filament_diameter: 1.75
                    heater_pin: PA1
                    sensor_type: EPCOS 100K B57560G104F
                    sensor_pin: PA0
                    min_temp: 0
                    max_temp: 260

                    [fan]
                    pin: PB15
                    """
                ),
            ),
        ],
    ),
    ComponentCategory(
        id="controller",
        label="Controller Board",
        description="Pick the primary control board that drives the printer.",
        options=[
            ComponentOption(
                id="octopus_pro",
                label="BigTreeTech Octopus Pro",
                description="32-bit STM32F446 board with support for TMC5160 drivers.",
                config_snippet=dedent(
                    """
                    [board_pins octopus_pro]
                    aliases:
                        X_STEP=PB13, X_DIR=PB12, X_ENABLE=PB14
                        Y_STEP=PB10, Y_DIR=PB2, Y_ENABLE=PB11
                        Z_STEP=PC6, Z_DIR=PC7, Z_ENABLE=PC8
                        E_STEP=PD2, E_DIR=PD4, E_ENABLE=PD3
                        HE0=PD5, FAN0=PD6
                    """
                ),
            ),
            ComponentOption(
                id="creality_v4_2_2",
                label="Creality 4.2.2",
                description="Stock Ender-3 8-bit style board updated with 32-bit MCU.",
                config_snippet=dedent(
                    """
                    [board_pins creality_v4_2_2]
                    aliases:
                        X_STEP=PB9, X_DIR=PB8, X_ENABLE=PA15
                        Y_STEP=PB7, Y_DIR=PB6, Y_ENABLE=PB5
                        Z_STEP=PB3, Z_DIR=PB4, Z_ENABLE=PB10
                        E_STEP=PB1, E_DIR=PB0, E_ENABLE=PC3
                        HE0=PA1, FAN0=PB15
                    """
                ),
            ),
        ],
    ),
    ComponentCategory(
        id="probe",
        label="Z Probe",
        description="Choose an automatic Z probe if your printer uses one.",
        options=[
            ComponentOption(
                id="euclid",
                label="Euclid Probe",
                description="Magnetic detachable probe with precise repeatability.",
                config_snippet=dedent(
                    """
                    [probe]
                    pin: ^PC13
                    x_offset: 0
                    y_offset: 25
                    z_offset: 7.5
                    speed: 10
                    samples: 3
                    sample_retract_dist: 5.0
                    lift_speed: 15
                    """
                ),
            ),
            ComponentOption(
                id="bltouch",
                label="Antclabs BLTouch",
                description="Widely used touch probe for automated bed leveling.",
                config_snippet=dedent(
                    """
                    [bltouch]
                    sensor_pin: ^PB1
                    control_pin: PB0
                    x_offset: -43
                    y_offset: -6
                    z_offset: 2.0
                    speed: 5
                    """
                ),
            ),
            ComponentOption(
                id="none",
                label="No Probe",
                description="Manual bed leveling using endstops only.",
                config_snippet="",
            ),
        ],
    ),
    ComponentCategory(
        id="bed_surface",
        label="Build Surface",
        description="Select the build surface to hint recommended temperatures.",
        options=[
            ComponentOption(
                id="wham_bam_flex",
                label="Wham Bam Flex Plate",
                description="PEI-coated flex plate with magnetic base.",
                config_snippet=dedent(
                    """
                    [heater_bed]
                    heater_pin: PB0
                    sensor_type: Generic 3950
                    sensor_pin: PB1
                    min_temp: 0
                    max_temp: 120
                    control: pid
                    pid_Kp: 45.4
                    pid_Ki: 1.23
                    pid_Kd: 312.5
                    """
                ),
            ),
            ComponentOption(
                id="glass",
                label="Glass Bed",
                description="Simple glass plate on aluminum heated bed.",
                config_snippet=dedent(
                    """
                    [heater_bed]
                    heater_pin: PB0
                    sensor_type: EPCOS 100K B57560G104F
                    sensor_pin: PB1
                    min_temp: 0
                    max_temp: 110
                    bang_bang: true
                    hysteresis: 2.0
                    """
                ),
            ),
        ],
    ),
]


_COMPONENT_LOOKUP: dict[str, ComponentOption] = {
    option.id: option
    for category in COMPONENT_CATEGORIES
    for option in category.options
}

_PRESET_LOOKUP: dict[str, PrinterPreset] = {preset.id: preset for preset in PRESETS}


def get_preset(preset_id: str) -> PrinterPreset | None:
    """Return a preset by identifier."""

    return _PRESET_LOOKUP.get(preset_id)


def get_category(category_id: str) -> ComponentCategory | None:
    """Return a component category by identifier."""

    return next((category for category in COMPONENT_CATEGORIES if category.id == category_id), None)


def build_configuration(
    *,
    preset: PrinterPreset,
    components: dict[str, str],
    custom_macros: list[str] | None,
    overrides: dict[str, str] | None,
) -> Tuple[str, list[str]]:
    """Combine preset and component snippets into a single configuration."""

    snippets: list[str] = [preset.base_template.strip()]
    warnings: list[str] = []

    for category in COMPONENT_CATEGORIES:
        option_id = components.get(category.id) or preset.default_components.get(category.id)
        if not option_id:
            warnings.append(f"No option selected for category '{category.label}'.")
            continue
        option = _COMPONENT_LOOKUP.get(option_id)
        if option is None:
            warnings.append(f"Unknown option '{option_id}' for category '{category.label}'.")
            continue
        snippet = option.config_snippet.strip()
        if snippet:
            snippets.append(snippet)

    if overrides:
        override_lines = ["[user_overrides]"]
        for key, value in overrides.items():
            override_lines.append(f"{key}: {value}")
        snippets.append("\n".join(override_lines))

    if custom_macros:
        macros_block = ["# Custom macros"]
        macros_block.extend(macro.strip() for macro in custom_macros if macro.strip())
        if len(macros_block) > 1:
            snippets.append("\n".join(macros_block))

    final_config = "\n\n".join(snippets) + "\n"

    return final_config, warnings
