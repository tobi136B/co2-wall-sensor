# FAQ

**English** | [Deutsch](de/faq.md)

### How accurate is the CO2 reading?
The SCD41 is specified for ±(50 ppm + 5 % of reading) between 400 and 5000 ppm. Automatic self calibration assumes the device sees fresh air (about 420 ppm) at least once a week, which is normal in ventilated rooms. If the room is never aired properly, disable `automatic_self_calibration` and use the calibration button instead.

### Which thresholds are sensible?
The defaults are 1000 ppm (yellow) and 1400 ppm (red). Values below 1000 ppm are generally considered harmless, above 2000 ppm ventilation is clearly needed. Both thresholds can be changed in Home Assistant at any time.

### The temperature reads too high.
Compare with a reference thermometer after 24 hours and adjust `temperature_offset` in the device file. Make sure the cable notch between ESP bay and sensor chamber is sealed.

### Can I use a different ESP32 board?
Yes. Any ESP32 supported by ESPHome works, but you must adjust the pins in `esphome/common/base.yaml` and the bay for the board in the generator. The ESP32-C3 SuperMini was chosen for its size, native USB-C and low heat.

### Can I use a different display?
Any ST7789 based 240 × 320 SPI display works with small changes. Different outer dimensions require new values for `LCD_W`, `LCD_H`, `GLASS_*`, `ACTIVE_*` and `LCD_HOLE_*` in the generator.

### Can it run on batteries?
Not in a useful way. The colour display needs constant power. For a battery device an e-paper display and deep sleep would be required, which is a different design.

### My wall box is mounted vertically.
The wall plate uses the two horizontal box screws. Most German flush wall boxes offer horizontal and vertical screw positions. If yours only has vertical ones, rotate `ScrewSlots` in the generator by 90°.

### Can I use the published firmware files directly?
Only for a quick hardware test. The release binaries are built by CI without real credentials: they open the hotspot "CO2 Wall Sensor Setup" (password `co2-sensor-setup`) where you can check display and sensor, and they show up in Home Assistant only with the CI key. Flash them with [ESPHome Web](https://web.esphome.io). For daily use always build the firmware yourself with your own `secrets.yaml`.

### Which inserts and screws exactly?
Generic M2 × 3 heat-set inserts with 3.2 mm outer diameter (the common "M2 x 3 x 3.2" packs) and M2 × 4 button head screws ISO 7380. Inserts with a different outer diameter work if you change `INSERT_HOLE_D` in the generator.

### Cable from below or from the back?
Both are prepared as knock-outs. Back with a right-angle plug for the flush wall box and the desk stand, bottom with a straight plug for a surface mounted cable. See [assembly](assembly.md#4-choose-the-cable-exit).

### Why are the drawing and images generated?
Because they then always match the model. Change a parameter, run the tools, commit. The CI checks that the tools still run.
