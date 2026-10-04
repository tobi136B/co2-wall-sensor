# Changelog

All notable changes to this project. Format based on [Keep a Changelog](https://keepachangelog.com), versioning follows [SemVer](https://semver.org).

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

**Deutsch:** Die Änderungshistorie wird auf Englisch geführt. Kurz zusammengefasst bringt 1.1.0 die vollständige Zweisprachigkeit, eine aufgeteilte Firmware, CI mit Firmware-Builds, Displayvorschau und Explosionsansicht.
