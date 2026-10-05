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
* **Wire notch sealed with hot glue**, so no warm air is drawn from the ESP bay into the chamber.
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
* **+2 of each** for the optional lock tab that ties the device to the wall plate.

The back cover is held at four points: two bosses in the bottom corners and two inserts in a solid 5 mm band above the display bay. The button heads sit in 1.3 mm counterbores, so the cover surface stays flat and slides cleanly onto the wall plate and desk stand. The cover has no pins or hooks on its inside and prints flat without supports.

## Nothing is glued

* **SCD41:** the breakout has no mounting holes. It slides into two rails with a groove on the front of the sensor carrier, an end stop above and a small snap bump below hold it in place.
* **ESP32-C3:** it has no mounting holes either. Side guides, two end stops and a short groove at its lower edge hold it. The groove sits where the board has no solder pads, so wires can be soldered along both edges.
* **Sensor carrier:** two screws. It is the removable floor of the sensor chamber, so the sensor can be replaced without touching the display.

## Cable exit: a swappable port module

The ESP32-C3 sits with its USB-C socket pointing **down**, with 13 mm of free space below it. The cable leaves through a small L-shaped **cable port module** at the lower back edge:

* **PortBack:** hole for the boot of a right-angle plug. The cable goes straight into the flush wall box or through the desk stand. The plug body is caught behind the module, which works as strain relief.
* **PortBottom:** opening for a straight plug, if the cable runs on the wall surface.

The module is clamped between housing and back cover, a step in the bottom wall and a lip under the cover hold it. Both versions take 2 g of filament, so you print both and decide on site. Changing it later takes four screws. Thin knock-out membranes were tried before (v1.2), but they cannot be closed again once broken out.

## Printing details

* **45° foot on bed edges.** A fillet that starts tangent to the print bed prints badly: the lowest layers are almost horizontal and the first layer squeezes out (elephant foot). The soft front edge therefore ends in a short 45° chamfer that is tangent to the fillet. It looks round, but prints clean.
* **Entry chamfers** on all insert holes centre the insert and give the displaced plastic room.
* **Fillets at the root of the bosses** make them stronger, they do not crack while pressing inserts.
* **Lead-in chamfer** on the rail, so the device finds the slot easily.
* **Engraved labels** on hidden faces: part name, version and print orientation.
* **One fit value** (`FIT`) for every sliding or plugged fit.

## Parameters in Fusion

Every value of the parameter block becomes a Fusion user parameter (*Modify > Change Parameters*), with its explanation as comment. To change the enclosure, edit the values there and run the script again: it reads the parameters of the open design and rebuilds every part with them, including the interference check. The model is generated by a script and is not a hand-built history, so a changed value takes effect when the script runs, not live in the timeline.

The assembly has a slider joint ("RailSlider"): the device can be pushed up the rail by 15 mm, exactly as it is removed from the wall plate.

## Power

The device is permanently powered via USB-C (about 0.5 W, roughly 4 to 5 kWh per year). A battery version was considered and rejected: a colour display needs constant power, and lithium cells inside a closed housing on the wall are an unnecessary risk.

## Parametric CAD and generated documentation

The enclosure is not modelled by hand. [`generate_enclosure.py`](../cad/fusion/generate_enclosure/generate_enclosure.py) builds every part from a single block of parameters, checks wall and desk assembly for interference and can export STL and STEP files. The [technical drawing](../tools/drawing.py), the [wiring diagram](../tools/wiring.py) and the [display preview](../tools/display_preview.py) are generated from the same sources. Changing one dimension keeps model, drawing and documentation consistent.
