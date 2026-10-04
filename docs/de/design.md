# Designnotizen

[English](../design.md) | **Deutsch**

Hier steht, warum das Gerät so aussieht und so funktioniert, wie es ist.

## Ziele

1. Luftqualität, Temperatur, Luftfeuchte und Uhrzeit **auf einem Bildschirm**, lesbar quer durch den Raum.
2. **Kein sichtbares Kabel** an der Wand, aber auch auf dem Schreibtisch nutzbar.
3. **Vertrauenswürdige Messwerte**, die nicht vom Gerät selbst verfälscht werden.
4. Alles nachbaubar und anpassbar: **parametrisches CAD, generierte Doku**.

## Warum ein SCD41?

Günstige „CO2“-Sensoren wie SGP30 oder CCS811 schätzen nur einen CO2-Äquivalenzwert aus flüchtigen organischen Verbindungen. Der SCD41 misst CO2 direkt (photoakustisch, NDIR) mit ±(50 ppm + 5 % vom Messwert) und liefert dazu Temperatur und Luftfeuchte. Er braucht freien Luftaustausch, und genau das bestimmt den Aufbau des Gehäuses.

## Thermik

Jedes elektronische Gerät heizt sich selbst auf. Ein ESP32 mit WLAN und ein Display-Hintergrundlicht heben einen eingebauten Sensor schnell um mehrere Kelvin an. Gegenmaßnahmen:

* **Eigene Sensorkammer** im Kinn des Gehäuses, zum Display durch eine Trennwand und zum ESP durch den verschraubten Sensorträger abgeschlossen. Der Träger ist ein eigenes Teil, dadurch lässt sich der SCD41 leicht einbauen und tauschen.
* **Luft kommt von unten** durch 13 Schlitze im Boden und je 3 Schlitze an den Seiten. Warme Luft der Elektronik steigt hinter dem Display nach oben, weg vom Sensor.
* **ESP32-C3 statt klassischem ESP32:** ein Kern, kein USB-UART-Chip, kein Laderegler. Weniger Abwärme.
* **Kabelkerbe mit Heißkleber abgedichtet**, damit keine warme Luft vom ESP in die Kammer gezogen wird.
* **Nachtmodus** dimmt das Hintergrundlicht und reduziert dabei auch die Wärme.
* Der Rest wird mit `temperature_offset` in der Firmware ausgeglichen (Standard 2,0 °C, mit Referenz prüfen).

## Geschlossene Front

Die Front hat keine Öffnungen. Staub setzt sich vor allem auf Öffnungen, die nach oben oder vorne zeigen, und eine durchgehende Front wirkt einfach ruhiger. Alle Lüftungsschlitze zeigen nach unten oder zur Seite.

## Montage: Schwalbenschwanzschiene

Eine kurze Schwalbenschwanzschiene am Rückdeckel passt in zwei Adapter:

* **Wandplatte 82 × 82 mm.** Deutsche Hohlwanddosen haben 68 mm Bohrung und einen Rand von ca. 75 mm, das kompakte Gerät allein würde sie nicht verdecken. Die Platte verdeckt die Dose, wird mit den normalen Geräteschrauben (60 mm) befestigt und hat zum Gerät konzentrische Ecken. So entsteht ein gleichmäßiger Rahmen wie bei einem Lichtschalter.
* **Tischständer.** Gleiche Schiene, das Gerät lehnt für bessere Lesbarkeit 12° nach hinten, mit 5 mm Luftspalt unten, damit die Lüftung frei bleibt.

Das Einsetzfenster über der Nut liegt verdeckt hinter dem Gerät. Gerät von vorne einsetzen und 15 mm nach unten schieben. Von außen ist nichts zu sehen, abnehmen geht ohne Werkzeug.

## Verschraubung: eine Schraubensorte, nur Metallgewinde

Kunststoffgewinde nutzen sich nach wenigen Zyklen ab, und selbstschneidende Schrauben sprengen dünne Dome. Deshalb sitzt an jeder Schraubstelle eine Einschmelzmutter aus Messing, überall mit denselben Teilen:

* **10 × Einschmelzmutter M2 × 3** (Außendurchmesser 3,2 mm, Bohrung Ø 3,0 × 3,4 mm): 4 für das Display, 4 für den Rückdeckel, 2 für den Sensorträger.
* **10 × Linsenkopfschraube (Halbrundkopf) M2 × 4, ISO 7380.** Ein Innensechskantschlüssel für das ganze Gerät.

Der Rückdeckel wird an vier Punkten gehalten: zwei Dome in den unteren Ecken und zwei Einschmelzmuttern in einem massiven 5 mm Band über dem Displayschacht. Die Linsenköpfe sitzen in 1,3 mm tiefen Senkungen, die Deckelfläche bleibt plan und gleitet sauber auf Wandplatte und Tischständer. Der Deckel hat innen weder Stifte noch Haken und druckt flach ohne Stützmaterial.

## Kabelaustritt: Entscheidung nach dem Druck

Der ESP32-C3 sitzt mit der USB-C-Buchse **nach unten**, darunter sind 13 mm frei. Zwei Ausbrechfelder mit 0,6 mm sind vorbereitet und bündig mit der Außenfläche, also unsichtbar:

* **Rückdeckel:** für einen Winkelstecker. Das Kabel geht direkt in die Hohlwanddose oder durch den Tischständer.
* **Unterseite:** für einen geraden Stecker, wenn das Kabel auf Putz läuft.

Man druckt ein Gehäuse und entscheidet vor Ort, welche Membran herausgebrochen wird. Die andere bleibt zu.

## Stromversorgung

Das Gerät hängt dauerhaft an USB-C (ca. 0,5 W, grob 4 bis 5 kWh im Jahr). Eine Akkuversion wurde geprüft und verworfen: Ein Farbdisplay braucht dauerhaft Strom, und Lithiumzellen in einem geschlossenen Gehäuse an der Wand sind ein unnötiges Risiko.

## Parametrisches CAD und generierte Doku

Das Gehäuse wird nicht von Hand modelliert. [`generate_enclosure.py`](../../cad/fusion/generate_enclosure/generate_enclosure.py) baut alle Teile aus einem einzigen Parameterblock, prüft Wand- und Tischaufbau auf Kollisionen und exportiert auf Wunsch STL und STEP. [Technische Zeichnung](../../tools/drawing.py), [Verdrahtungsplan](../../tools/wiring.py) und [Displayvorschau](../../tools/display_preview.py) entstehen aus denselben Quellen. Wer ein Maß ändert, hält Modell, Zeichnung und Doku automatisch gleich.
