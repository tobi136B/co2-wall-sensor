# Changelog

All notable changes to this project. Format based on [Keep a Changelog](https://keepachangelog.com), versioning follows [SemVer](https://semver.org).

## [1.8.0](https://github.com/tobi136B/co2-wall-sensor/compare/v1.7.2...v1.8.0) (2026-10-07)


### Added

* **firmware:** outdoor values, window hint and settings in Home Assistant ([#21](https://github.com/tobi136B/co2-wall-sensor/issues/21)) ([9c6789e](https://github.com/tobi136B/co2-wall-sensor/commit/9c6789ecc3ec2cc87e6c7034e68d26a26aef3755))

## [1.7.2](https://github.com/tobi136B/co2-wall-sensor/compare/v1.7.1...v1.7.2) (2026-10-07)


### Fixed

* shop links, prices and pictures match the current state ([#18](https://github.com/tobi136B/co2-wall-sensor/issues/18)) ([16f6d1d](https://github.com/tobi136B/co2-wall-sensor/commit/16f6d1dd997285e862691753d4c995153b6d7b4e))

## [1.7.1](https://github.com/tobi136B/co2-wall-sensor/compare/v1.7.0...v1.7.1) (2026-10-07)


### Fixed

* **cad:** measured right-angle plug and inserts of both diameters ([#16](https://github.com/tobi136B/co2-wall-sensor/issues/16)) ([be7c70b](https://github.com/tobi136B/co2-wall-sensor/commit/be7c70b7b6148175292aeee8a550067edc6a8dce))

## [1.7.0](https://github.com/tobi136B/co2-wall-sensor/compare/v1.6.0...v1.7.0) (2026-10-07)


### Added

* measured ESP32-C3 holder, collision-free assembly and new animation ([#14](https://github.com/tobi136B/co2-wall-sensor/issues/14)) ([0e9e9ed](https://github.com/tobi136B/co2-wall-sensor/commit/0e9e9ed84a7108affdd0960e28bb1d37ff0fe281))

## [1.6.0](https://github.com/tobi136B/co2-wall-sensor/compare/v1.5.0...v1.6.0) (2026-10-06)


### Added

* **firmware:** CO2 trend arrow and ventilation forecast ([#11](https://github.com/tobi136B/co2-wall-sensor/issues/11)) ([b7deac4](https://github.com/tobi136B/co2-wall-sensor/commit/b7deac44cd859aff8ef96658c97d00f933d838d5))
* interactive 3D assembly guide and new README animation ([#13](https://github.com/tobi136B/co2-wall-sensor/issues/13)) ([0c56e3d](https://github.com/tobi136B/co2-wall-sensor/commit/0c56e3df885308c8588ff31f40f612a8a9c0e9aa))

## [1.5.0](https://github.com/tobi136B/co2-wall-sensor/compare/v1.4.0...v1.5.0) (2026-10-06)


### Added

* **cad:** printability for 0.4 mm nozzles and diamond vent mesh ([#9](https://github.com/tobi136B/co2-wall-sensor/issues/9)) ([80bae21](https://github.com/tobi136B/co2-wall-sensor/commit/80bae21d80c4b81d086d13308233caf516e13bbc))


### Documentation

* room size and placement of the sensor ([8ed4240](https://github.com/tobi136B/co2-wall-sensor/commit/8ed4240ff7e65f8ec842e42d2965d60d6d796678))

## [1.4.0](https://github.com/tobi136B/co2-wall-sensor/compare/v1.3.0...v1.4.0) (2026-10-05)


### Added

* **cad:** sensor carrier profiles for different SCD41 boards with spring tongue ([4884566](https://github.com/tobi136B/co2-wall-sensor/commit/4884566fa0200700a9ffd2bd03d331de52491c9b)), closes [#7](https://github.com/tobi136B/co2-wall-sensor/issues/7)
* generate shop link tables from hardware/bom.csv ([27f08ae](https://github.com/tobi136B/co2-wall-sensor/commit/27f08ae2e01583154e715adda9edb1a230080099))
* readable bill of materials in hardware/bom.yaml ([4d5691e](https://github.com/tobi136B/co2-wall-sensor/commit/4d5691edf74087e0b451b58f861e5ddc2cf3e3b5))


### Documentation

* add sensor carrier profiles and online configurator to the roadmap ([f5e4023](https://github.com/tobi136B/co2-wall-sensor/commit/f5e4023f99dcf99ea56c6cae3dcb68d4f661ada3))

## [1.3.0] - 2026-10-05

### Added
* **Cable port modules:** a small swappable part at the lower back edge decides the cable exit. `PortBack` for a right-angle plug (the plug body is caught behind the module, strain relief), `PortBottom` for a straight plug. Print both, swap with four screws.
* **SCD41 slides into rails** with end stop and snap bump on the sensor carrier, sized for the common 15 × 20 mm breakout.
* **ESP32-C3 is held by guides, end stops and a short groove**, nothing in the device is glued any more.
* **Optional lock tab** ties the device to the wall plate with two more M2 screws.
* **All dimensions are Fusion user parameters** (*Modify > Change Parameters*); the script takes them over when it runs again.
* Slider joint in the assembly: the device can be pushed up the rail in Fusion.
* Engraved labels with part name, version and print orientation.
* 45° foot on all rounded bed edges, entry chamfers on insert holes, fillets at boss roots, lead-in chamfer on the rail.
* Renders of cable ports, sensor carrier and lock tab.

### Changed
* Device depth 24 mm (was 22) to fit a straight USB-C overmould and to give the SCD41 1.4 mm of air in front of its opening.
* Wall plate is printed front face down (no 78 mm bridge on the wall side any more).
* Sensor carrier is printed standing on its lower edge.
* One fit value `FIT` for all sliding and plugged fits.

### Removed
* Knock-out membranes of v1.2, replaced by the cable port modules.

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

**Deutsch:** Die Änderungshistorie wird auf Englisch geführt. Kurz zusammengefasst: 1.3.0 bringt tauschbare Kabelport-Module (Kabel hinten oder unten), Schienen für den SCD41, eine optionale Sicherungslasche, alle Maße als Fusion-Parameter und viele Details für einen sauberen Druck; im Gerät ist nichts mehr geklebt. 1.2.0 verschraubt alles mit nur einer Schraubensorte (10 Einschmelzmuttern M2 × 3 und 10 Linsenkopfschrauben M2 × 4), bringt den verschraubten Sensorträger und lässt den Kabelaustritt nach dem Druck wählen (unten oder hinten). 1.1.0 brachte die vollständige Zweisprachigkeit, eine aufgeteilte Firmware, CI mit Firmware-Builds, Displayvorschau und Explosionsansicht.
