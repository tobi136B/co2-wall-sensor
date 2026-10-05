# Druck und Aufbau

[English](../assembly.md) | **Deutsch**

![Explosionsansicht](../images/exploded_view.png)

## 1. 3D-Druck

Jedes Teil trägt auf einer verdeckten Fläche seinen Namen, die Version und die Drucklage als eingeprägte Beschriftung.

| Teil | Datei | Ausrichtung | Hinweise |
|------|-------|-------------|----------|
| Gehäuse | [`housing.stl`](../../cad/stl/housing.stl) | Front nach unten | Die Front liegt auf dem Druckbett (eine strukturierte PEI-Platte sieht super aus). Ein 45° Fuß an der Frontkante verhindert den Elefantenfuß. Kein Stützmaterial. |
| Sensorträger | [`sensor_carrier.stl`](../../cad/stl/sensor_carrier.stl) | stehend auf der Unterkante | Die Schienen werden so zu senkrechten Kanälen. 5 mm Brim verwenden. |
| Rückdeckel | [`back_cover.stl`](../../cad/stl/back_cover.stl) | Innenseite nach unten | Beschriftung "THIS FACE DOWN". Schiene zeigt nach oben, kein Stützmaterial. |
| Kabelport hinten | [`cable_port_back.stl`](../../cad/stl/cable_port_back.stl) | große Rückfläche nach unten | Für einen Winkelstecker. |
| Kabelport unten | [`cable_port_bottom.stl`](../../cad/stl/cable_port_bottom.stl) | große Rückfläche nach unten | Für einen geraden Stecker. Am besten beide drucken, je 2 g. |
| Wandplatte | [`wall_plate.stl`](../../cad/stl/wall_plate.stl) | **Sichtseite nach unten** | Die Front bekommt die Oberfläche des Druckbetts. Andersherum müsste die 78 mm große Aussparung für den Dosenrand frei überbrückt werden. |
| Sicherungslasche (optional) | [`lock_tab.stl`](../../cad/stl/lock_tab.stl) | Vorderseite nach unten | Nur nötig, wenn sich das Gerät nicht ohne Werkzeug abnehmen lassen soll. |
| Tischständer | [`desk_stand.stl`](../../cad/stl/desk_stand.stl) | auf der Seite | Auf der Seite gedruckt ist die Schiene am stabilsten. |

**Empfohlene Einstellungen:** PETG, 0,2 mm Schichthöhe, 3 Wände, 20 % Gyroid, Nahtposition "hinten" oder "ausgerichtet". PLA geht auch, kann aber im Sommer hinter einem sonnigen Fenster weich werden.

**Zwei Farben:** Gehäuse in Mattschwarz oder Anthrazit, Wandplatte in der Farbe der Lichtschalter (meist Reinweiß). Das Ergebnis wirkt wie ein Schaltereinsatz im Rahmen.

**Passung zu stramm oder zu locker?** Alle Schiebe- und Steckpassungen hängen an einem Wert, `FIT` (0,3 mm je Seite). In Fusion unter *Ändern > Parameter ändern* anpassen, Skript erneut starten und das betroffene Teil neu drucken. Siehe [Designnotizen](design.md#parameter-in-fusion).

## 2. Verbindungselemente: eine Schraubensorte für alles

| Anz. | Teil | Wo |
|----:|------|----|
| 10 | Einschmelzmutter **M2 × 3**, Außendurchmesser 3,2 mm (Bohrung Ø 3,0 × 3,4 mm) | 4 Display, 4 Rückdeckel, 2 Sensorträger |
| 10 | Linsenkopfschraube (Halbrundkopf) **M2 × 4**, ISO 7380, Innensechskant 1,3 mm | gleiche Stellen |
| +2 | dieselbe Mutter und Schraube | optionale Sicherungslasche: 1 im Gehäuse, 1 in der Wandplatte |

Die einzigen anderen Schrauben sind die beiden, die der Hohlwanddose beiliegen. Im Gerät ist nichts geklebt.

## 3. Vormontage

1. **Einschmelzmuttern eindrücken** mit dem Lötkolben (ca. 200 bis 220 °C, wenn vorhanden mit M2-Spitze). Jedes Loch hat eine kleine Einführschräge, die die Mutter zentriert. Unter Eigengewicht einsinken lassen und bündig aufhören.
   * 4 in die Displaydome rund um den Displayschacht. Die Front dahinter ist nur 1,1 mm dick, also mit wenig Temperatur und wenig Druck arbeiten.
   * 4 für den Rückdeckel: 2 in den unteren Ecken, 2 im massiven Band über dem Display.
   * 2 für den Sensorträger in die kurzen Dome im Kinn.
   * Optionale Sicherung: 1 von außen in die Unterseite des Gehäuses, 1 vorne in die Wandplatte unterhalb des Geräts.
2. **Elektronik zuerst auf dem Tisch testen.** Nach [verdrahtung.md](verdrahtung.md) verdrahten, Firmware flashen und das Display prüfen, bevor alles eingebaut wird.

## 4. Kabelaustritt wählen

Das Kabel verlässt das Gerät durch ein kleines, tauschbares **Kabelport-Modul** an der unteren hinteren Kante. Beide Versionen drucken und vor Ort entscheiden:

| Modul | Stecker | Einsatz |
|-------|---------|---------|
| **Port hinten** | USB-C Winkelstecker, "nach oben/unten gewinkelt" | Hohlwanddose und **immer auf dem Tischständer** |
| **Port unten** | gerader USB-C-Stecker, Steckerkörper höchstens 12 × 7 mm | Kabel auf Putz, Powerbank unter dem Gerät |

<img src="../images/cable_port_back.png" width="49%" alt="Kabelport hinten"> <img src="../images/cable_port_bottom.png" width="49%" alt="Kabelport unten">

Das Modul wird zwischen Gehäuse und Rückdeckel geklemmt. Eine Stufe in der Unterseite verhindert, dass es herausfällt, eine Lippe unter dem Rückdeckel hält es nach hinten. Den Kabelaustritt später zu wechseln, kostet vier Schrauben.

**Zugentlastung:** Beim Modul hinten sitzt der Körper des Winkelsteckers hinter dem Modul. Zug am Kabel endet am Modul und nicht an der USB-Buchse.

## 5. Zusammenbau

![Innenansicht](../images/interior.png)

1. **Display:** mit dem Glas voran in den Displayschacht legen und mit 4 × M2 × 4 verschrauben.
2. **SCD41:** vier Litzen von ca. 8 cm an GND, VDD, SCL und SDA löten. Die Platine von der Unterkante in die beiden Schienen auf der Frontseite des Sensorträgers schieben, Sensor zeigt vom Träger weg, bis sie hinter der kleinen Rastnase einrastet. Die Litzen durch die Kerbe an der Oberkante führen.

   <img src="../images/sensor_carrier_front.png" width="70%" alt="SCD41 in den Schienen">
3. **ESP32-C3:** die Litzen von Display und SCD41 anlöten ([Verdrahtung](verdrahtung.md)). Zuerst das USB-Kabel in den ESP32-C3 stecken:
   * Modul hinten: das Kabel seitlich in den Schlitz des Moduls legen,
   * Modul unten: den Stecker von außen durch das Modul schieben.

   Dann den ESP32-C3 von oben zwischen die Seitenführungen auf der Rückseite des Trägers schieben, bis die Unterkante auf den Anschlägen sitzt und unter die beiden kleinen Lippen rutscht.

   <img src="../images/sensor_carrier_back.png" width="70%" alt="ESP32-C3 auf der Rückseite des Trägers">
4. **Sensorträger:** auf die Leisten im Kinn legen und mit 2 × M2 × 4 verschrauben. Er schließt die Sensorkammer gegen die warme Elektronik ab. Die Kabelkerbe mit einem Tropfen Heißkleber abdichten.
5. **Kabelport-Modul:** von hinten in die Öffnung an der unteren hinteren Kante schieben.
6. **Rückdeckel:** in den Sitz legen und mit 4 × M2 × 4 verschrauben. Die Linsenköpfe sitzen in Senkungen unter der Oberfläche, der Deckel gleitet weiterhin auf die Wandplatte.

## 6. Wandmontage auf der Hohlwanddose

1. **Strom in die Dose bringen:** entweder ein Unterputz-USB-Netzteil (Arbeiten an 230 V nur durch eine Elektrofachkraft) oder ein USB-Kabel, das in der Wand zu einer Steckdose läuft.
2. **Wandplatte** mit den beiden Geräteschrauben der Dose befestigen (60 mm Abstand, waagrecht). Die Langlöcher gleichen eine leicht verdrehte Dose aus.
3. USB-Kabel durch den Kabeldurchlass führen und ins Gerät stecken.
4. **Gerät aufsetzen:** vor die Platte halten, die Schiene in das verdeckte Einsetzfenster stecken und **15 mm nach unten schieben**. Fertig.
5. **Optionale Sicherung:** die Sicherungslasche unter das Gerät halten, nach oben ins Gehäuse und nach hinten in die Wandplatte schrauben (2 × M2 × 4).

   <img src="../images/lock_tab.png" width="60%" alt="Sicherungslasche unter dem Gerät">

Zum Abnehmen die Lasche lösen (falls montiert), das Gerät 15 mm nach oben schieben und abziehen.

## 7. Tischständer

Das Modul hinten mit Winkelstecker verwenden. Gerät von oben auf die Schiene setzen und nach unten schieben. Das Gerät lehnt 12° nach hinten, 5 mm Luftspalt unten halten die Lüftung frei. Das Kabel läuft durch die Kerbe hinten am Fuß hinaus.

## 8. Inbetriebnahme

**Der einfache Weg:** Firmware auf der [Projektseite](https://tobi136b.github.io/co2-wall-sensor/) direkt aus dem Browser flashen, im selben Fenster das WLAN eintragen und das Gerät in Home Assistant übernehmen. Firmware-Updates erscheinen danach in Home Assistant.

**Selbst bauen:**

1. `esphome/secrets.yaml.example` nach `esphome/secrets.yaml` kopieren und ausfüllen.
2. Im ESPHome Builder in Home Assistant `esphome/co2-wall-sensor-de.yaml` (deutsche Oberfläche) zusammen mit dem Ordner `common` anlegen.
3. Das erste Mal per USB flashen, danach kommen Updates über WLAN (OTA).

**Danach in beiden Fällen:**

1. **Kalibrierung:** Gerät 15 Minuten neben ein offenes Fenster legen, dann in Home Assistant *SCD41 kalibrieren (Frischluft 420 ppm)* drücken. Die automatische Selbstkalibrierung ist zusätzlich aktiv.
2. **Temperatur:** nach 24 Stunden mit einem Referenzthermometer vergleichen und `temperature_offset` in der Gerätedatei anpassen (nach dem Übernehmen im ESPHome Dashboard, wenn du über den Browser geflasht hast).
