# Druck und Aufbau

## 3D-Druck

| Teil | Datei | Druckausrichtung | Hinweise |
|------|-------|------------------|----------|
| Gehäuse | `cad/stl/gehaeuse_front.stl` | Front nach unten | Glatte Front direkt auf dem Druckbett (Texturplatte sieht edel aus). Kein Support nötig. |
| Rückdeckel | `cad/stl/rueckdeckel.stl` | Innenseite nach unten | Schiene zeigt nach oben, kein Support. |
| Wandplatte | `cad/stl/wandplatte_hohlwanddose.stl` | Wandseite nach unten | Die Schwalbenschwanznut druckt ohne Support (45° Überhang). |
| Tischständer | `cad/stl/tischstaender.stl` | Seitlich liegend | Seitlich gedruckt wird die Schiene am stabilsten. |

**Empfohlene Einstellungen:** PETG, 0,2 mm Schichthöhe, 3 Wandlinien, 20 % Gyroid. PLA geht auch, kann sich aber im Sommer hinter einem sonnigen Fenster verformen.

**Zweifarbig:** Gehäuse in Mattschwarz oder Anthrazit, Wandplatte in der Farbe deiner Schalter (meist Reinweiß). Das sieht aus wie ein Schaltereinsatz im Rahmen.

## Teile einsetzen

1. **Einschmelzmuttern:** 2 × M3 in die beiden Dome unten im Gehäuse mit dem Lötkolben (ca. 220 °C) einsetzen.
2. **Display:** Mit dem Glas nach vorne in die Tasche legen, der PH2.0-Stecker zeigt zur Seite mit dem Platz für den Stecker. Mit 4 × M2 × 4 Kunststoffschrauben (Blechschrauben) an den Domen festschrauben.
3. **SCD41:** Vorne in die Sensorkammer, die Sensoröffnung zeigt zu den Lüftungsschlitzen. Mit doppelseitigem Schaumklebeband fixieren. **Hinweis:** Die Sensorkammer ist für eine Platine von etwa 24 × 22 mm ausgelegt. Bei anderen Maßen den Parameter `SCD_B/SCD_H/SCD_T` im Generator anpassen.
4. **ESP32-C3:** Hinten auf die Rippen legen, USB-C zeigt nach oben zum Kabelaustritt. Der Rückdeckel drückt ihn mit zwei Stiften fest.
5. **Kabel:** USB-C-Winkelstecker einstecken, Kabel durch den Kabelaustritt im Rückdeckel führen.
6. **Rückdeckel:** Oben mit den zwei Nasen einhängen, unten zuklappen und mit 2 × M3 × 6 Senkkopfschrauben verschrauben.

## Wandmontage auf der Hohlwanddose

1. Strom in die Dose bringen: entweder ein **Unterputz-USB-Netzteil** (Arbeiten an 230 V nur durch eine Elektrofachkraft) oder ein USB-Kabel, das in der Wand zu einer Steckdose führt.
2. Wandplatte mit den beiden **Geräteschrauben der Dose** (60 mm Abstand, waagrecht) festschrauben. Die Langlöcher gleichen eine schief sitzende Dose aus.
3. USB-Kabel durch den Kabeldurchlass führen und am Gerät einstecken.
4. Gerät vor die Platte halten, mit der Schiene in das Einsetzfenster stecken und **15 mm nach unten schieben**. Fertig.

## Tischständer

Gerät von oben auf die Schiene setzen und nach unten schieben. Das Gerät lehnt 12° nach hinten, unten bleibt ein Luftspalt für die Lüftung. Das Kabel läuft hinten durch die Kerbe im Fuß weg.

## Inbetriebnahme

1. `esphome/secrets.yaml.example` nach `esphome/secrets.yaml` kopieren und ausfüllen.
2. In Home Assistant das ESPHome Builder Add-on öffnen und `esphome/co2-wandsensor.yaml` als neues Gerät anlegen.
3. Beim ersten Mal per USB flashen, danach geht alles per WLAN (OTA).
4. Home Assistant findet das Gerät automatisch. Integration bestätigen, fertig.
5. **Kalibrierung:** Das Gerät 15 Minuten ans offene Fenster stellen und dann in Home Assistant den Knopf *SCD41 kalibrieren (Frischluft 420 ppm)* drücken. Die automatische Selbstkalibrierung ist zusätzlich aktiv.
6. **Temperatur abgleichen:** Nach 24 h mit einem Referenzthermometer vergleichen und `temperatur_offset` in der YAML anpassen.
