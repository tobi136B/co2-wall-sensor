# Printing and assembly

**English** | [Deutsch](de/aufbau.md)

![Exploded view](images/exploded_view.png)

## 1. 3D printing

| Part | File | Orientation | Notes |
|------|------|-------------|-------|
| Housing | [`cad/stl/housing.stl`](../cad/stl/housing.stl) | front face down | The front lies directly on the bed (a textured PEI sheet looks great). No supports needed. |
| Sensor carrier | [`cad/stl/sensor_carrier.stl`](../cad/stl/sensor_carrier.stl) | SCD41 side down | Small flat part, no supports. |
| Back cover | [`cad/stl/back_cover.stl`](../cad/stl/back_cover.stl) | inside face down | Rail points up, the knock-out membrane is bridged. No supports. |
| Wall plate | [`cad/stl/wall_plate.stl`](../cad/stl/wall_plate.stl) | wall side down | The dovetail slot prints without supports. |
| Desk stand | [`cad/stl/desk_stand.stl`](../cad/stl/desk_stand.stl) | on its side | Printed on its side the rail is strongest. |

**Recommended settings:** PETG, 0.2 mm layers, 3 walls, 20 % gyroid infill. PLA works too but may soften in summer behind a sunny window. Use a slicer with variable line width (Arachne, default in PrusaSlicer, OrcaSlicer and Bambu Studio) so the 0.6 mm knock-out membranes are printed.

**Two colours:** housing in matte black or anthracite, wall plate in the colour of your light switches (usually pure white). The result looks like a switch insert in its frame.

## 2. Fasteners: one screw type for everything

| Qty | Part | Where |
|----:|------|-------|
| 10 | Heat-set insert **M2 × 3**, outer diameter 3.2 mm (hole Ø 3.0 × 3.4 mm) | 4 display, 4 back cover, 2 sensor carrier |
| 10 | Button head screw **M2 × 4**, ISO 7380, hex socket 1.3 mm | same positions |

The only other screws are the two that come with your flush wall box.

## 3. Pre-assembly

1. **Press in all 10 inserts** from the open back of the housing with a soldering iron (about 200 to 220 °C, M2 tip if you have one). Let them sink in under their own weight and stop flush with the boss.
   * 4 on the display bosses around the display bay. The front skin behind them is only 1.1 mm thick, so work with low temperature and little pressure, otherwise the front face may show a mark.
   * 4 for the back cover: 2 in the bottom corners, 2 in the solid band above the display.
   * 2 for the sensor carrier on the short bosses in the chin.
2. **Test the electronics on the desk first.** Wire everything as described in [wiring.md](wiring.md), flash the firmware and check the display before building it in.

## 4. Choose the cable exit

The housing is prepared for both cable directions. Decide now, after printing:

| Exit | Plug | Use | What to break out |
|------|------|-----|-------------------|
| **Back** | right-angle USB-C (90°, "up/down angled") | wall plate with the cable coming out of the flush wall box, **and always on the desk stand** | knock-out in the back cover |
| **Bottom** | straight USB-C | surface mounted cable on the wall, or a power bank below the device | knock-out in the bottom wall of the housing |

Both knock-outs are 0.6 mm membranes, flush and invisible from outside. Cut along the edge from the inside with a craft knife, push the membrane out and deburr. Only break out the one you need, the other stays closed and dust tight.

![Interior with ESP32-C3 and USB-C plug pointing down](images/interior.png)

## 5. Assembly

1. **Display:** place it glass first into the display bay. Fix it with 4 × M2 × 4 into the inserts.
2. **SCD41:** stick the back of the board with a piece of double-sided foam tape between the two guides on the front side of the sensor carrier (the side facing the display). The sensor points to the front of the device, fresh air reaches it through the bottom and side vents.
   > The model uses a 20 × 20 × 8.1 mm placeholder. Measure your board and adjust `SCD_W/SCD_H/SCD_T` in the generator before printing.
3. **Sensor carrier:** route the SCD41 wires through the notch at its upper edge, put the carrier onto the ledges in the chin and fix it with 2 × M2 × 4. The carrier closes the sensor chamber against the warm electronics.
4. **Seal the cable notch** with a drop of hot glue. This stops warm air from the ESP bay entering the sensor chamber.
5. **ESP32-C3:** stick it with a strip of double-sided foam tape onto the two ribs on the back of the carrier, between the side guides, **USB-C socket pointing down**.
6. **Cable:** plug in the USB-C cable and lead it out through the knock-out you opened in section 4.
7. **Back cover:** put it into the seat and fix it with 4 × M2 × 4. The button heads sit in counterbores and stay below the surface, so the cover still slides onto the wall plate.

## 6. Wall mounting on a flush wall box

1. **Bring power into the box:** either a flush mounted USB power supply (work on 230 V must be done by a qualified electrician) or a USB cable that runs inside the wall to a socket.
2. **Mount the wall plate** with the two box screws (60 mm spacing, horizontal). The slots compensate a slightly rotated box.
3. Route the USB cable through the cable passage and plug it into the device (back exit).
4. **Attach the device:** hold it in front of the plate, insert the rail into the hidden insertion window and **slide it 15 mm down**. Done.

To remove it, push it 15 mm up and pull it off.

## 7. Desk stand

Use the back exit with a right-angle plug. Place the device on the rail from above and slide it down. The device leans back by 12°, a 5 mm air gap below keeps the vents free. The cable runs out through the notch at the back of the foot.

## 8. Commissioning

1. Copy `esphome/secrets.yaml.example` to `esphome/secrets.yaml` and fill it in.
2. Open the ESPHome Builder in Home Assistant and add `esphome/co2-wall-sensor.yaml` (English) or `esphome/co2-wall-sensor-de.yaml` (German) together with the `common` folder.
3. Flash via USB the first time, afterwards updates go over WiFi (OTA).
4. Home Assistant discovers the device. Confirm the integration.
5. **Calibration:** put the device next to an open window for 15 minutes, then press *Calibrate SCD41 (fresh air 420 ppm)* in Home Assistant. Automatic self calibration is enabled in addition.
6. **Temperature:** after 24 hours compare with a reference thermometer and adjust `temperature_offset` in the device file.
