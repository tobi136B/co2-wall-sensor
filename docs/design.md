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

* **Separate sensor chamber** in the chin of the housing, closed towards the display bay by a divider and towards the ESP bay by the screwed sensor carrier. The carrier is a separate part, so the SCD41 is easy to mount and to replace.
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

## Fastening: one screw type, all metal threads

Plastic threads wear out after a few cycles and self-tapping screws crack thin bosses. Every screw connection therefore uses a brass heat-set insert, and all of them use the same parts:

* **10 × heat-set insert M2 × 3** (outer diameter 3.2 mm, hole Ø 3.0 × 3.4 mm): 4 for the display, 4 for the back cover, 2 for the sensor carrier.
* **10 × button head screw M2 × 4, ISO 7380.** One hex key for the whole device.

The back cover is held at four points: two bosses in the bottom corners and two inserts in a solid 5 mm band above the display bay. The button heads sit in 1.3 mm counterbores, so the cover surface stays flat and slides cleanly onto the wall plate and desk stand. The cover has no pins or hooks on its inside and prints flat without supports.

## Cable exit: decide after printing

The ESP32-C3 sits with its USB-C socket pointing **down**, with 13 mm of free space below it. Two knock-outs of 0.6 mm are prepared and flush with the outer surface, so they are invisible:

* **Back cover:** for a right-angle plug. The cable goes straight into the flush wall box or through the desk stand.
* **Bottom wall:** for a straight plug, if the cable runs on the wall surface.

You print one housing and decide on site which membrane to break out. The other one stays closed.

## Power

The device is permanently powered via USB-C (about 0.5 W, roughly 4 to 5 kWh per year). A battery version was considered and rejected: a colour display needs constant power, and lithium cells inside a closed housing on the wall are an unnecessary risk.

## Parametric CAD and generated documentation

The enclosure is not modelled by hand. [`generate_enclosure.py`](../cad/fusion/generate_enclosure/generate_enclosure.py) builds every part from a single block of parameters, checks wall and desk assembly for interference and can export STL and STEP files. The [technical drawing](../tools/drawing.py), the [wiring diagram](../tools/wiring.py) and the [display preview](../tools/display_preview.py) are generated from the same sources. Changing one dimension keeps model, drawing and documentation consistent.
