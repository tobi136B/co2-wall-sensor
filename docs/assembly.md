# Printing and assembly

**English** | [Deutsch](de/aufbau.md)

## 1. 3D printing

| Part | File | Orientation | Notes |
|------|------|-------------|-------|
| Housing | [`cad/stl/housing.stl`](../cad/stl/housing.stl) | front face down | The front lies directly on the bed (a textured PEI sheet looks great). No supports needed. |
| Back cover | [`cad/stl/back_cover.stl`](../cad/stl/back_cover.stl) | inside face down | Rail points up, no supports. |
| Wall plate | [`cad/stl/wall_plate.stl`](../cad/stl/wall_plate.stl) | wall side down | The dovetail slot prints without supports (45° overhang). |
| Desk stand | [`cad/stl/desk_stand.stl`](../cad/stl/desk_stand.stl) | on its side | Printed on its side the rail is strongest. |

**Recommended settings:** PETG, 0.2 mm layers, 3 walls, 20 % gyroid infill. PLA works too but may soften in summer behind a sunny window.

**Two colours:** housing in matte black or anthracite, wall plate in the colour of your light switches (usually pure white). The result looks like a switch insert in its frame.

## 2. Pre-assembly

1. **Heat-set inserts:** press 2 × M3 inserts into the two bosses at the bottom of the housing with a soldering iron (about 220 °C).
2. **Test the electronics on the desk first.** Wire everything as described in [wiring.md](wiring.md), flash the firmware and check the display before building it in.

## 3. Assembly

1. **Display:** place it glass first into the display bay. The PH2.0 connector points to the side with the connector recess. Fix it with 4 × M2 × 4 self-tapping plastic screws.
2. **SCD41:** into the sensor chamber at the front, sensor opening facing the vents. Fix it with double-sided foam tape.
   > The chamber is designed for a board of about 24 × 22 mm. For other sizes adjust `SCD_W/SCD_H/SCD_T` in the generator.
3. **Seal the cable notch:** route the SCD41 wires through the notch in the chamber floor and close the notch with a drop of hot glue. This stops warm air from the ESP bay entering the sensor chamber.
4. **ESP32-C3:** lay it on the ribs in the rear bay, USB-C pointing up towards the cable exit. The back cover presses it down with two pins.
5. **Cable:** plug in the right-angle USB-C cable and route it through the cable exit in the back cover.
6. **Back cover:** hook it in at the top with the two hooks, swing it closed and fix it with 2 × M3 × 6 countersunk screws.

## 4. Wall mounting on a flush wall box

1. **Bring power into the box:** either a flush mounted USB power supply (work on 230 V must be done by a qualified electrician) or a USB cable that runs inside the wall to a socket.
2. **Mount the wall plate** with the two box screws (60 mm spacing, horizontal). The slots compensate a slightly rotated box.
3. Route the USB cable through the cable passage and plug it into the device.
4. **Attach the device:** hold it in front of the plate, insert the rail into the hidden insertion window and **slide it 15 mm down**. Done.

To remove it, push it 15 mm up and pull it off.

## 5. Desk stand

Place the device on the rail from above and slide it down. The device leans back by 12°, a 5 mm air gap below keeps the vents free. The cable runs out through the notch at the back of the foot.

## 6. Commissioning

1. Copy `esphome/secrets.yaml.example` to `esphome/secrets.yaml` and fill it in.
2. Open the ESPHome Builder in Home Assistant and add `esphome/co2-wall-sensor.yaml` (English) or `esphome/co2-wall-sensor-de.yaml` (German) together with the `common` folder.
3. Flash via USB the first time, afterwards updates go over WiFi (OTA).
4. Home Assistant discovers the device. Confirm the integration.
5. **Calibration:** put the device next to an open window for 15 minutes, then press *Calibrate SCD41 (fresh air 420 ppm)* in Home Assistant. Automatic self calibration is enabled in addition.
6. **Temperature:** after 24 hours compare with a reference thermometer and adjust `temperature_offset` in the device file.
