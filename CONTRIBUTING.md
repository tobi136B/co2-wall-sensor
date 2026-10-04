# Contributing

**English** | [Deutsch](#deutsch)

Thanks for your interest in improving the CO2 Wall Sensor!

## Ways to help

* **Build one and report back.** Photos, measured dimensions of your SCD41 board and display, and temperature offsets are very valuable.
* **Report bugs** with the [bug report template](https://github.com/tobi136B/co2-wall-sensor/issues/new/choose).
* **Suggest features** with the feature request template.
* **Send pull requests** for firmware, CAD, tools or documentation.

## Ground rules

* **Geometry lives in one place.** Never edit STL or STEP files by hand. Change `cad/fusion/generate_enclosure/generate_enclosure.py`, run it in Fusion with `EXPORT = True` and commit the regenerated files.
* **Generated documentation.** After changing parameters or pins, run:
  ```bash
  pip install -r requirements.txt
  python tools/drawing.py && python tools/wiring.py && python tools/display_preview.py
  ```
* **Both languages.** User-facing text exists in English and German. Update both, or mention in the pull request that a translation is missing.
* **Firmware texts** go into the substitutions of `co2-wall-sensor.yaml` and `co2-wall-sensor-de.yaml`, logic into `common/base.yaml`.
* **Code style:** Python is checked with `ruff check tools`. Keep YAML at 2 spaces.
* **No secrets.** `esphome/secrets.yaml` is ignored by git, keep it that way.

## Pull request checklist

* [ ] CI is green (firmware compiles in both languages, tools run)
* [ ] Generated files updated if parameters or pins changed
* [ ] English and German docs updated
* [ ] `CHANGELOG.md` entry added

---

## Deutsch

Danke, dass du den CO2-Wandsensor verbessern möchtest!

* **Nachbauen und berichten:** Fotos, gemessene Maße deiner SCD41-Platine und des Displays sowie Temperatur-Offsets helfen sehr.
* **Fehler melden** und **Ideen vorschlagen** über die Vorlagen unter [Issues](https://github.com/tobi136B/co2-wall-sensor/issues/new/choose).
* **Pull Requests** für Firmware, CAD, Tools oder Doku sind willkommen.

Die Regeln oben gelten genauso: Geometrie nur im Generator ändern, generierte Dateien neu erzeugen, beide Sprachen pflegen, keine Zugangsdaten einchecken. Issues und Pull Requests dürfen gerne auf Deutsch geschrieben werden.
