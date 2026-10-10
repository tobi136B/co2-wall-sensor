# Druck und Aufbau

[English](../assembly.md) | **Deutsch**

![Explosionsansicht](../images/exploded_view.png)

**Lieber in 3D?** Die [interaktive Aufbauanleitung](https://tobi136b.github.io/co2-wall-sensor/de/assembly.html) geht alle 12 Schritte durch. Gerät drehen, mit dem Schieberegler zerlegen, durch das Gehäuse schauen und sehen, welches Teil als Nächstes kommt.

[![3D-Aufbauanleitung](../images/assembly_guide_de.png)](https://tobi136b.github.io/co2-wall-sensor/de/assembly.html)

## 1. 3D-Druck

Jedes Teil trägt auf einer verdeckten Fläche seinen Namen, die Version und die Drucklage als eingeprägte Beschriftung.

| Teil | Datei | Ausrichtung | Hinweise |
|------|-------|-------------|----------|
| Gehäuse | [`housing.stl`](../../cad/stl/housing.stl) | Front nach unten | Die Front liegt auf dem Druckbett (eine strukturierte PEI-Platte sieht super aus). Ein 45° Fuß an der Frontkante verhindert den Elefantenfuß. Kein Stützmaterial. |
| Sensorträger | [`sensor_carrier_14x22.stl`](../../cad/stl/sensor_carrier_14x22.stl) oder [`sensor_carrier_15x20.stl`](../../cad/stl/sensor_carrier_15x20.stl) | stehend auf der Unterkante | **Passend zu deiner SCD41-Platine**, siehe [Sensor ausmessen](sensor-ausmessen.md). Stehend gedruckt werden die Schienen zu senkrechten Kanälen, beide Federzungen wachsen nach oben und die Kabelbrücke druckt ohne Stützmaterial. 5 mm Brim verwenden. |
| Rückdeckel | [`back_cover.stl`](../../cad/stl/back_cover.stl) | Innenseite nach unten | Beschriftung "THIS FACE DOWN". Schiene zeigt nach oben, kein Stützmaterial. Derselbe Deckel für beide Kabelausgänge. |
| Wandplatte | [`wall_plate.stl`](../../cad/stl/wall_plate.stl) | **Sichtseite nach unten** | Die Front bekommt die Oberfläche des Druckbetts. Andersherum müsste die 78 mm große Aussparung für den Dosenrand frei überbrückt werden. |
| Tischständer | [`desk_stand.stl`](../../cad/stl/desk_stand.stl) | auf der Seite | Auf der Seite gedruckt ist die Schiene am stabilsten. |

**Empfohlene Einstellungen:** PETG, 0,2 mm Schichthöhe, 3 Wände, 20 % Gyroid, Nahtposition "hinten" oder "ausgerichtet". PLA geht auch, kann aber im Sommer hinter einem sonnigen Fenster weich werden.

**Zwei Farben:** Gehäuse in Mattschwarz oder Anthrazit, Wandplatte in der Farbe der Lichtschalter (meist Reinweiß). Das Ergebnis wirkt wie ein Schaltereinsatz im Rahmen.

**Passung zu stramm oder zu locker?** Alle Schiebe- und Steckpassungen hängen an einem Wert, `FIT` (0,3 mm je Seite). In Fusion unter *Ändern > Parameter ändern* anpassen, Skript erneut starten und das betroffene Teil neu drucken. Siehe [Designnotizen](design.md#parameter-in-fusion).

## 2. Verbindungselemente: eine Schraubensorte für alles

| Anz. | Teil | Wo |
|----:|------|----|
| 10 | Einschmelzmutter **M2 × 3**, Außendurchmesser 3,0 oder 3,2 mm (Bohrung Ø 2,9 × 3,4 mm passt für beide) | 4 Display, 4 Rückdeckel, 2 Sensorträger |
| 10 | Linsenkopfschraube (Halbrundkopf) **M2 × 4**, ISO 7380, Innensechskant 1,3 mm | gleiche Stellen |
| 2 | Schraube **M4** mit 6er Dübel, Linsen- oder Senkkopf | Wandplatte |

Die Wandplatte hat 5 mm breite Langlöcher mit 3 mm Spiel nach oben und unten und einer 45°-Senkung, so liegen Linsen- und Senkköpfe unter ihrer Oberfläche. Die beiden Schrauben einer Hohlwanddose (60 mm Abstand) passen in dieselben Langlöcher. Im Gerät ist nichts geklebt.

## 3. Kabelaustritt wählen

Beide Wege gehen mit denselben gedruckten Teilen:

| Kabel | Was du brauchst | Einsatz |
|-------|-----------------|---------|
| **Nach hinten** | USB-C-Winkeladapter 90° (Stecker auf Buchse) in der Buchse des ESP32-C3, darin ein beliebiges USB-C-Kabel | Hohlwanddose und **immer auf dem Tischständer** |
| **Nach unten** | gerader USB-C-Stecker, Steckerkörper höchstens 12 × 7 mm | Kabel auf Putz, Powerbank unter dem Gerät |

<img src="../images/cable_port_back.png" width="49%" alt="Kabel nach hinten"> <img src="../images/cable_port_bottom.png" width="49%" alt="Kabel nach unten">

Der Adapter zeigt zur Wand und geht durch das Loch im Rückdeckel, das Kabel läuft gerade durch den Durchlass der Wandplatte in die Dose. Ein gerader Stecker sitzt im Fenster in der Bodenwand, das ihn stramm hält. Mit dem Stecker unten bleibt das Loch im Rückdeckel einfach leer, es zeigt ja zur Wand.

Das Loch ist großzügig (Adapterkörper 14 × 8 mm plus 0,6 mm Spiel). Für einen größeren Adapter `ADAPTER_W`, `ADAPTER_T` und `ADAPTER_L` in Fusion ändern, siehe [Designnotizen](design.md#parameter-in-fusion).

## 4. Schritt für Schritt

**Bevor du anfängst, leg dir bereit:** Lötkolben mit feiner Spitze, Innensechskant 1,3 mm, kleiner Schlitzschraubendreher, Seitenschneider. Alle 12 Schritte gibt es auch in der [3D-Aufbauanleitung](https://tobi136b.github.io/co2-wall-sensor/de/assembly.html), dort kannst du jeden Schritt drehen und das Gerät zerlegen.

<!-- steps:start (generated from site/assembly_steps.yaml) -->

### Schritt 1 von 12: Das Gehäuse

<img src="../images/steps/step_01.png" width="60%" alt="Das Gehäuse">

**Du brauchst:** Gedrucktes Gehäuse

Mit der Front nach unten gedruckt. Du schaust von hinten darauf, auf die Seite, die später zur Wand zeigt. Rechts und links sind in dieser Anleitung immer von hinten gesehen, so wie hier. ([in 3D ansehen](https://tobi136b.github.io/co2-wall-sensor/de/assembly.html#step-1))

> **Tipp:** Kein Stützmaterial nötig. Den Rand (Brim) entfernen und prüfen, dass die vier Deckelsitze in den Ecken sauber sind.

### Schritt 2 von 12: 10 Einschmelzmuttern

<img src="../images/steps/step_02.png" width="60%" alt="10 Einschmelzmuttern">

**Du brauchst:** 10 Einschmelzmuttern M2 × 3, Lötkolben auf 200 bis 220 °C

Die M2-Muttern mit dem Lötkolben eindrücken (ca. 200 bis 220 °C). 4 rund um den Displayschacht, 4 für den Rückdeckel, 2 für den Sensorträger. Die Einführschräge zentriert sie. ([in 3D ansehen](https://tobi136b.github.io/co2-wall-sensor/de/assembly.html#step-2))

> **Tipp:** Mutter auf das Loch setzen, mit dem Lötkolben antippen und unter Eigengewicht einsinken lassen, bis sie bündig ist. Nicht drücken. Hinter den 4 Displaydomen ist die Front nur 1,1 mm dick: wenig Hitze, kein Druck.

### Schritt 3 von 12: Display

<img src="../images/steps/step_03.png" width="60%" alt="Display">

**Du brauchst:** Display mit eingestecktem Kabel, 4 Schrauben M2 × 4, Innensechskant 1,3 mm

Zuerst das mitgelieferte Kabel ins Display stecken. Dann mit dem Glas voran in den Displayschacht, Stecker nach links, und 4 Schrauben M2 × 4 durch die Ecklöcher. ([in 3D ansehen](https://tobi136b.github.io/co2-wall-sensor/de/assembly.html#step-3))

> **Tipp:** Es passt nur in einer Richtung: Stecker nach links, wo der Schacht länger ist. Dann steht das Bild aufrecht und der Elektronikstreifen verschwindet hinter dem Rahmen. Die Schutzfolie auf dem Glas bis zum Schluss drauflassen.

### Schritt 4 von 12: Sensorträger

<img src="../images/steps/step_04.png" width="60%" alt="Sensorträger">

**Du brauchst:** Sensorträger für deine SCD41-Platine

Der Träger ist der herausnehmbare Boden der Sensorkammer und hält auf seiner Rückseite den ESP32-C3. Drucke den, der zu deiner SCD41-Platine passt, hier die Version 13,5 × 21,75 mm. ([in 3D ansehen](https://tobi136b.github.io/co2-wall-sensor/de/assembly.html#step-4))

> **Tipp:** Unsicher, welche Platine du hast? Siehe [Sensor ausmessen](sensor-ausmessen.md).

### Schritt 5 von 12: SCD41 in die Schienen

<img src="../images/steps/step_05.png" width="60%" alt="SCD41 in die Schienen">

**Du brauchst:** SCD41, 4 Litzen von ca. 8 cm, Lötkolben

Zuerst vier Litzen von ca. 8 cm an die Lötpunkte löten. Dann die Platine von oben einschieben, Sensor zeigt zu dir, Lötpunkte zum Kabelschlitz, bis die Federzunge über die Oberkante schnappt. ([in 3D ansehen](https://tobi136b.github.io/co2-wall-sensor/de/assembly.html#step-5))

> **Tipp:** Zum Herausnehmen die Federzunge mit einem kleinen Schraubendreher zurückdrücken.

### Schritt 6 von 12: ESP32-C3 auf den Schlitten

<img src="../images/steps/step_06.png" width="60%" alt="ESP32-C3 auf den Schlitten">

**Du brauchst:** ESP32-C3 SuperMini

Bauteile nach oben, USB-C-Buchse nach unten. Oben auf den Schlitten legen und zwischen den Führungen nach unten schieben, bis er auf den Anschlägen steht. Der Haken schnappt hinter seine Oberkante. ([in 3D ansehen](https://tobi136b.github.io/co2-wall-sensor/de/assembly.html#step-6))

> **Tipp:** Zum Herausnehmen den Haken mit einem kleinen Schraubendreher nach unten drücken und die Platine nach oben schieben.

### Schritt 7 von 12: USB-C-Adapter

<img src="../images/steps/step_07.png" width="60%" alt="USB-C-Adapter">

**Du brauchst:** USB-C-Winkeladapter 90° (Stecker auf Buchse)

Den Adapter von unten in die Buchse des ESP32-C3 stecken, sein Körper zeigt nach hinten. Der Träger ist unter der Buchse offen. Später geht das Kabel gerade nach hinten in die Wanddose. ([in 3D ansehen](https://tobi136b.github.io/co2-wall-sensor/de/assembly.html#step-7))

> **Tipp:** Lieber ein Kabel auf Putz? Den Adapter weglassen und später ein gerades Kabel von unten durch das Fenster im Gehäuseboden einstecken.

### Schritt 8 von 12: Träger ins Gehäuse

<img src="../images/steps/step_08.png" width="60%" alt="Träger ins Gehäuse">

**Du brauchst:** 2 Schrauben M2 × 4

Den Träger auf die Leisten im Kinn legen, der Schlitten gleitet über den Displaystecker. Mit 2 Schrauben M2 × 4 festschrauben. ([in 3D ansehen](https://tobi136b.github.io/co2-wall-sensor/de/assembly.html#step-8))

> **Tipp:** Die vier SCD41-Litzen vorher von der offenen Seite in den schmalen Kabelschlitz legen, dann bleibt die Sensorkammer ohne Kleber von der warmen Elektronik getrennt.

### Schritt 9 von 12: Verdrahtung

<img src="../images/steps/step_09.png" width="60%" alt="Verdrahtung">

**Du brauchst:** Das Kabel des Displays (gekürzt), Lötkolben, den [Verdrahtungsplan](verdrahtung.md)

Display: Das Flachkabel faltet sich an der linken Wand zurück und läuft hinter dem Display hinüber zum Schlitten und unter seiner Brücke durch, jede Ader geht zu ihrem Lötpunkt. SCD41: die 4 Litzen am Kabelkanal des Trägers entlang und über die linke Führung. Farben wie im Verdrahtungsplan. ([in 3D ansehen](https://tobi136b.github.io/co2-wall-sensor/de/assembly.html#step-9))

> **Tipp:** Das Kabel zuerst unter der Brücke durchschieben und die Länge jeder Ader an ihrem Lötpunkt anzeichnen, dann kürzen und löten. Das Kabel bleibt im Display stecken: Zum Ausbauen des Displays nur den Stecker ziehen.

### Schritt 10 von 12: Rückdeckel

<img src="../images/steps/step_10.png" width="60%" alt="Rückdeckel">

**Du brauchst:** Rückdeckel, 4 Schrauben M2 × 4

Den Deckel in seinen Sitz legen, der Adapter geht durch sein Loch. Mit 4 Schrauben M2 × 4 festschrauben. ([in 3D ansehen](https://tobi136b.github.io/co2-wall-sensor/de/assembly.html#step-10))

> **Tipp:** Hinten darf außer dem Adapter nichts überstehen: Die Köpfe liegen versenkt, sonst lässt sich das Gerät nicht auf die Wandplatte schieben.

### Schritt 11 von 12: Wandplatte

<img src="../images/steps/step_11.png" width="60%" alt="Wandplatte">

**Du brauchst:** Wandplatte, 2 Schrauben M4 mit 6er Dübeln (oder die 2 Schrauben einer Hohlwanddose)

Die Platte an die Wand schrauben, Beschriftung zur Wand, 60 mm Abstand zwischen den Schrauben. Die Langlöcher geben 3 mm Spiel nach oben und unten, die Senkungen nehmen Linsen- und Senkköpfe. ([in 3D ansehen](https://tobi136b.github.io/co2-wall-sensor/de/assembly.html#step-11))

> **Tipp:** Strom in einer Unterputzdose: ein USB-Netzteil (Arbeiten an 230 V nur durch eine Elektrofachkraft) oder ein USB-Kabel in der Wand. Das Kabel durch den Durchlass der Platte führen.

### Schritt 12 von 12: Gerät aufsetzen

<img src="../images/steps/step_12.png" width="60%" alt="Gerät aufsetzen">

**Du brauchst:** Nichts

Gerät vor die Platte halten, die Schiene in das verdeckte Fenster stecken und 15 mm nach unten schieben. Fertig. Zum Abnehmen nach oben schieben und abziehen. ([in 3D ansehen](https://tobi136b.github.io/co2-wall-sensor/de/assembly.html#step-12))

> **Tipp:** Das Kabel in den Adapter stecken, bevor du das Gerät auf die Schiene setzt.

<!-- steps:end -->

## 5. Tischständer

Den Winkeladapter verwenden, das Kabel geht nach hinten. Gerät von oben auf die Schiene setzen und nach unten schieben. Das Gerät lehnt 12° nach hinten, 5 mm Luftspalt unten halten die Lüftung frei. Das Kabel läuft durch die Kerbe hinten am Fuß hinaus.

## 6. Inbetriebnahme

**Der einfache Weg:** Firmware auf der [Projektseite](https://tobi136b.github.io/co2-wall-sensor/) direkt aus dem Browser flashen, im selben Fenster das WLAN eintragen und das Gerät in Home Assistant übernehmen. Firmware-Updates erscheinen danach in Home Assistant.

**Selbst bauen:**

1. `esphome/secrets.yaml.example` nach `esphome/secrets.yaml` kopieren und ausfüllen.
2. Im ESPHome Builder in Home Assistant `esphome/co2-wall-sensor-de.yaml` (deutsche Oberfläche) zusammen mit dem Ordner `common` anlegen.
3. Das erste Mal per USB flashen, danach kommen Updates über WLAN (OTA).

**Danach in beiden Fällen:**

1. **Kalibrierung:** Gerät 15 Minuten neben ein offenes Fenster legen, dann in Home Assistant *SCD41 kalibrieren (Frischluft 420 ppm)* drücken. Die automatische Selbstkalibrierung ist zusätzlich aktiv.
2. **Temperatur:** nach 24 Stunden mit einem Referenzthermometer vergleichen und den Unterschied in Home Assistant als *Temperaturkorrektur* eintragen. Die Luftfeuchte wird damit mitkorrigiert.
3. **Höhe:** *Höhe über dem Meer* für deinen Ort einstellen, das macht den CO2-Wert genauer.
4. **Nacht und Außenwerte:** Nachtzeit, Dimmen oder Ausschalten, Fensterhinweis und Außenfühler stellst du alles in Home Assistant ein, siehe [Home Assistant](../../README.de.md#home-assistant).
