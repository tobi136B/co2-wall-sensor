# FAQ

[English](../faq.md) | **Deutsch**

### Wie genau ist der CO2-Wert?
Der SCD41 ist mit ±(50 ppm + 5 % vom Messwert) zwischen 400 und 5000 ppm spezifiziert. Die automatische Selbstkalibrierung geht davon aus, dass das Gerät mindestens einmal pro Woche Frischluft (ca. 420 ppm) sieht, was in gelüfteten Räumen normal ist. Wird der Raum nie richtig gelüftet, `automatic_self_calibration` abschalten und stattdessen die Kalibriertaste nutzen.

### Wie groß darf der Raum für einen Sensor sein?
**Ein Sensor pro Raum.** CO2 verteilt sich innerhalb eines Raumes in wenigen Minuten gleichmäßig, aber Wände und geschlossene Türen trennen die Luft. Ein Sensor im Wohnzimmer sagt also wenig über das Schlafzimmer.

Die Raumgröße ist selten die Grenze. Richtlinien für Gebäude rechnen mit einem Sensor pro 500 m² offener Fläche ([Arc/GBCI](https://arc.gbci.org/sites/default/files/Arc-CO2Guide.pdf)), der Sensorhersteller BAPI nennt höchstens 725 m² bei ruhiger Luft ([BAPI](https://www.bapihvac.com/application_note/air-quality-sensor-coverage-area-and-mounting/)). Jedes Wohnzimmer, Schlafzimmer, Büro oder Klassenzimmer deckt ein Gerät also ab; nur große offene Flächen mit mehreren Zonen brauchen mehr.

Wichtiger als die Größe ist der Platz:
* **Höhe 1 bis 1,5 m**, also im Atembereich sitzender Personen. Die Wandplatte auf einer Hohlwanddose in Schalterhöhe (ca. 1,05 m) ist ideal.
* **Mindestens 1 bis 2 m Abstand zu Personen**, damit niemand den Sensor direkt anatmet (nicht direkt neben Bett oder Schreibtisch).
* **Nicht neben Fenster, Tür, Heizkörper oder Lüftungsauslass** und nicht in direkte Sonne.

### Wofür ist das Fenster unten im Gehäuse?
Dort sitzt ein gerader USB-C-Stecker, wenn das Kabel auf Putz nach unten läuft. Mit dem Winkeladapter und dem Kabel nach hinten bleibt es leer; es liegt neben dem Lüftungsgitter und ist nur von unten sichtbar. Siehe [Aufbau](aufbau.md#3-kabelaustritt-wählen).

### Welche Schwellen sind sinnvoll?
Standard sind 1000 ppm (Gelb) und 1400 ppm (Rot). Werte unter 1000 ppm gelten allgemein als unbedenklich, über 2000 ppm sollte dringend gelüftet werden. Beide Schwellen lassen sich jederzeit in Home Assistant ändern.

### Die Temperatur ist zu hoch.
Nach 24 Stunden mit einem Referenzthermometer vergleichen und `temperature_offset` in der Gerätedatei anpassen. Prüfen, ob alle vier SCD41-Litzen nebeneinander im Kabelschlitz liegen, damit er zwischen ESP-Bereich und Sensorkammer dicht ist.

### Kann ich ein anderes ESP32-Board nehmen?
Ja. Jeder von ESPHome unterstützte ESP32 funktioniert, aber die Pins in `esphome/common/base.yaml` und die Aufnahme im Generator müssen angepasst werden. Der ESP32-C3 SuperMini wurde wegen Größe, USB-C und geringer Abwärme gewählt.

### Kann ich ein anderes Display nehmen?
Jedes ST7789-Display mit 240 × 320 und SPI funktioniert mit kleinen Änderungen. Andere Außenmaße brauchen neue Werte für `LCD_W`, `LCD_H`, `GLASS_*`, `ACTIVE_*` und `LCD_HOLE_*` im Generator.

### Geht Batteriebetrieb?
Nicht sinnvoll. Das Farbdisplay braucht dauerhaft Strom. Ein Akkugerät bräuchte E-Paper und Tiefschlaf, das wäre ein anderes Design.

### Dübel oder Hohlwanddose?
Beides. Die Wandplatte nimmt zwei Schrauben M4 mit 6er Dübeln im Abstand von 60 mm oder die beiden waagrechten Geräteschrauben einer Hohlwanddose. Die Langlöcher geben 3 mm Spiel nach oben und unten. Hat deine Dose nur senkrechte Schraubpositionen, nimm Dübel.

### Browser-Installer oder selbst bauen?
Beides ist vollwertig. Der **Browser-Installer** auf der [Projektseite](https://tobi136b.github.io/co2-wall-sensor/) flasht eine fertige Firmware, in der keine WLAN-Zugangsdaten stecken. Nach dem Flashen trägst du dein WLAN im selben Browserfenster ein (oder über den Hotspot "CO2 Wall Sensor", den das Gerät ohne WLAN öffnet), Home Assistant findet das Gerät, und neue Releases erscheinen in Home Assistant als Firmware-Update. Wer die Konfiguration ändern will, klickt im ESPHome Dashboard auf "Übernehmen": Es holt die passende YAML aus diesem Repository. Der **eigene Build** mit deiner `secrets.yaml` bringt von Anfang an API-Verschlüsselung und volle Kontrolle.

### Telefoniert das Gerät nach Hause?
Nein. Die Firmware prüft nur das Release-Manifest auf der Projektseite auf Updates, und zwar nur, wenn du die Update-Entität aufrufst, oder einmal am Tag. Messwerte verlassen dein Netzwerk nie.

### Welche Einschmelzmuttern und Schrauben genau?
Handelsübliche Einschmelzmuttern M2 × 3 mit 3,0 oder 3,2 mm Außendurchmesser (die verbreiteten Packungen „M2 x 3 x 3“ oder „M2 x 3 x 3,2“) und Linsenkopfschrauben M2 × 4 nach ISO 7380, je 10 Stück. Muttern in anderer Größe gehen, wenn `INSERT_HOLE_D` und `INSERT_HOLE_L` angepasst werden.

### Kabel von unten oder von hinten?
Beides, mit denselben gedruckten Teilen. Nach hinten: ein USB-C-Winkeladapter 90° (Stecker auf Buchse) im ESP32-C3, das Kabel geht gerade in die Hohlwanddose; auf dem Tischständer immer so. Nach unten: ein gerades Kabel durch das Fenster im Boden. Siehe [Aufbau](aufbau.md#3-kabelaustritt-wählen).

### Mein gerader USB-C-Stecker passt nicht.
Das Fenster im Boden nimmt Stecker mit einem Steckerkörper bis 12 × 7 mm. Für dickere Stecker `PLUG_W` und `PLUG_H` anpassen (wird `PLUG_H` größer, wird das Gerät tiefer) oder das Kabel mit dem Winkeladapter nach hinten führen.

### Das Bild auf dem Display steht auf dem Kopf.
In Home Assistant *Display auf dem Kopf* einschalten, das Bild dreht sich sofort um 180°. Wie das Display sitzt, gibt das Gehäuse vor: Sein Stecker ist rechts, von hinten gesehen.

### Meine SCD41-Platine sieht anders aus.
Ausmessen und mit den bekannten Profilen vergleichen. Nur der kleine Sensorträger hängt von der Platine ab, alles andere bleibt gleich. Siehe [Sensor ausmessen](sensor-ausmessen.md).

### Mein ESP32-C3 SuperMini ist etwas anders.
Der Halter ist für Platinen aus anderen Lieferungen ausgelegt. Die Platine liegt auf ganzer Länge auf einem Schlitten, Quetschrippen in den Seitenführungen zentrieren sie, die Führungen nehmen Platinen bis 1,2 mm Dicke, und ein Federhaken schnappt hinter ihre Oberkante. Gemessene Platine: 18,2 × 22,71 × 0,74 mm, USB-C-Buchse 9,0 mm breit, 3,5 mm hoch, 1,5 mm über der Unterkante.

| Maß | passt ohne neuen Druck |
|-----|------------------------|
| Breite | 18,0 bis 18,6 mm |
| Dicke | bis 1,2 mm |
| Länge | 22,0 bis 22,8 mm (eine kürzere Platine hat etwas Spiel) |
| Überstand der USB-C-Buchse | 0,5 bis 2,5 mm |

Außerhalb davon `C3_W`, `C3_H`, `C3_PCB` oder `C3_USB_OUT` im Generator ändern und einen neuen Sensorträger drucken.

### Wie ändere ich ein Maß?
Die erzeugte Konstruktion in Fusion öffnen, *Ändern > Parameter ändern*, Wert anpassen und das Skript erneut starten. Es übernimmt alle Parameter der offenen Konstruktion, baut alle Teile neu und prüft auf Kollisionen. Mit `EXPORT = True` schreibt es auch neue STL- und STEP-Dateien. Siehe [Designnotizen](design.md#parameter-in-fusion).

### Warum werden Zeichnung und Bilder generiert?
Damit sie immer zum Modell passen. Parameter ändern, Tools starten, committen. Die CI erzeugt sie neu, prüft, ob die Druckdateien zu den aktuellen Parametern gehören und ob alle Links in der Doku funktionieren.
