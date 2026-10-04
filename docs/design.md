# Design notes

**English** | [Deutsch](de/design.md)

This page explains why the device looks and works the way it does.

## Goals

1. Show air quality, temperature, humidity and time **on one screen**, readable from across the room.
2. **No visible cable** on the wall, but also usable on a desk.
3. Measurements that are **trustworthy**, not distorted by the device itself.
4. Everything reproducible and adjustable: **parametric CAD, generated documentation**.

## Why a SCD41?

Cheap "CO2" sensors such as the SGP30 or CCS811 only estimate an equivalent CO2 value from volatile organic compounds. The SCD41 measures CO2 directly (photoacoustic NDIR) with ±(50 ppm + 5 % of reading) and also provides temperature and humidity. It needs free air exchange, which drives the whole enclosure layout.

## Thermal concept

Every electronic device heats itself up. An ESP32 with WiFi and an LCD backlight easily lift an internal sensor by several kelvin. Countermeasures:

* **Separate sensor chamber** in the chin of the housing, closed towards the display bay by a divider and towards the ESP bay by a floor.
* **Air enters from below** through 13 slots in the bottom and 3 slots on each side. Warm air from the electronics rises upwards behind the display, away from the sensor.
* **ESP32-C3 instead of a classic ESP32:** single core, no USB-UART chip, no charger. Less waste heat.
* **Cable notch sealed with hot glue**, so no warm air is drawn from the ESP bay into the chamber.
* **Night mode** dims the backlight, which also reduces heat.
* The remaining offset is compensated by `temperature_offset` in the firmware (default 2.0 °C, verify against a reference).

## Closed front

The front has no openings. Dust settles mostly on openings that face up or forward, and an unbroken front simply looks calmer. All vents face down or sideways.

## Mounting: dovetail rail

A short dovetail rail on the back cover fits two adapters:

* **Wall plate 82 × 82 mm.** German flush wall boxes have a 68 mm hole and a rim of about 75 mm, so the compact device alone could not cover them. The plate covers the box, is screwed to the standard box screws (60 mm) and has corners concentric to the device, which creates an even frame like a light switch.
* **Desk stand.** Same rail, device leans back by 12° for better readability, with a 5 mm air gap below so the vents stay free.

The insertion window above the slot is hidden behind the device. You insert the device from the front and slide it 15 mm down. Nothing is visible from outside and the device can be removed without tools.

## Power

The device is permanently powered via USB-C (about 0.5 W, roughly 4 to 5 kWh per year). A battery version was considered and rejected: a colour display needs constant power, and lithium cells inside a closed housing on the wall are an unnecessary risk.

## Parametric CAD and generated documentation

The enclosure is not modelled by hand. [`generate_enclosure.py`](../cad/fusion/generate_enclosure/generate_enclosure.py) builds every part from a single block of parameters, checks wall and desk assembly for interference and can export STL and STEP files. The [technical drawing](../tools/drawing.py), the [wiring diagram](../tools/wiring.py) and the [display preview](../tools/display_preview.py) are generated from the same sources. Changing one dimension keeps model, drawing and documentation consistent.
