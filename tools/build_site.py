#!/usr/bin/env python3
"""
Project page for GitHub Pages: browser installer (ESP Web Tools), update manifests for the
ESPHome update entity, downloads and the bill of materials, in English and German.

Usage:   python tools/build_site.py --version 1.3.0 --dist dist --out _site
         (dist contains the firmware binaries built by the CI; without them only the page is built)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path
from urllib.parse import quote

import assembly_model
import bom

ROOT = Path(__file__).resolve().parents[1]
REPO = "https://github.com/tobi136B/co2-wall-sensor"
BLUEPRINT_RAW = f"{REPO}/blob/main/homeassistant/blueprints/co2_ventilation_reminder.yaml"
BLUEPRINT = "https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=" + quote(BLUEPRINT_RAW, safe="")
IMAGES = [
    "hero_wall.png",
    "desk_stand.png",
    "exploded_view.png",
    "interior.png",
    "cable_port_back.png",
    "cable_port_bottom.png",
    "sensor_carrier_front.png",
    "display_preview_en.png",
    "display_preview_de.png",
    "social_preview.png",
]

TEXT = {
    "en": {
        "title": "CO2 Wall Sensor",
        "tagline": "A compact CO2, temperature and humidity monitor for Home Assistant. "
        "It covers a flush wall box or stands on your desk.",
        "t_language": "Language",
        "t_install_cta": "Install the firmware",
        "t_print_cta": "Print the enclosure",
        "t_version": "Version",
        "t_hero_alt": "The CO2 Wall Sensor on its wall plate",
        "t_scale_label": "Air quality levels shown on the display",
        "t_good": "Good",
        "t_good_text": "Below 1000 ppm. Fresh air, nothing to do.",
        "t_moderate": "Moderate",
        "t_moderate_text": "1000 to 1400 ppm. Concentration starts to drop.",
        "t_ventilate": "Ventilate!",
        "t_ventilate_text": "Above 1400 ppm. Open a window now.",
        "t_install_title": "Install from your browser",
        "t_install_intro": "Connect the ESP32-C3 SuperMini with a USB-C cable and click the button. "
        "Works in Chrome and Edge on desktop computers. No ESPHome installation needed.",
        "t_install_button": "Install CO2 Wall Sensor",
        "t_unsupported": "Your browser cannot talk to USB devices. Open this page in Chrome or Edge on a computer.",
        "t_not_allowed": "The installer needs a secure connection (https).",
        "t_other_language": 'Prefer German names on the display and in Home Assistant? Use the <a href="{base}de/index.html#install">German page</a>.',
        "t_s1": "Install",
        "t_s1_text": "The firmware is flashed in about a minute. It contains no passwords.",
        "t_s2": "Connect to WiFi",
        "t_s2_text": "Choose your network in the same window. Without a computer: join the hotspot "
        "&quot;CO2 Wall Sensor&quot; with your phone.",
        "t_s3": "Add to Home Assistant",
        "t_s3_text": "Home Assistant finds the sensor by itself. Confirm it under Settings, Devices.",
        "t_s4": "Stay up to date",
        "t_s4_text": "New releases appear as a firmware update in Home Assistant. One click installs them.",
        "t_display_title": "Everything on one screen",
        "t_display_text": "Air quality, CO2 with a three hour trend, temperature, humidity and the time. "
        "The display dims at night and can be switched off from Home Assistant.",
        "t_display_alt": "The display in the three air quality levels",
        "t_print_title": "Print the enclosure",
        "t_print_text": "The plates contain every part in its print orientation. Open them in PrusaSlicer, OrcaSlicer, "
        "Bambu Studio or Cura and print in PETG. Everything is screwed with one screw type into "
        "heat-set inserts, nothing is glued.",
        "t_dl_device": "Device plate (3MF)",
        "t_dl_mounts": "Wall plate and desk stand (3MF)",
        "t_dl_all": "All files of the release",
        "t_guide": "3D assembly guide",
        "t_guide_text": "Every step in 3D: turn the device, take it apart and see which part comes next.",
        "t_cap_exploded": "Housing, sensor carrier, cable port and back cover",
        "t_cap_back": "Cable to the back, into the wall box",
        "t_cap_bottom": "Cable to the bottom, on the wall surface",
        "t_cap_interior": "Inside: display, ESP32-C3 and cable port",
        "t_cap_carrier": "The SCD41 slides into rails",
        "t_cap_desk": "On the desk stand",
        "t_parts_title": "What you need",
        "t_parts_text": "About 45 euros of parts. Pick the shop you like, the links are suggestions.",
        "t_qty": "Qty",
        "t_part": "Part",
        "t_prices": "Prices as checked in October 2026, they change often. Two sensor carriers fit the 13.5 × 21.75 mm and the 15 × 20 mm SCD41 board.",
        "t_docs_title": "Documentation",
        "t_docs_text": "Step by step assembly, wiring, the reasons behind the design and answers to common questions.",
        "t_doc_assembly": "Printing and assembly",
        "t_doc_wiring": "Wiring",
        "t_doc_design": "Design notes",
        "t_doc_faq": "FAQ",
        "t_doc_drawing": "Technical drawing (PDF)",
        "t_doc_blueprint": "Home Assistant blueprint: ventilation reminder",
        "t_footer": "Open source: software MIT, hardware CERN-OHL-P-2.0. Made by Tobias Schneider. "
        f'<a href="{REPO}">Source on GitHub</a>.',
        "doc_assembly": f"{REPO}/blob/main/docs/assembly.md",
        "doc_wiring": f"{REPO}/blob/main/docs/wiring.md",
        "doc_design": f"{REPO}/blob/main/docs/design.md",
        "doc_faq": f"{REPO}/blob/main/docs/faq.md",
    },
    "de": {
        "title": "CO2-Wandsensor",
        "tagline": "Kompakter CO2-, Temperatur- und Feuchtesensor für Home Assistant. "
        "Er verdeckt eine Hohlwanddose oder steht auf dem Schreibtisch.",
        "t_language": "Sprache",
        "t_install_cta": "Firmware installieren",
        "t_print_cta": "Gehäuse drucken",
        "t_version": "Version",
        "t_hero_alt": "Der CO2-Wandsensor auf seiner Wandplatte",
        "t_scale_label": "Luftqualitätsstufen auf dem Display",
        "t_good": "Gut",
        "t_good_text": "Unter 1000 ppm. Frische Luft, nichts zu tun.",
        "t_moderate": "Mäßig",
        "t_moderate_text": "1000 bis 1400 ppm. Die Konzentration lässt nach.",
        "t_ventilate": "Lüften!",
        "t_ventilate_text": "Über 1400 ppm. Jetzt das Fenster öffnen.",
        "t_install_title": "Im Browser installieren",
        "t_install_intro": "Den ESP32-C3 SuperMini per USB-C anschließen und auf den Knopf klicken. "
        "Funktioniert in Chrome und Edge am Computer. Kein ESPHome nötig.",
        "t_install_button": "CO2-Wandsensor installieren",
        "t_unsupported": "Dein Browser kann nicht mit USB-Geräten sprechen. Öffne die Seite in Chrome oder Edge am Computer.",
        "t_not_allowed": "Der Installer braucht eine sichere Verbindung (https).",
        "t_other_language": 'Lieber englische Namen auf dem Display und in Home Assistant? Dann die <a href="{base}index.html#install">englische Seite</a> verwenden.',
        "t_s1": "Installieren",
        "t_s1_text": "Die Firmware ist in etwa einer Minute geflasht. Sie enthält keine Passwörter.",
        "t_s2": "WLAN verbinden",
        "t_s2_text": "Im selben Fenster das Netzwerk wählen. Ohne Computer: mit dem Handy den Hotspot "
        "&quot;CO2 Wandsensor&quot; öffnen.",
        "t_s3": "In Home Assistant aufnehmen",
        "t_s3_text": "Home Assistant findet den Sensor von selbst. Unter Einstellungen, Geräte bestätigen.",
        "t_s4": "Aktuell bleiben",
        "t_s4_text": "Neue Versionen erscheinen in Home Assistant als Firmware-Update. Ein Klick installiert sie.",
        "t_display_title": "Alles auf einem Bildschirm",
        "t_display_text": "Luftqualität, CO2 mit Drei-Stunden-Verlauf, Temperatur, Luftfeuchte und Uhrzeit. "
        "Nachts wird das Display gedimmt, aus Home Assistant lässt es sich ganz ausschalten.",
        "t_display_alt": "Das Display in den drei Luftqualitätsstufen",
        "t_print_title": "Gehäuse drucken",
        "t_print_text": "Die Druckplatten enthalten alle Teile in ihrer Drucklage. In PrusaSlicer, OrcaSlicer, "
        "Bambu Studio oder Cura öffnen und in PETG drucken. Alles wird mit einer Schraubensorte in "
        "Einschmelzmuttern verschraubt, nichts ist geklebt.",
        "t_dl_device": "Druckplatte Gerät (3MF)",
        "t_dl_mounts": "Wandplatte und Tischständer (3MF)",
        "t_dl_all": "Alle Dateien des Releases",
        "t_guide": "3D-Aufbauanleitung",
        "t_guide_text": "Jeder Schritt in 3D: Gerät drehen, zerlegen und sehen, welches Teil als Nächstes kommt.",
        "t_cap_exploded": "Gehäuse, Sensorträger, Kabelport und Rückdeckel",
        "t_cap_back": "Kabel nach hinten, in die Hohlwanddose",
        "t_cap_bottom": "Kabel nach unten, auf Putz",
        "t_cap_interior": "Innen: Display, ESP32-C3 und Kabelport",
        "t_cap_carrier": "Der SCD41 gleitet in Schienen",
        "t_cap_desk": "Auf dem Tischständer",
        "t_parts_title": "Das brauchst du",
        "t_parts_text": "Teile für rund 45 Euro. Such dir den Shop aus, die Links sind Vorschläge.",
        "t_qty": "Anz.",
        "t_part": "Teil",
        "t_prices": "Preise Stand Oktober 2026, sie ändern sich oft. Zwei Sensorträger passen für die 13,5 × 21,75 mm und die 15 × 20 mm SCD41-Platine.",
        "t_docs_title": "Dokumentation",
        "t_docs_text": "Aufbau Schritt für Schritt, Verdrahtung, die Gründe hinter dem Design und Antworten auf häufige Fragen.",
        "t_doc_assembly": "Druck und Aufbau",
        "t_doc_wiring": "Verdrahtung",
        "t_doc_design": "Designnotizen",
        "t_doc_faq": "FAQ",
        "t_doc_drawing": "Technische Zeichnung (PDF)",
        "t_doc_blueprint": "Home-Assistant-Blueprint: Lüftungserinnerung",
        "t_footer": "Open Source: Software MIT, Hardware CERN-OHL-P-2.0. Gebaut von Tobias Schneider. "
        f'<a href="{REPO}">Quellcode auf GitHub</a>.',
        "doc_assembly": f"{REPO}/blob/main/docs/de/aufbau.md",
        "doc_wiring": f"{REPO}/blob/main/docs/de/verdrahtung.md",
        "doc_design": f"{REPO}/blob/main/docs/de/design.md",
        "doc_faq": f"{REPO}/blob/main/docs/de/faq.md",
    },
}


ASSEMBLY = {
    "en": {
        "a_title": "Assembly guide · CO2 Wall Sensor",
        "a_description": "Interactive 3D assembly guide of the CO2 Wall Sensor: every step, every screw, every wire.",
        "a_back": "Project page",
        "a_hint": "Drag to turn, scroll to zoom, point at a part to see its name",
        "a_loading": "Loading the 3D model …",
        "a_noscript": "The 3D guide needs JavaScript. The written guide is in docs/assembly.md.",
        "a_new_parts": "New in this step",
        "a_prev": "Previous step",
        "a_next": "Next",
        "a_play": "Play all steps",
        "a_explode": "Take apart",
        "a_xray": "See through the housing",
        "a_view": "Reset view",
    },
    "de": {
        "a_title": "Aufbauanleitung · CO2-Wandsensor",
        "a_description": "Interaktive 3D-Aufbauanleitung des CO2-Wandsensors: jeder Schritt, jede Schraube, jede Litze.",
        "a_back": "Projektseite",
        "a_hint": "Ziehen zum Drehen, Scrollen zum Zoomen, auf ein Teil zeigen für seinen Namen",
        "a_loading": "3D-Modell wird geladen …",
        "a_noscript": "Die 3D-Anleitung braucht JavaScript. Die schriftliche Anleitung steht in docs/de/aufbau.md.",
        "a_new_parts": "Neu in diesem Schritt",
        "a_prev": "Vorheriger Schritt",
        "a_next": "Weiter",
        "a_play": "Alle Schritte abspielen",
        "a_explode": "Zerlegen",
        "a_xray": "Gehäuse durchsichtig",
        "a_view": "Ansicht zurücksetzen",
    },
}


def fill(template: str, values: dict) -> str:
    text = (ROOT / "site" / template).read_text(encoding="utf-8")
    for key, value in values.items():
        text = text.replace("{{" + key + "}}", str(value))
    if "{{" in text:
        raise SystemExit(f"unfilled placeholder in site/{template}")
    return text


def assembly_page(lang: str, base: str) -> str:
    return fill(
        "assembly.html",
        {
            **ASSEMBLY[lang],
            "lang": lang,
            "base": base,
            "home": "index.html" if lang == "en" else "de/index.html",
            "t_language": TEXT[lang]["t_language"],
            "cur_en": 'aria-current="page"' if lang == "en" else "",
            "cur_de": 'aria-current="page"' if lang == "de" else "",
        },
    )


def manifests(version: str, dist: Path, out: Path) -> None:
    fw = out / "firmware"
    fw.mkdir(parents=True, exist_ok=True)
    for lang in ("en", "de"):
        factory = dist / f"co2-wall-sensor-{lang}-installer.factory.bin"
        ota = dist / f"co2-wall-sensor-{lang}-installer.ota.bin"
        if not factory.exists():
            print(f"note: {factory.name} not found, manifest-{lang}.json skipped")
            continue
        shutil.copy2(factory, fw / factory.name)
        build = {"chipFamily": "ESP32-C3", "parts": [{"path": factory.name, "offset": 0}]}
        if ota.exists():
            shutil.copy2(ota, fw / ota.name)
            build["ota"] = {
                "path": ota.name,
                "md5": hashlib.md5(ota.read_bytes()).hexdigest(),  # noqa: S324 (checksum, not security)
                "summary": f"CO2 Wall Sensor {version}",
                "release_url": f"{REPO}/releases/tag/v{version}",
            }
        manifest = {
            "name": TEXT[lang]["title"],
            "version": version,
            "home_assistant_domain": "esphome",
            "new_install_prompt_erase": True,
            "builds": [build],
        }
        (fw / f"manifest-{lang}.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def page(lang: str, version: str, base: str) -> str:
    t = dict(TEXT[lang])
    values = {
        **t,
        "lang": lang,
        "base": base,
        "version": version,
        "bom_rows": bom.html_rows(lang),
        "blueprint": BLUEPRINT,
        "cur_en": 'aria-current="page"' if lang == "en" else "",
        "cur_de": 'aria-current="page"' if lang == "de" else "",
    }
    values["t_other_language"] = t["t_other_language"].replace("{base}", base)
    values["guide"] = f"{base}{'de/' if lang == 'de' else ''}assembly.html"
    return fill("template.html", values)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--version", required=True)
    ap.add_argument("--dist", type=Path, default=ROOT / "dist")
    ap.add_argument("--out", type=Path, default=ROOT / "_site")
    args = ap.parse_args()
    out = args.out
    if out.exists():
        shutil.rmtree(out)
    (out / "img").mkdir(parents=True)
    (out / "de").mkdir()
    for name in IMAGES:
        src = ROOT / "docs" / "images" / name
        if src.exists():
            shutil.copy2(src, out / "img" / name)
    shutil.copy2(ROOT / "site" / "favicon.svg", out / "img" / "favicon.svg")
    (out / "index.html").write_text(page("en", args.version, ""), encoding="utf-8")
    (out / "de" / "index.html").write_text(page("de", args.version, "../"), encoding="utf-8")
    (out / "assembly.html").write_text(assembly_page("en", ""), encoding="utf-8")
    (out / "de" / "assembly.html").write_text(assembly_page("de", "../"), encoding="utf-8")
    shutil.copy2(ROOT / "site" / "assembly.js", out / "assembly.js")
    assembly_model.write(out / "models")
    (out / ".nojekyll").write_text("", encoding="utf-8")
    manifests(args.version, args.dist, out)
    print(f"written: {out}")


if __name__ == "__main__":
    main()
