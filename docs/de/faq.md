# FAQ

[English](../faq.md) | **Deutsch**

### Wie genau ist der CO2-Wert?
Der SCD41 ist mit ±(50 ppm + 5 % vom Messwert) zwischen 400 und 5000 ppm spezifiziert. Die automatische Selbstkalibrierung geht davon aus, dass das Gerät mindestens einmal pro Woche Frischluft (ca. 420 ppm) sieht, was in gelüfteten Räumen normal ist. Wird der Raum nie richtig gelüftet, `automatic_self_calibration` abschalten und stattdessen die Kalibriertaste nutzen.

### Welche Schwellen sind sinnvoll?
Standard sind 1000 ppm (Gelb) und 1400 ppm (Rot). Werte unter 1000 ppm gelten allgemein als unbedenklich, über 2000 ppm sollte dringend gelüftet werden. Beide Schwellen lassen sich jederzeit in Home Assistant ändern.

### Die Temperatur ist zu hoch.
Nach 24 Stunden mit einem Referenzthermometer vergleichen und `temperature_offset` in der Gerätedatei anpassen. Prüfen, ob die Kabelkerbe zwischen ESP-Bereich und Sensorkammer abgedichtet ist.

### Kann ich ein anderes ESP32-Board nehmen?
Ja. Jeder von ESPHome unterstützte ESP32 funktioniert, aber die Pins in `esphome/common/base.yaml` und die Aufnahme im Generator müssen angepasst werden. Der ESP32-C3 SuperMini wurde wegen Größe, USB-C und geringer Abwärme gewählt.

### Kann ich ein anderes Display nehmen?
Jedes ST7789-Display mit 240 × 320 und SPI funktioniert mit kleinen Änderungen. Andere Außenmaße brauchen neue Werte für `LCD_W`, `LCD_H`, `GLASS_*`, `ACTIVE_*` und `LCD_HOLE_*` im Generator.

### Geht Batteriebetrieb?
Nicht sinnvoll. Das Farbdisplay braucht dauerhaft Strom. Ein Akkugerät bräuchte E-Paper und Tiefschlaf, das wäre ein anderes Design.

### Meine Hohlwanddose sitzt hochkant.
Die Wandplatte nutzt die beiden waagrechten Geräteschrauben. Die meisten Hohlwanddosen bieten waagrechte und senkrechte Schraubpositionen. Hat deine nur senkrechte, im Generator `ScrewSlots` um 90° drehen.

### Kann ich die fertigen Firmware-Dateien direkt nutzen?
Nur für einen schnellen Hardwaretest. Die Release-Dateien baut die CI ohne echte Zugangsdaten: Sie öffnen den Hotspot „CO2 Wandsensor Setup“ (Passwort `co2-sensor-setup`), über den du Display und Sensor prüfen kannst, in Home Assistant tauchen sie nur mit dem CI-Schlüssel auf. Flashen mit [ESPHome Web](https://web.esphome.io). Für den Alltag die Firmware immer selbst mit eigener `secrets.yaml` bauen.

### Welche Einschmelzmuttern und Schrauben genau?
Handelsübliche Einschmelzmuttern M2 × 3 mit 3,2 mm Außendurchmesser (die verbreiteten Packungen „M2 x 3 x 3,2“) und Linsenkopfschrauben M2 × 4 nach ISO 7380. Muttern mit anderem Außendurchmesser gehen, wenn im Generator `INSERT_HOLE_D` angepasst wird.

### Kabel von unten oder von hinten?
Beides ist als Ausbrechfeld vorbereitet. Hinten mit Winkelstecker für die Hohlwanddose und den Tischständer, unten mit geradem Stecker für ein Kabel auf Putz. Siehe [Aufbau](aufbau.md#4-kabelaustritt-wählen).

### Warum werden Zeichnung und Bilder generiert?
Damit sie immer zum Modell passen. Parameter ändern, Tools starten, committen. Die CI prüft, ob die Tools weiterhin laufen.
