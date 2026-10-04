# Changelog

All notable changes to this project. Format based on [Keep a Changelog](https://keepachangelog.com), versioning follows [SemVer](https://semver.org).

## [1.2.0] - 2026-10-04

### Added
* **Sensor carrier:** removable, screwed floor of the sensor chamber. Carries the SCD41 on the front and the ESP32-C3 on the back, so the sensor is easy to mount and to replace.
* **Selectable cable exit:** two flush knock-outs (0.6 mm), back cover for a right-angle plug, bottom wall for a straight plug. Decide after printing.
* Renders of the interior and the back view.
* Fastener summary on the technical drawing.

### Changed
* **One fastener type for everything:** 10 heat-set inserts M2 × 3 (OD 3.2) and 10 button head screws M2 × 4, ISO 7380. Display, back cover (4 points) and sensor carrier are all screwed into inserts. M3 inserts, countersunk screws and self-tapping plastic screws are gone.
* Back cover without hooks or pins: four counterbored screws, prints flat without supports.
* ESP32-C3 turned by 180°, USB-C socket now points down with 13 mm of space for the plug.
* Device grows to 69.8 × 69.8 × 22 mm to make room for the insert bosses (wall plate stays 82 × 82 mm).
* Firmware: WiFi transmit power limited to 8.5 dB, a known fix for unstable ESP32-C3 SuperMini boards.
* Drawing, assembly guide, design notes, FAQ and bill of materials updated in English and German.

## [1.1.0] - 2026-10-04

### Added
* English as primary language with full German translation (README, docs, firmware, drawing, wiring diagram).
* Firmware split into `common/base.yaml` plus device files for English and German.
* Display preview generator and rendered previews of all three air quality states.
* Exploded view and coloured renders.
* Design notes, FAQ, machine-readable bill of materials.
* GitHub Actions: firmware compile for both languages, tool checks, release builds with firmware and print files.
* Issue and pull request templates, contributing guide.
* Fusion generator can export STL and STEP directly (`EXPORT = True`).

### Changed
* CAD generator rewritten with English identifiers and component names; file names of STL and STEP are English now.
* Secrets use English keys (`wifi_ssid`, `wifi_password`, `api_encryption_key`, ...).

## [1.0.0] - 2026-10-04

### Added
* First release: compact 66.8 × 66.8 × 20 mm enclosure with dovetail rail.
* Wall plate for German flush wall boxes and desk stand with 12° tilt.
* ESPHome firmware for ESP32-C3 SuperMini, SCD41 and Waveshare 2inch LCD.

---

**Deutsch:** Die Änderungshistorie wird auf Englisch geführt. Kurz zusammengefasst: 1.2.0 verschraubt alles mit nur einer Schraubensorte (10 Einschmelzmuttern M2 × 3 und 10 Linsenkopfschrauben M2 × 4), bringt den verschraubten Sensorträger und lässt den Kabelaustritt nach dem Druck wählen (unten oder hinten). 1.1.0 brachte die vollständige Zweisprachigkeit, eine aufgeteilte Firmware, CI mit Firmware-Builds, Displayvorschau und Explosionsansicht.
