# Verdrahtung

[English](../wiring.md) | **Deutsch**

![Verdrahtungsplan](../images/wiring_de.png)

Alle Module laufen mit 3,3 V direkt aus dem ESP32-C3 SuperMini. Strom kommt über die USB-C-Buchse des ESP.

## ESP32-C3 SuperMini zu Waveshare 2inch LCD (SPI)

| LCD | ESP32-C3 | Funktion |
|-----|----------|----------|
| VCC | 3V3      | Versorgung 3,3 V |
| GND | GND      | Masse |
| DIN | GPIO6    | SPI MOSI |
| CLK | GPIO4    | SPI Takt |
| CS  | GPIO7    | Chip Select |
| DC  | GPIO5    | Daten / Kommando |
| RST | GPIO3    | Reset |
| BL  | GPIO10   | Hintergrundlicht (PWM, dimmbar) |

## ESP32-C3 SuperMini zu SCD41 (I2C)

| SCD41 | ESP32-C3 | Funktion |
|-------|----------|----------|
| VDD   | 3V3      | Versorgung 3,3 V |
| GND   | GND      | Masse |
| SDA   | GPIO0    | I2C Daten |
| SCL   | GPIO1    | I2C Takt |

## Warum genau diese Pins?

* **GPIO2, GPIO8 und GPIO9** sind Strapping-Pins des ESP32-C3 (GPIO8 hängt zusätzlich an der blauen LED, GPIO9 am BOOT-Taster). Sie bleiben frei, damit das Board immer sauber startet.
* **GPIO18 und GPIO19** sind die USB-Datenleitungen und bleiben ebenfalls frei.
* **GPIO10** ist PWM-fähig und dimmt das Hintergrundlicht, damit funktioniert der Nachtmodus.

Der Plan wird mit `python tools/wiring.py` direkt aus `esphome/common/base.yaml` erzeugt. Wer Pins in der YAML ändert, erzeugt den Plan einfach neu.

## Tipps

* **Display:** Das beiliegende PH2.0-Kabel auf ca. 5 cm kürzen und direkt an den ESP löten. Es läuft gerade über die Rückseite des Displays zum oberen Ende des ESP32-C3, diesen Weg hält das Gehäuse frei.
* **SCD41:** 4 Litzen AWG 30 von ca. 8 cm. Sie liegen nebeneinander im schmalen Kabelschlitz des Sensorträgers und auf der Rückseite unter der Lippe des Kabelclips. Kleber ist nicht nötig.
* Der SCD41 zieht für wenige Millisekunden bis ca. 200 mA. Der 3,3-V-Regler des SuperMini schafft das, die Versorgungsleitungen trotzdem kurz halten.
* Alles zuerst auf dem Tisch testen, dann einbauen.
