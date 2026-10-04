# Druck und Aufbau

[English](../assembly.md) | **Deutsch**

## 1. 3D-Druck

| Teil | Datei | Ausrichtung | Hinweise |
|------|-------|-------------|----------|
| Gehäuse | [`cad/stl/housing.stl`](../../cad/stl/housing.stl) | Front nach unten | Die Front liegt direkt auf dem Druckbett (Texturplatte sieht edel aus). Kein Support nötig. |
| Rückdeckel | [`cad/stl/back_cover.stl`](../../cad/stl/back_cover.stl) | Innenseite nach unten | Schiene zeigt nach oben, kein Support. |
| Wandplatte | [`cad/stl/wall_plate.stl`](../../cad/stl/wall_plate.stl) | Wandseite nach unten | Die Schwalbenschwanznut druckt ohne Support (45° Überhang). |
| Tischständer | [`cad/stl/desk_stand.stl`](../../cad/stl/desk_stand.stl) | seitlich liegend | Seitlich gedruckt ist die Schiene am stabilsten. |

**Empfohlene Einstellungen:** PETG, 0,2 mm Schichthöhe, 3 Wandlinien, 20 % Gyroid. PLA geht auch, kann aber im Sommer hinter einem sonnigen Fenster weich werden.

**Zweifarbig:** Gehäuse in Mattschwarz oder Anthrazit, Wandplatte in der Farbe deiner Lichtschalter (meist Reinweiß). Das sieht aus wie ein Schaltereinsatz im Rahmen.

## 2. Vorbereitung

1. **Einschmelzmuttern:** 2 × M3 mit dem Lötkolben (ca. 220 °C) in die beiden Dome unten im Gehäuse einsetzen.
2. **Elektronik zuerst auf dem Tisch testen.** Alles nach [verdrahtung.md](verdrahtung.md) verbinden, Firmware flashen und das Display prüfen, bevor du einbaust.

## 3. Zusammenbau

1. **Display:** mit dem Glas voran in die Displaytasche legen. Der PH2.0-Stecker zeigt zur Seite mit der Aussparung für den Stecker. Mit 4 × M2 × 4 Kunststoffschrauben festschrauben.
2. **SCD41:** vorne in die Sensorkammer, Sensoröffnung zu den Lüftungsschlitzen. Mit doppelseitigem Schaumklebeband fixieren.
   > Die Kammer ist für eine Platine von ca. 24 × 22 mm ausgelegt. Bei anderen Maßen `SCD_W/SCD_H/SCD_T` im Generator anpassen.
3. **Kabelkerbe abdichten:** die SCD41-Leitungen durch die Kerbe im Zwischenboden führen und die Kerbe mit einem Tropfen Heißkleber schließen. So zieht keine warme Luft vom ESP in die Sensorkammer.
4. **ESP32-C3:** hinten auf die Rippen legen, USB-C zeigt nach oben zum Kabelaustritt. Der Rückdeckel drückt ihn mit zwei Stiften fest.
5. **Kabel:** USB-C-Winkelstecker einstecken und durch den Kabelaustritt im Rückdeckel führen.
6. **Rückdeckel:** oben mit den zwei Nasen einhängen, zuklappen und mit 2 × M3 × 6 Senkkopfschrauben verschrauben.

## 4. Wandmontage auf der Hohlwanddose

1. **Strom in die Dose bringen:** entweder ein Unterputz-USB-Netzteil (Arbeiten an 230 V nur durch eine Elektrofachkraft) oder ein USB-Kabel, das in der Wand zu einer Steckdose führt.
2. **Wandplatte festschrauben** mit den beiden Geräteschrauben der Dose (60 mm Abstand, waagrecht). Die Langlöcher gleichen eine leicht verdrehte Dose aus.
3. USB-Kabel durch den Kabeldurchlass führen und am Gerät einstecken.
4. **Gerät aufsetzen:** vor die Platte halten, die Schiene in das verdeckte Einsetzfenster stecken und **15 mm nach unten schieben**. Fertig.

Zum Abnehmen 15 mm nach oben schieben und abziehen.

## 5. Tischständer

Gerät von oben auf die Schiene setzen und nach unten schieben. Das Gerät lehnt 12° nach hinten, ein Luftspalt von 5 mm hält die Lüftung unten frei. Das Kabel läuft hinten durch die Kerbe im Fuß weg.

## 6. Inbetriebnahme

1. `esphome/secrets.yaml.example` nach `esphome/secrets.yaml` kopieren und ausfüllen.
2. Im ESPHome Builder in Home Assistant `esphome/co2-wall-sensor-de.yaml` (deutsch) oder `esphome/co2-wall-sensor.yaml` (englisch) zusammen mit dem Ordner `common` anlegen.
3. Beim ersten Mal per USB flashen, danach laufen Updates über WLAN (OTA).
4. Home Assistant findet das Gerät. Integration bestätigen.
5. **Kalibrierung:** das Gerät 15 Minuten an ein offenes Fenster stellen und dann in Home Assistant *SCD41 kalibrieren (Frischluft 420 ppm)* drücken. Die automatische Selbstkalibrierung ist zusätzlich aktiv.
6. **Temperatur:** nach 24 Stunden mit einem Referenzthermometer vergleichen und `temperature_offset` in der Gerätedatei anpassen.
