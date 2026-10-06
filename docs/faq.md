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

### What is the hole in the bottom of the housing for?
It takes a heat-set insert for the optional lock tab. The tab is screwed to the housing and to the wall plate from below, so the device cannot simply be slid off the wall (office, school, children). Without the lock tab the hole stays empty; it is only visible from below. See [assembly](assembly.md#6-wall-mounting-on-the-flush-box).

### Which thresholds are sensible?
The defaults are 1000 ppm (yellow) and 1400 ppm (red). Values below 1000 ppm are generally considered harmless, above 2000 ppm ventilation is clearly needed. Both thresholds can be changed in Home Assistant at any time.

### The temperature reads too high.
Compare with a reference thermometer after 24 hours and adjust `temperature_offset` in the device file. Make sure the wire notch between ESP bay and sensor chamber is sealed.

### Can I use a different ESP32 board?
Yes. Any ESP32 supported by ESPHome works, but you must adjust the pins in `esphome/common/base.yaml` and the bay for the board in the generator. The ESP32-C3 SuperMini was chosen for its size, native USB-C and low heat.

### Can I use a different display?
Any ST7789 based 240 × 320 SPI display works with small changes. Different outer dimensions require new values for `LCD_W`, `LCD_H`, `GLASS_*`, `ACTIVE_*` and `LCD_HOLE_*` in the generator.

### Can it run on batteries?
Not in a useful way. The colour display needs constant power. For a battery device an e-paper display and deep sleep would be required, which is a different design.

### My wall box is mounted vertically.
The wall plate uses the two horizontal box screws. Most German flush wall boxes offer horizontal and vertical screw positions. If yours only has vertical ones, rotate `ScrewSlots` in the generator by 90°.

### Browser installer or my own build?
Both are first class. The **browser installer** on the [project page](https://tobi136b.github.io/co2-wall-sensor/) flashes a ready firmware without any WiFi credentials inside. After flashing you enter your WiFi in the same browser window (or via the hotspot "CO2 Wall Sensor" that the device opens when it has no WiFi), Home Assistant discovers it, and new releases appear as firmware updates in Home Assistant. If you want to change the configuration, click "Adopt" in the ESPHome dashboard: it pulls the matching YAML from this repository. The **own build** with your `secrets.yaml` gives you API encryption and full control from the start.

### Does the device phone home?
No. The firmware only checks the release manifest on the project page for updates, and only if you look at the update entity or once per day. Measurements never leave your network.

### Which inserts and screws exactly?
Generic M2 × 3 heat-set inserts with 3.2 mm outer diameter (the common "M2 x 3 x 3.2" packs) and M2 × 4 button head screws ISO 7380, 10 of each (12 with the optional lock tab). Inserts with a different outer diameter work if you change `INSERT_HOLE_D`.

### Cable from below or from the back?
Both. Print the two cable port modules and use the one you need: back with a right-angle plug for the flush wall box and the desk stand, bottom with a straight plug for a surface mounted cable. Swapping later takes four screws. See [assembly](assembly.md#4-choose-the-cable-exit).

### My straight USB-C plug does not fit.
The bottom port takes plugs with an overmould of up to 12 × 7 mm. For bulkier plugs change `PLUG_W` and `PLUG_H` (the device gets deeper if `PLUG_H` grows) or use the back port with a right-angle plug.

### My SCD41 board looks different.
Measure it and compare it with the known profiles. Only the small sensor carrier depends on the board, everything else stays the same. See [measure your sensor](measure-sensor.md).

### How do I change a dimension?
Open the generated design in Fusion, go to *Modify > Change Parameters*, change the value and run the script again. It takes over all parameters of the open design, rebuilds every part and checks for interference. With `EXPORT = True` it also writes new STL and STEP files. See [design notes](design.md#parameters-in-fusion).

### Why are the drawing and images generated?
Because they then always match the model. Change a parameter, run the tools, commit. The CI regenerates them, checks that the print files belong to the current parameters and that all links in the documentation work.
