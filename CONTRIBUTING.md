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
* **Dimensions are Fusion user parameters.** Change them under *Modify > Change Parameters* or in the `PARAMETERS` block, run the script with `EXPORT = True` and commit STL, STEP and `cad/build_info.json`. The CI fails if the print files do not belong to the current parameters.
* **Generated documentation.** After changing parameters or pins, run:
  ```bash
  pip install -r requirements.txt
  python tools/drawing.py && python tools/wiring.py && python tools/display_preview.py && python tools/build_3mf.py
  python tools/check_repo.py
  ```
* **Both languages.** User-facing text exists in English and German. Update both, or mention in the pull request that a translation is missing.
* **Firmware texts** go into the substitutions of the four device files (`co2-wall-sensor*.yaml`), logic into `common/base.yaml`, network settings into `common/network_secrets.yaml` (own build) or `common/network_factory.yaml` (browser installer).
* **Commit messages follow [Conventional Commits](https://www.conventionalcommits.org):** `feat:`, `fix:`, `docs:`, `cad:` (enclosure), `ci:`, `chore:`. Releases, version numbers and the changelog are created from them automatically (release-please), so do not edit `CHANGELOG.md` by hand.
* **Code style:** Python is checked with `ruff check tools`. Keep YAML at 2 spaces.
* **No secrets.** `esphome/secrets.yaml` is ignored by git, keep it that way.

## Pull request checklist

* [ ] CI is green (four firmware builds, tools, repository and link checks)
* [ ] Generated files updated if parameters or pins changed
* [ ] English and German docs updated
* [ ] Commit messages follow Conventional Commits

---

## Deutsch

Danke, dass du den CO2-Wandsensor verbessern möchtest!

* **Nachbauen und berichten:** Fotos, gemessene Maße deiner SCD41-Platine und des Displays sowie Temperatur-Offsets helfen sehr.
* **Fehler melden** und **Ideen vorschlagen** über die Vorlagen unter [Issues](https://github.com/tobi136B/co2-wall-sensor/issues/new/choose).
* **Pull Requests** für Firmware, CAD, Tools oder Doku sind willkommen.

Die Regeln oben gelten genauso: Geometrie nur über die Parameter ändern, generierte Dateien neu erzeugen, beide Sprachen pflegen, keine Zugangsdaten einchecken, Commit-Nachrichten nach Conventional Commits. Issues und Pull Requests dürfen gerne auf Deutsch geschrieben werden.
