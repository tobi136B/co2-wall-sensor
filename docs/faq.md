# FAQ

**English** | [Deutsch](de/faq.md)

### How accurate is the CO2 reading?
The SCD41 is specified for ±(50 ppm + 5 % of reading) between 400 and 5000 ppm. Automatic self calibration assumes the device sees fresh air (about 420 ppm) at least once a week, which is normal in ventilated rooms. If the room is never aired properly, disable `automatic_self_calibration` and use the calibration button instead.

### How large a room can one sensor monitor?
**One sensor per room.** CO2 spreads evenly within a room in a few minutes, but walls and closed doors separate the air, so a sensor in the living room says little about the bedroom.

The size of the room is rarely the limit. Building guidelines put one sensor per 500 m² of open floor space ([Arc/GBCI](https://arc.gbci.org/sites/default/files/Arc-CO2Guide.pdf)), the sensor manufacturer BAPI gives at most 725 m² in still air ([BAPI](https://www.bapihvac.com/application_note/air-quality-sensor-coverage-area-and-mounting/)). Every living room, bedroom, office or classroom is therefore covered by one device; only open spaces with several zones need more.

Placement matters more than size:
* **Height 1 to 1.5 m**, the breathing zone of seated people. The wall plate on a flush box at switch height (about 1.05 m) is ideal.
* **At least 1 to 2 m away from people**, so nobody breathes directly at the sensor (not right beside the bed or the desk).
* **Not next to windows, doors, radiators or ventilation outlets**, and not in direct sunlight.

### What is the window in the bottom of the housing for?
It takes a straight USB-C plug when the cable runs down the wall. With the 90° adapter and the cable to the back it stays empty; it lies next to the vent mesh and is only visible from below. See [assembly](assembly.md#3-choose-the-cable-exit).

### Which thresholds are sensible?
The defaults are 1000 ppm (yellow) and 1400 ppm (red). Values below 1000 ppm are generally considered harmless, above 2000 ppm ventilation is clearly needed. Both thresholds can be changed in Home Assistant at any time.

### The temperature reads too high.
Compare with a reference thermometer after 24 hours and adjust `temperature_offset` in the device file. Make sure all four SCD41 wires lie side by side in the wire slot, so it seals the sensor chamber against the ESP bay.

### Can I use a different ESP32 board?
Yes. Any ESP32 supported by ESPHome works, but you must adjust the pins in `esphome/common/base.yaml` and the bay for the board in the generator. The ESP32-C3 SuperMini was chosen for its size, native USB-C and low heat.

### Can I use a different display?
Any ST7789 based 240 × 320 SPI display works with small changes. Different outer dimensions require new values for `LCD_W`, `LCD_H`, `GLASS_*`, `ACTIVE_*` and `LCD_HOLE_*` in the generator.

### Can it run on batteries?
Not in a useful way. The colour display needs constant power. For a battery device an e-paper display and deep sleep would be required, which is a different design.

### Wall plugs or flush wall box?
Both. The wall plate takes two M4 screws with 6 mm wall plugs, 60 mm apart, or the two horizontal screws of a German flush wall box. The slots give 3 mm play up and down. If your box only has vertical screw positions, use wall plugs.

### Browser installer or my own build?
Both are first class. The **browser installer** on the [project page](https://tobi136b.github.io/co2-wall-sensor/) flashes a ready firmware without any WiFi credentials inside. After flashing you enter your WiFi in the same browser window (or via the hotspot "CO2 Wall Sensor" that the device opens when it has no WiFi), Home Assistant discovers it, and new releases appear as firmware updates in Home Assistant. If you want to change the configuration, click "Adopt" in the ESPHome dashboard: it pulls the matching YAML from this repository. The **own build** with your `secrets.yaml` gives you API encryption and full control from the start.

### Does the device phone home?
No. The firmware only checks the release manifest on the project page for updates, and only if you look at the update entity or once per day. Measurements never leave your network.

### Which inserts and screws exactly?
Generic M2 × 3 heat-set inserts with 3.0 or 3.2 mm outer diameter (the common "M2 x 3 x 3" or "M2 x 3 x 3.2" packs) and M2 × 4 button head screws ISO 7380, 10 of each. Inserts with a different size work if you change `INSERT_HOLE_D` and `INSERT_HOLE_L`.

### Cable from below or from the back?
Both, with the same printed parts. To the back: a 90° USB-C adapter (plug to socket) in the ESP32-C3, the cable goes straight into the flush wall box; always use it on the desk stand. To the bottom: a straight cable through the window in the bottom. See [assembly](assembly.md#3-choose-the-cable-exit).

### My straight USB-C plug does not fit.
The window in the bottom takes plugs with an overmould of up to 12 × 7 mm. For bulkier plugs change `PLUG_W` and `PLUG_H` (the device gets deeper if `PLUG_H` grows) or lead the cable to the back with the 90° adapter.

### The picture on the display is upside down.
Switch on *Display upside down* in Home Assistant, the picture turns by 180° at once. The housing decides how the display sits: its connector is on the left, seen from the back, and the picture stands upright. The switch is only a fallback.

### My SCD41 board looks different.
Measure it and compare it with the known profiles. Only the small sensor carrier depends on the board, everything else stays the same. See [measure your sensor](measure-sensor.md).

### My ESP32-C3 SuperMini is a little different.
The holder is designed for boards from other batches. The board lies on a sled over its whole length, crush ribs in the side guides centre it, the guides take boards up to 1.2 mm thick, and a spring hook clicks behind its upper edge. Measured board: 18.2 × 22.71 × 0.74 mm, USB-C socket 9.0 mm wide, 3.5 mm high, 1.5 mm over the lower edge.

| Dimension | fits without a new print |
|-----------|--------------------------|
| Width | 18.0 to 18.6 mm |
| Thickness | up to 1.2 mm |
| Length | 22.0 to 22.8 mm (a shorter board has some play) |
| USB-C socket over the lower edge | 0.5 to 2.5 mm |

Outside these ranges change `C3_W`, `C3_H`, `C3_PCB` or `C3_USB_OUT` in the generator and print a new sensor carrier.

### How do I change a dimension?
Open the generated design in Fusion, go to *Modify > Change Parameters*, change the value and run the script again. It takes over all parameters of the open design, rebuilds every part and checks for interference. With `EXPORT = True` it also writes new STL and STEP files. See [design notes](design.md#parameters-in-fusion).

### Why are the drawing and images generated?
Because they then always match the model. Change a parameter, run the tools, commit. The CI regenerates them, checks that the print files belong to the current parameters and that all links in the documentation work.
