"""
CO2 Wall Sensor: parametric enclosure generator for Autodesk Fusion
===================================================================

Creates a new Fusion design that contains every part as its own component:

    Housing        front housing with display window and isolated sensor chamber
    SensorCarrier  removable floor of the sensor chamber: SCD41 slides into rails on the
                   front and is held by a spring tongue, the ESP32-C3 sits between guides on
                   the back. One carrier per SCD41 board profile (SCD_BOARDS), all other
                   parts are the same for every board.
    BackCover      back cover with dovetail rail
    PortBack       cable port module, cable leaves to the back (right-angle plug)
    PortBottom     cable port module, cable leaves at the bottom (straight plug)
    WallPlate      82 x 82 plate that covers a German flush wall box
    LockTab        optional lock tab, screws the device to the wall plate
    DeskStand      desk stand using the same rail, device leans back by 12 degrees
    Dummy_*        reference bodies for display, SCD41, ESP32-C3 and USB-C plugs, shown
                   transparent: they are never exported and never printed

Run it in Fusion: Utilities > Scripts and Add-Ins > "+" > add this folder >
select generate_enclosure > Run.

Dimensions
----------
Every value of the PARAMETERS block becomes a Fusion user parameter
(Modify > Change Parameters). To change the enclosure, edit the values there
and run the script again: it reads the parameters of the open design and
rebuilds every part with them. The values below are the defaults.

Fastening
---------
Every screw connection uses the same M2 heat-set insert and the same M2 x 4
button head screw (ISO 7380). Nothing is glued. The cable port module is
clamped between housing and back cover, swap it to change the cable exit.

Coordinate system: front face at z = 0, wall side towards +z, +y points up.
"""
import hashlib
import json
import math
import os
import re

import adsk.core
import adsk.fusion

VERSION = '1.6'          # enclosure version, engraved into every part

# ===================== PARAMETERS =====================
# --- device ---
BODY = 69.8             # outer width and height of the device
WALL = 2.0              # wall thickness
LIP = 2.0               # front lip in front of the display glass
DEPTH = 24.0            # device depth without rail
COVER_T = 2.5           # back cover thickness
R_CORNER = 4.0          # outer corner radius
R_FRONT = 2.5           # soft front edge, ends in a 45 degree foot on the print bed
WINDOW_CHAMFER = 0.8    # chamfer around the display window
FIT = 0.3               # fit clearance per side for all sliding and plugged parts
TOP_BAND = 5.0          # solid band above the display bay, holds two cover inserts
# --- fasteners: one insert type, one screw type ---
INSERT_HOLE_D = 3.0     # hole for M2 x 3 heat-set insert (outer diameter 3.2)
INSERT_HOLE_L = 3.4     # hole depth (insert length 3.0 + 0.4)
INSERT_LEAD = 0.4       # entry chamfer, centres the insert while pressing
BOSS_D = 5.0            # boss around an insert
BOSS_FILLET = 0.6       # fillet at the root of the bosses
SCREW_CLEAR_D = 2.4     # clearance hole for M2
HEAD_D, HEAD_H = 4.2, 1.3   # counterbore for M2 ISO 7380 button head (head 3.5 x 1.1)
# --- display: Waveshare 2inch LCD Module ---
LCD_W, LCD_H, LCD_PCB = 58.0, 35.0, 1.6
GLASS_W, GLASS_H, GLASS_T = 48.2, 34.7, 2.5     # GLASS_T is an assumption, measure it
ACTIVE_W, ACTIVE_H = 40.8, 30.6
LCD_X = -2.1            # PCB offset so the active area is centred in the window
LCD_HOLE_X, LCD_HOLE_Y = 26.5, 15.0
LCD_BOSS_D = 4.6        # slightly smaller boss, sits right next to the glass
# --- chin: sensor chamber in front, ESP32-C3 behind ---
DIVIDER = 2.5           # wall between display bay and chin
FLOOR_Z, FLOOR_T = 12.0, 2.0    # sensor carrier (removable floor of the chamber)
RIB_H = 1.2             # ESP32-C3 sits this far above the carrier
# ESP32-C3 SuperMini, measured: board only, without the socket
C3_W, C3_H, C3_PCB = 18.2, 22.71, 0.74
C3_USB_OUT = 1.5        # the USB-C socket sticks out this far over the lower board edge
C3_USB_W, C3_USB_H = 9.0, 3.5   # USB-C socket: width, height above the board
C3_PARTS_H = 2.2        # tallest part on the board besides the socket (the two buttons)
C3_X = 13.0
# tolerances of the ESP32-C3 holder: boards of other batches fit without a new print
C3_PLAY = 0.3           # side play in the guides, taken up by crush ribs
C3_RIB = 0.4            # how far the crush ribs reach into the guide
C3_PCB_MAX = 1.2        # thickest board the guides take
BOOT_PLAY = 1.0         # the cable boot may sit this much higher or lower (socket and plug tolerances)
PLUG_SPACE = 12.5       # free space below the mouth of the USB-C socket for the plug
PLUG_W, PLUG_H = 12.0, 7.0      # overmould of a straight USB-C plug
BOOT_D = 7.0            # hole for the cable boot of a right-angle plug
# SCD41 board as mounted: W across the rails, L in the slide direction. Defaults: profile '14x22'.
# Offsets are seen from the front of the device: right and up are positive (right is -x in the model).
SCD_W, SCD_L, SCD_PCB = 21.75, 13.51, 1.53      # SCD41 breakout board
SCD_H = 6.3             # height of the SCD41 above the board
SCD_SENSOR_X, SCD_SENSOR_Y = -3.95, 0.0         # centre of the SCD41 from the board centre, seen from the front
SCD_PAD_X = 9.1         # solder pad column from the board centre, seen from the front (0: pads not on a rail)
SCD_LIP = 0.8           # rail lip in front of the board edge
SCD_STOP = 0.8          # end stop below the board (2 lines of a 0.4 mm nozzle)
# --- spring tongue: presses the SCD41 board against its end stop, takes up length tolerances ---
SPRING_X = -1.0         # x of the tongue centre
SPRING_W, SPRING_L = 4.0, 10.0  # width and free length of the tongue
SPRING_T = 1.2          # thickness of the tongue (the carrier is FLOOR_T thick)
SPRING_HOOK = 0.8       # height of the 45 degree hook in front of the tongue
SPRING_PRELOAD = 0.4    # the hook is pushed back this far by a board of nominal length
# --- cable port module ---
PORT_W = 16.0           # width of the module (outside)
PORT_STEP = 1.2         # the module is wider behind the outer skin, so it cannot fall out
PORT_TOP = 12.5         # height of the module in the back cover (from the inner bottom wall)
# --- dovetail rail ---
RAIL_FOOT, RAIL_HEAD, RAIL_H, RAIL_L = 12.0, 16.0, 3.0, 14.0
RAIL_Y0 = -10.0         # lower end of the rail
RAIL_TRAVEL = 15.0      # insert the device, then slide it 15 mm down
RAIL_LEAD = 0.6         # lead-in chamfer on rail and slot
# --- wall plate ---
PLATE = 82.0
PLATE_T = 7.0
BOX_RIM_D, BOX_RIM_T = 78.0, 1.5
BOX_SCREW_SPACING = 60.0
LOCK_X = -19.0          # position of the optional lock tab (its housing insert sits where the carrier has only its floor)
# --- desk stand ---
TILT = 12.0             # device leans back by this angle
STAND_GAP = 5.0         # air gap below the device, keeps the vents free
# --- labels ---
LABEL_H = 2.2           # text height of the embossed part labels
LABEL_DEPTH = 0.4
# --- printing ---
MIN_WALL = 0.8          # thinnest wall anywhere: 2 lines of a 0.4 mm nozzle
VENT_HOLE = 2.5         # vent mesh: diagonal of the diamond holes (45 degree edges print without support)
VENT_WEB = 1.0          # vent mesh: width of the webs between the holes

EXPORT = False          # True: write STL + STEP into ../../stl and ../../step
USE_DOC_PARAMS = True   # True: take over the user parameters of the open design (changes made in Fusion)

# Known SCD41 breakout boards. The export writes one sensor carrier per profile
# (cad/stl/sensor_carrier_<name>.stl), plus sensor_carrier_custom.stl if the SCD_* parameters
# of the design match none of them. Measure your board: see docs/measure-sensor.md.
SCD_BOARDS = {
    # 13.5 x 21.75 mm, pads GND VDD SCL SDA on a short edge, lies crosswise
    '14x22': dict(SCD_W=21.75, SCD_L=13.51, SCD_PCB=1.53, SCD_H=6.3, SCD_SENSOR_X=-3.95, SCD_SENSOR_Y=0.0,
                  SCD_PAD_X=9.1),
    # 15 x 20 mm, stands upright
    '15x20': dict(SCD_W=15.0, SCD_L=20.0, SCD_PCB=1.6, SCD_H=7.0, SCD_SENSOR_X=0.0, SCD_SENSOR_Y=-3.95,
                  SCD_PAD_X=0.0),
}


def diamond_centres(u0, v0, u1, v1):
    """Centres of a staggered diamond mesh that fits into the rectangle (webs VENT_WEB wide)."""
    h = VENT_HOLE / 2
    pitch = VENT_HOLE + VENT_WEB * math.sqrt(2)
    out, row, v = [], 0, v0 + h
    while v + h <= v1 + 1e-6:
        u = u0 + h + (pitch / 2 if row % 2 else 0)
        while u + h <= u1 + 1e-6:
            out.append((u, v))
            u += pitch
        v += pitch / 2
        row += 1
    # centre the pattern in the rectangle
    if out:
        du = ((u0 + u1) - (min(c[0] for c in out) + max(c[0] for c in out))) / 2
        dv = ((v0 + v1) - (min(c[1] for c in out) + max(c[1] for c in out))) / 2
        out = [(u + du, v + dv) for u, v in out]
    return out


def derive():
    """Values that follow from the parameters. Called again after loading Fusion parameters."""
    global CLEARANCE, RAIL_CLEARANCE, COVER_Z, XL, XR, Y_TOP_IN, BAY_W, BAY_H, BAY_X0, BAY_X1, BAY_Y1, BAY_Y0
    global LCD_Y, Y_DIV_LOW, Y_CHIN_LOW, Y_CHIN_MID, C3_MOUTH, C3_Y0, C3_Z0, PLUG_Z, SOCKET_TOP, B, COVER_SCREWS
    global CARRIER_SCREWS, LCD_HOLES, CABLE, PORT_X0, PORT_X1, PORT_Z0, PORT_Y1, BOOT_Y, SCD_Y0, SCD_ZT
    global LOCK_Z, LOCK_BOSS_Y1, LOCK_POINTS, SCD_TOP, HOOK_B, HOOK_C, HOOK_A, TONGUE_TIP, TONGUE_ROOT
    global VENT_BOTTOM, VENT_SIDE
    CLEARANCE = FIT
    RAIL_CLEARANCE = FIT
    COVER_Z = DEPTH - COVER_T
    XL, XR = -BODY / 2 + WALL, BODY / 2 - WALL
    Y_TOP_IN = BODY / 2 - WALL
    BAY_W, BAY_H = LCD_W + 2 * CLEARANCE, LCD_H + 2 * CLEARANCE
    BAY_X0, BAY_X1 = LCD_X - BAY_W / 2, LCD_X + BAY_W / 2
    BAY_Y1 = Y_TOP_IN - TOP_BAND
    BAY_Y0 = BAY_Y1 - BAY_H
    LCD_Y = (BAY_Y0 + BAY_Y1) / 2
    Y_DIV_LOW = BAY_Y0 - DIVIDER
    Y_CHIN_LOW = -BODY / 2 + WALL
    Y_CHIN_MID = (Y_CHIN_LOW + Y_DIV_LOW) / 2
    C3_MOUTH = Y_CHIN_LOW + PLUG_SPACE               # mouth of the USB-C socket, the plug ends here
    C3_Y0 = C3_MOUTH + C3_USB_OUT                    # lower edge of the ESP32-C3 board, it stands on the end stops
    C3_Z0 = FLOOR_Z + FLOOR_T + RIB_H                # underside of the ESP32-C3 PCB
    PLUG_Z = C3_Z0 + C3_PCB + C3_USB_H / 2           # centre of the USB-C socket
    SOCKET_TOP = C3_Z0 + C3_PCB + C3_USB_H
    B = 2.4                                          # boss centre distance from the inner walls
    COVER_SCREWS = [(XL + B, Y_CHIN_LOW + B), (XR - B, Y_CHIN_LOW + B),
                    (-20.0, Y_TOP_IN - TOP_BAND / 2), (20.0, Y_TOP_IN - TOP_BAND / 2)]
    CARRIER_SCREWS = [(XL + B, Y_DIV_LOW - B), (XR - B, Y_DIV_LOW - B)]
    LCD_HOLES = [(LCD_X + sx * LCD_HOLE_X, LCD_Y + sy * LCD_HOLE_Y) for sx in (-1, 1) for sy in (-1, 1)]
    CABLE = (C3_X - 7, C3_X + 7, Y_CHIN_LOW + 0.5, C3_MOUTH)      # cable passage in wall plate and stand
    PORT_X0, PORT_X1 = C3_X - PORT_W / 2, C3_X + PORT_W / 2
    PORT_Z0 = PLUG_Z - PLUG_H / 2 - 1.2              # lower end of the port opening in the bottom wall
    PORT_Y1 = Y_CHIN_LOW + PORT_TOP                  # upper end of the port opening in the back cover
    BOOT_Y = C3_MOUTH - 5.5                          # cable boot of the right-angle plug
    # SCD41: slides in from the top, stands on the end stop, the hook of the spring tongue presses on its top edge
    SCD_Y0 = Y_CHIN_LOW + 0.2 + SCD_STOP + 0.15      # lower edge of the SCD41 board
    SCD_TOP = SCD_Y0 + SCD_L                         # upper edge
    SCD_ZT = FLOOR_Z                                 # board lies against the carrier
    HOOK_B = SCD_TOP - SPRING_PRELOAD                # pressing face of the hook: from the carrier face (y = HOOK_B)
    HOOK_C = HOOK_B + SPRING_HOOK                    # ... at 45 degrees to the tip (y = HOOK_C)
    HOOK_A = HOOK_C + SPRING_HOOK                    # entry ramp back to the carrier face (y = HOOK_A)
    TONGUE_TIP = HOOK_A + 0.1                        # free end of the tongue (it grows upwards from its root
    TONGUE_ROOT = TONGUE_TIP - SPRING_L              # when the carrier is printed on its lower edge)
    # vent mesh, bottom (u = x, v = z) and sides (u = y, v = z): between front wall and carrier, clear of the bosses
    z0, z1 = WALL + MIN_WALL, FLOOR_Z - MIN_WALL
    xv = XR - B - BOSS_D / 2 - MIN_WALL
    VENT_BOTTOM = diamond_centres(-xv, z0, xv, z1)
    VENT_SIDE = diamond_centres(COVER_SCREWS[0][1] + BOSS_D / 2 + MIN_WALL, z0,
                                CARRIER_SCREWS[0][1] - BOSS_D / 2 - MIN_WALL, FLOOR_Z - 1.5 - MIN_WALL)
    LOCK_Z = COVER_Z - 4.0                           # height of the lock insert in the bottom wall
    LOCK_BOSS_Y1 = Y_CHIN_LOW + 3.0                  # inner face of the lock insert boss
    LOCK_POINTS = (LOCK_X - 3.0, LOCK_X + 3.0)       # x of the housing insert and of the wall plate insert


derive()
VI = adsk.core.ValueInput
ANGLE_PARAMS = {'TILT'}


# ----------------------------------------------------------------------------- Fusion user parameters
def parameter_specs():
    """(name, default, comment) for every number of the PARAMETERS block, read from this file."""
    text = open(os.path.abspath(__file__), encoding='utf-8').read()
    block = text[text.index('# ===================== PARAMETERS'):text.index('\nEXPORT =')]
    specs = []
    for line in block.splitlines():
        m = re.match(r'^([A-Z0-9_, ]+?)\s*=\s*([^#]+?)\s*(?:#\s*(.*))?$', line)
        if not m:
            continue
        names = [n.strip() for n in m.group(1).split(',')]
        for n in names:
            specs.append((n, globals()[n], (m.group(3) or '').strip()))
    return specs


def parameters_fingerprint():
    """sha256 over the parameter values (the same function lives in tools/check_repo.py)."""
    values = ';'.join(f'{n}={float(v):.6g}' for n, v, _c in parameter_specs())
    return hashlib.sha256(values.encode('utf-8')).hexdigest()


def load_user_parameters(design):
    """Take over the values of a previous run, so changes made in Fusion survive a rebuild."""
    if design is None or not USE_DOC_PARAMS:
        return 0
    if not any(o.component.name == 'WallPlate' for o in design.rootComponent.occurrences):
        return 0
    count = 0
    for name, _default, _c in parameter_specs():
        p = design.userParameters.itemByName(name)
        if p is None:
            continue
        globals()[name] = round(math.degrees(p.value) if name in ANGLE_PARAMS else p.value * 10.0, 6)
        count += 1
    derive()
    return count


def write_user_parameters(design):
    for name, _default, comment in parameter_specs():
        value = globals()[name]
        unit = 'deg' if name in ANGLE_PARAMS else 'mm'
        design.userParameters.add(name, VI.createByString(f'{value:g} {unit}'), unit, comment)


# ----------------------------------------------------------------------------- helpers
def cm(v):
    """Fusion works in centimetres internally."""
    return v / 10.0


def pt(x, y, z):
    return adsk.core.Point3D.create(cm(x), cm(y), cm(z))


def sketch_pt(sk, x, y, z):
    """Project a model point into the sketch plane (sketch z = 0)."""
    p = sk.modelToSketchSpace(pt(x, y, z))
    p.z = 0
    return p


def _offset_plane(comp, base, value, axis):
    # The normal direction of the base planes differs between versions: check and flip if needed.
    inp = comp.constructionPlanes.createInput()
    inp.setByOffset(base, VI.createByReal(cm(value)))
    pl = comp.constructionPlanes.add(inp)
    if abs(getattr(pl.geometry.origin, axis) - cm(value)) > 1e-6:
        pl.deleteMe()
        inp = comp.constructionPlanes.createInput()
        inp.setByOffset(base, VI.createByReal(-cm(value)))
        pl = comp.constructionPlanes.add(inp)
    pl.isLightBulbOn = False
    return pl


def plane_z(comp, z):
    return comp.xYConstructionPlane if abs(z) < 1e-9 else _offset_plane(comp, comp.xYConstructionPlane, z, 'z')


def plane_y(comp, y):
    return _offset_plane(comp, comp.xZConstructionPlane, y, 'y')


def plane_x(comp, x):
    return _offset_plane(comp, comp.yZConstructionPlane, x, 'x')


def rect_sketch(comp, plane, rects, name):
    sk = comp.sketches.add(plane)
    sk.name = name
    for a, b in rects:
        sk.sketchCurves.sketchLines.addTwoPointRectangle(sketch_pt(sk, *a), sketch_pt(sk, *b))
    return sk


def circle_sketch(comp, plane, circles, name):
    sk = comp.sketches.add(plane)
    sk.name = name
    for centre, dia in circles:
        sk.sketchCurves.sketchCircles.addByCenterRadius(sketch_pt(sk, *centre), cm(dia / 2))
    return sk


def poly_sketch(comp, plane, points, name):
    sk = comp.sketches.add(plane)
    sk.name = name
    lines = sk.sketchCurves.sketchLines
    p = [sketch_pt(sk, *q) for q in points]
    for i in range(len(p)):
        lines.addByTwoPoints(p[i], p[(i + 1) % len(p)])
    return sk


def rounded_rect_sketch(comp, z, half_w, half_h, r, name):
    """Rounded rectangle centred on the z axis in the plane z."""
    sk = comp.sketches.add(plane_z(comp, z))
    sk.name = name
    lines, arcs = sk.sketchCurves.sketchLines, sk.sketchCurves.sketchArcs
    k = r * (1 - math.sqrt(0.5))
    for sx, sy in ((1, 1), (-1, 1), (-1, -1), (1, -1)):
        cx, cy = sx * (half_w - r), sy * (half_h - r)
        arcs.addByThreePoints(sketch_pt(sk, cx + sx * r, cy, z),
                              sketch_pt(sk, sx * (half_w - k), sy * (half_h - k), z),
                              sketch_pt(sk, cx, cy + sy * r, z))
    w, h = half_w - r, half_h - r
    for a, b in (((half_w, -h), (half_w, h)), ((w, half_h), (-w, half_h)),
                 ((-half_w, h), (-half_w, -h)), ((-w, -half_h), (w, -half_h))):
        lines.addByTwoPoints(sketch_pt(sk, a[0], a[1], z), sketch_pt(sk, b[0], b[1], z))
    return sk


def _profiles(sk):
    oc = adsk.core.ObjectCollection.create()
    for p in sk.profiles:
        oc.add(p)
    return oc


def extrude(comp, sk, length, op, name, body=None):
    """Symmetric extrusion around the sketch plane."""
    inp = comp.features.extrudeFeatures.createInput(_profiles(sk), op)
    inp.setSymmetricExtent(VI.createByReal(cm(length)), True)
    if body is not None:
        inp.participantBodies = [body]
    f = comp.features.extrudeFeatures.add(inp)
    f.name = name
    if op == adsk.fusion.FeatureOperations.NewBodyFeatureOperation:
        for b in f.bodies:
            b.name = name
    return f


def box(comp, x0, y0, z0, x1, y1, z1, op, name, body=None):
    sk = rect_sketch(comp, plane_z(comp, (z0 + z1) / 2), [((x0, y0, 0), (x1, y1, 0))], name)
    return extrude(comp, sk, z1 - z0, op, name, body)


def cylinders(comp, centres, dia, z0, z1, op, name, body=None):
    sk = circle_sketch(comp, plane_z(comp, (z0 + z1) / 2), [((x, y, 0), dia) for x, y in centres], name)
    return extrude(comp, sk, z1 - z0, op, name, body)


def cylinders_y(comp, centres_xz, dia, y0, y1, op, name, body=None):
    """Cylinders along the y axis."""
    ym = (y0 + y1) / 2
    sk = circle_sketch(comp, plane_y(comp, ym), [((x, ym, z), dia) for x, z in centres_xz], name)
    return extrude(comp, sk, y1 - y0, op, name, body)


def prism_x(comp, points_yz, x0, x1, op, name, body=None):
    """Polygon in the YZ plane, extruded along x."""
    xm = (x0 + x1) / 2
    sk = poly_sketch(comp, plane_x(comp, xm), [(xm, y, z) for y, z in points_yz], name)
    return extrude(comp, sk, x1 - x0, op, name, body)


def prism_y(comp, points_xz, y0, y1, op, name, body=None):
    """Polygon in the XZ plane, extruded along y."""
    ym = (y0 + y1) / 2
    sk = poly_sketch(comp, plane_y(comp, ym), [(x, ym, z) for x, z in points_xz], name)
    return extrude(comp, sk, y1 - y0, op, name, body)


def dovetail(comp, z_foot, foot, head, height, y0, y1, op, name, body=None):
    """Trapezoid (narrow at the foot, wide at the head) extruded along y."""
    zh = z_foot + height
    pts = [(-foot / 2, z_foot), (foot / 2, z_foot), (head / 2, zh), (-head / 2, zh)]
    return prism_y(comp, pts, y0, y1, op, name, body)


def dovetail_slot(comp, body):
    """Dovetail slot with a hidden insertion window above it (shared by wall plate and stand)."""
    c = RAIL_CLEARANCE
    cut = adsk.fusion.FeatureOperations.CutFeatureOperation
    y0, y1 = RAIL_Y0 - c, RAIL_Y0 + RAIL_L + c
    dovetail(comp, DEPTH - 0.01, RAIL_FOOT + 2 * c, RAIL_HEAD + 2 * c, RAIL_H + c, y0, y1, cut, 'DovetailSlot', body)
    hw = RAIL_HEAD / 2 + c
    box(comp, -hw, y1 - 0.01, DEPTH - 0.01, hw, y1 + RAIL_TRAVEL, DEPTH + RAIL_H + c, cut, 'InsertionWindow', body)
    # lead-in: chamfer the edges where the rail enters the slot
    edges = [e for e in body.edges if _edge_in_plane(e, 'y', y1)
             and _edge_within(e, lambda p: abs(p.x) <= cm(hw) + 1e-6 and cm(DEPTH) - 1e-6 <= p.z
                              <= cm(DEPTH + RAIL_H + c) + 1e-6)]
    try_chamfer(comp, edges, RAIL_LEAD, 'SlotLeadIn')


def fillet(comp, edges, radius, name):
    oc = adsk.core.ObjectCollection.create()
    for e in edges:
        oc.add(e)
    if oc.count == 0:
        return None
    inp = comp.features.filletFeatures.createInput()
    inp.addConstantRadiusEdgeSet(oc, VI.createByReal(cm(radius)), True)
    f = comp.features.filletFeatures.add(inp)
    f.name = name
    return f


def chamfer(comp, edges, dist, name):
    oc = adsk.core.ObjectCollection.create()
    for e in edges:
        oc.add(e)
    if oc.count == 0:
        return None
    inp = comp.features.chamferFeatures.createInput2()
    inp.chamferEdgeSets.addEqualDistanceChamferEdgeSet(oc, VI.createByReal(cm(dist)), False)
    f = comp.features.chamferFeatures.add(inp)
    f.name = name
    return f


def try_chamfer(comp, edges, dist, name):
    """Cosmetic chamfer: skip it if the geometry does not allow it."""
    try:
        return chamfer(comp, edges, dist, name)
    except RuntimeError:
        print('note: chamfer', name, 'skipped')
        return None


def try_fillet(comp, edges, radius, name):
    try:
        return fillet(comp, edges, radius, name)
    except RuntimeError:
        print('note: fillet', name, 'skipped')
        return None


def _edge_points(e):
    return [e.startVertex.geometry, e.endVertex.geometry] if e.startVertex else [e.pointOnEdge]


def _edge_in_plane(e, axis, value):
    return all(abs(getattr(p, axis) - cm(value)) < 1e-5 for p in _edge_points(e) + [e.pointOnEdge])


def _edge_within(e, pred):
    return all(pred(p) for p in _edge_points(e) + [e.pointOnEdge])


def circular_edges(body, radius, centre_pred):
    out = []
    for e in body.edges:
        g = e.geometry
        if isinstance(g, (adsk.core.Circle3D, adsk.core.Arc3D)) and abs(g.radius - cm(radius)) < 1e-5:
            if centre_pred(g.center):
                out.append(e)
    return out


def z_edges(body, length, pred=lambda p: True):
    """Straight edges parallel to z with the given length."""
    out = []
    for e in body.edges:
        g = e.geometry
        if isinstance(g, adsk.core.Line3D):
            s, t = g.startPoint, g.endPoint
            if (abs(s.x - t.x) < 1e-6 and abs(s.y - t.y) < 1e-6
                    and abs(abs(s.z - t.z) - cm(length)) < 1e-5 and pred(s)):
                out.append(e)
    return out


def planar_face_at_z(body, z):
    return [f for f in body.faces if abs(f.pointOnFace.z - cm(z)) < 1e-6
            and isinstance(f.geometry, adsk.core.Plane)][0]


def new_component(root, name):
    occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    occ.component.name = name
    return occ.component


def combine(comp, target, tools, op, name, keep_tools=False):
    oc = adsk.core.ObjectCollection.create()
    for t in tools:
        oc.add(t)
    inp = comp.features.combineFeatures.createInput(target, oc)
    inp.operation = op
    inp.isKeepToolBodies = keep_tools
    f = comp.features.combineFeatures.add(inp)
    f.name = name
    return f


def bed_foot(comp, body, z_face, half_w, half_h, r_corner, r_edge, direction, name):
    """Replace the lowest part of a rounded edge that touches the print bed by a 45 degree foot.

    A fillet that starts tangent to the bed prints badly (almost horizontal overhang, elephant foot).
    The foot is tangent to the fillet, so the edge still looks round.
    """
    t = r_edge * (1 - math.sqrt(0.5))          # height where the fillet is at 45 degrees
    h = 2 * t                                    # height of the foot
    ops = adsk.fusion.FeatureOperations
    z_top = z_face + direction * h
    s0 = rounded_rect_sketch(comp, z_face, half_w - h, half_h - h, max(r_corner - h, 0.3), name + 'Bed')
    s1 = rounded_rect_sketch(comp, z_top, half_w, half_h, r_corner, name + 'Top')
    li = comp.features.loftFeatures.createInput(ops.NewBodyFeatureOperation)
    li.loftSections.add(s0.profiles.item(0))
    li.loftSections.add(s1.profiles.item(0))
    keep = comp.features.loftFeatures.add(li).bodies.item(0)
    z0, z1 = sorted((z_face - direction * 1.0, z_top))
    ring = box(comp, -half_w - 2, -half_h - 2, z0, half_w + 2, half_h + 2, z1, ops.NewBodyFeatureOperation,
               name + 'Ring').bodies.item(0)
    combine(comp, ring, [keep], ops.CutFeatureOperation, name + 'Cutter')
    combine(comp, body, [ring], ops.CutFeatureOperation, name)


def label(comp, body, z_face, x0, y0, x1, y1, text, flip=False, name='Label', height=None):
    """Engrave a text into a face that lies in the plane z_face and faces +z (or -z with flip)."""
    sk = comp.sketches.add(plane_z(comp, z_face))
    sk.name = name
    inp = sk.sketchTexts.createInput2(text, cm(height or LABEL_H))
    inp.setAsMultiLine(sketch_pt(sk, x0, y0, z_face), sketch_pt(sk, x1, y1, z_face),
                       adsk.core.HorizontalAlignments.CenterHorizontalAlignment,
                       adsk.core.VerticalAlignments.MiddleVerticalAlignment, 0)
    inp.isHorizontalFlip = flip
    txt = sk.sketchTexts.add(inp)
    ei = comp.features.extrudeFeatures.createInput(txt, adsk.fusion.FeatureOperations.CutFeatureOperation)
    ei.setSymmetricExtent(VI.createByReal(cm(2 * LABEL_DEPTH)), True)
    ei.participantBodies = [body]
    comp.features.extrudeFeatures.add(ei).name = name


# ----------------------------------------------------------------------------- fasteners
def insert_holes(comp, points, z_top, body):
    """Blind holes for M2 heat-set inserts, opening at z_top towards +z, with entry chamfer."""
    cut = adsk.fusion.FeatureOperations.CutFeatureOperation
    cylinders(comp, points, INSERT_HOLE_D, z_top - INSERT_HOLE_L, z_top + 0.1, cut, 'M2InsertHoles', body)
    lead_chamfer(comp, body, [(x, y, z_top) for x, y in points])


def lead_chamfer(comp, body, centres):
    def at(c):
        return any(abs(c.x - cm(x)) < 1e-4 and abs(c.y - cm(y)) < 1e-4 and abs(c.z - cm(z)) < 1e-4
                   for x, y, z in centres)
    try_chamfer(comp, circular_edges(body, INSERT_HOLE_D / 2, at), INSERT_LEAD, 'InsertLeadIn')


def boss_fillets(comp, body, points, dia, z_base, name):
    def at(c):
        return abs(c.z - cm(z_base)) < 1e-4 and any(abs(c.x - cm(x)) < 1e-4 and abs(c.y - cm(y)) < 1e-4
                                                      for x, y in points)
    try_fillet(comp, circular_edges(body, dia / 2, at), BOSS_FILLET, name)


def screw_holes(comp, points, z_face, body, counterbore=True):
    """Clearance hole through a part whose outer face is at z_face, optional counterbore for the head."""
    cut = adsk.fusion.FeatureOperations.CutFeatureOperation
    cylinders(comp, points, SCREW_CLEAR_D, z_face - 10, z_face + 0.1, cut, 'M2Clearance', body)
    if counterbore:
        cylinders(comp, points, HEAD_D, z_face - HEAD_H, z_face + 0.1, cut, 'M2HeadRecess', body)


def open_head_recesses(comp, points, z_face, outline, body):
    """Open a screw head recess towards the part edge where the wall beside it would be thinner than MIN_WALL.

    The recess becomes U-shaped; the part around it (housing wall) closes it from outside.
    outline = (x0, y0, x1, y1) of the part.
    """
    r = HEAD_D / 2
    x0e, y0e, x1e, y1e = outline
    for cx, cy in points:
        x0, y0, x1, y1 = cx - r, cy - r, cx + r, cy + r
        opened = False
        if x0 - x0e < MIN_WALL:
            x0, opened = x0e - 1, True
        if x1e - x1 < MIN_WALL:
            x1, opened = x1e + 1, True
        if y0 - y0e < MIN_WALL:
            y0, opened = y0e - 1, True
        if y1e - y1 < MIN_WALL:
            y1, opened = y1e + 1, True
        if opened:
            box(comp, x0, y0, z_face - HEAD_H, x1, y1, z_face + 0.1, adsk.fusion.FeatureOperations.CutFeatureOperation,
                'OpenHeadRecess', body)


def vent_mesh(comp, plane, centres, to3d, depth, body, name):
    """Diamond mesh in a wall, centres (u, v) from diamond_centres(), to3d(u, v) -> model point.

    v is the print direction (z of the housing, printed front face down): the 45 degree edges of the
    diamonds print without support.
    """
    h = VENT_HOLE / 2
    sk = comp.sketches.add(plane)
    sk.name = name
    lines = sk.sketchCurves.sketchLines
    for u, v in centres:
        pts = [sketch_pt(sk, *to3d(u + du, v + dv)) for du, dv in ((h, 0), (0, h), (-h, 0), (0, -h))]
        for i in range(4):
            lines.addByTwoPoints(pts[i], pts[(i + 1) % 4])
    extrude(comp, sk, depth, adsk.fusion.FeatureOperations.CutFeatureOperation, name, body)


# ----------------------------------------------------------------------------- parts
def build_housing(root, ops):
    NEW, CUT, JOIN = ops
    comp = new_component(root, 'Housing')
    body = box(comp, -BODY / 2, -BODY / 2, 0, BODY / 2, BODY / 2, DEPTH, NEW, 'BaseBody').bodies.item(0)
    body.name = 'Housing'
    fillet(comp, z_edges(body, DEPTH), R_CORNER, 'CornerRadius')
    fillet(comp, list(planar_face_at_z(body, 0).edges), R_FRONT, 'SoftFrontEdge')
    bed_foot(comp, body, 0, BODY / 2, BODY / 2, R_CORNER, R_FRONT, 1, 'FrontBedFoot')
    box(comp, XL, Y_CHIN_LOW, COVER_Z, XR, Y_TOP_IN, DEPTH + 1, CUT, 'CoverSeat')

    # display bay and window
    box(comp, BAY_X0, BAY_Y0, LIP, BAY_X1, BAY_Y1, COVER_Z + 1, CUT, 'DisplayBay')
    ww, wh = ACTIVE_W + 1.0, ACTIVE_H + 1.0
    box(comp, -ww / 2, LCD_Y - wh / 2, -1, ww / 2, LCD_Y + wh / 2, LIP + 0.5, CUT, 'DisplayWindow')
    fillet(comp, z_edges(body, LIP, lambda p: abs(abs(p.x) - cm(ww / 2)) < 1e-5), 1.0, 'WindowCorners')
    front = planar_face_at_z(body, 0)
    chamfer(comp, [e for lp in front.loops if not lp.isOuter for e in lp.edges], WINDOW_CHAMFER, 'WindowChamfer')
    # display: 4 bosses with M2 inserts at the PCB mounting holes
    cylinders(comp, LCD_HOLES, LCD_BOSS_D, LIP, LIP + GLASS_T, JOIN, 'LcdBosses', body)
    insert_holes(comp, LCD_HOLES, LIP + GLASS_T, body)

    # chin: open sensor chamber in front (closed later by the SensorCarrier), ESP bay behind
    box(comp, XL, Y_CHIN_LOW, WALL, XR, Y_DIV_LOW, COVER_Z + 1, CUT, 'Chin')
    box(comp, C3_X - 10, Y_DIV_LOW - 0.5, FLOOR_Z + FLOOR_T, C3_X + 10, BAY_Y0 + 0.5, COVER_Z + 1, CUT,
        'EspPassage')
    # bosses: 2 full height (cover screws at the bottom), 2 up to the carrier (carrier screws)
    cylinders(comp, COVER_SCREWS[:2], BOSS_D, WALL, COVER_Z, JOIN, 'CoverBossesBottom', body)
    cylinders(comp, CARRIER_SCREWS, BOSS_D, WALL, FLOOR_Z, JOIN, 'CarrierBosses', body)
    boss_fillets(comp, body, COVER_SCREWS[:2] + CARRIER_SCREWS, BOSS_D, WALL, 'BossRootFillets')
    insert_holes(comp, COVER_SCREWS, COVER_Z, body)
    insert_holes(comp, CARRIER_SCREWS, FLOOR_Z, body)
    # ledges along the side walls carry the sensor carrier and seal the chamber
    for x0, x1 in ((XL, XL + 1.2), (XR - 1.2, XR)):
        box(comp, x0, Y_CHIN_LOW, FLOOR_Z - 1.5, x1, Y_DIV_LOW, FLOOR_Z, JOIN, 'CarrierLedge', body)

    # vents: diamond mesh in the bottom and the sides of the sensor chamber only, the front stays closed
    yb = -BODY / 2 + WALL / 2
    vent_mesh(comp, plane_y(comp, yb), VENT_BOTTOM, lambda u, v: (u, yb, v), WALL + 1, body, 'BottomVents')
    for xp in (-BODY / 2 + WALL / 2, BODY / 2 - WALL / 2):
        vent_mesh(comp, plane_x(comp, xp), VENT_SIDE, lambda u, v, xp=xp: (xp, u, v), WALL + 1, body, 'SideVents')

    # cable port: stepped opening in the bottom wall, open towards the back, the port module fills it
    c = FIT / 2
    y_step = -BODY / 2 + WALL / 2
    box(comp, PORT_X0 - c, -BODY / 2 - 1, PORT_Z0 - c, PORT_X1 + c, Y_CHIN_LOW + 0.01, DEPTH + 1, CUT, 'PortOpening',
        body)
    box(comp, PORT_X0 - PORT_STEP - c, y_step - c, PORT_Z0 - c, PORT_X1 + PORT_STEP + c, Y_CHIN_LOW + 0.01, DEPTH + 1,
        CUT, 'PortStep', body)

    # optional lock: insert in a boss behind the bottom wall, screw comes from the lock tab below.
    # The boss is a block down to the floor level: the carrier has a matching notch, so it can be lifted
    # straight out of the back past the boss (tools/assembly_check.py tests every assembly path).
    lx = LOCK_POINTS[0]
    box(comp, lx - BOSS_D / 2, Y_CHIN_LOW - 0.01, FLOOR_Z, lx + BOSS_D / 2, LOCK_BOSS_Y1, LOCK_Z + BOSS_D / 2, JOIN,
        'LockBoss', body)
    cut_y = adsk.fusion.FeatureOperations.CutFeatureOperation
    cylinders_y(comp, [(lx, LOCK_Z)], INSERT_HOLE_D, -BODY / 2 - 0.1, -BODY / 2 + INSERT_HOLE_L, cut_y,
                'LockInsertHole', body)
    try_chamfer(comp, circular_edges(body, INSERT_HOLE_D / 2,
                                     lambda p: abs(p.y + cm(BODY / 2)) < 1e-4 and abs(p.x - cm(lx)) < 1e-4),
                INSERT_LEAD, 'LockLeadIn')

    label(comp, body, COVER_Z, -17, BAY_Y1 + 0.6, 17, Y_TOP_IN - 0.6, f'CO2 WALL SENSOR v{VERSION}', name='Label',
          height=1.8)
    return comp


def build_sensor_carrier(root, ops, name='SensorCarrier', profile=None):
    """Removable floor of the sensor chamber. SCD41 slides into rails on the front, ESP32-C3 on the back.

    The SCD41 board slides in from the top until it stands on the end stop. A tongue in the carrier carries
    a 45 degree hook that springs over the upper board edge and presses the board onto the end stop, so the
    board sits without play even if it is a few tenths longer or shorter than nominal. Printed on its lower
    edge, the tongue grows upwards from its root and the rails become vertical channels.
    """
    NEW, CUT, JOIN = ops
    comp = new_component(root, name)
    s = 0.2
    y_lo, y_hi = Y_CHIN_LOW + s, Y_DIV_LOW - s
    body = box(comp, XL + s, y_lo, FLOOR_Z, XR - s, y_hi, FLOOR_Z + FLOOR_T, NEW, 'Carrier').bodies.item(0)
    body.name = name
    # notches around the two full-height cover bosses
    r = BOSS_D / 2 + 0.3 + BOSS_FILLET
    for x, y in COVER_SCREWS[:2]:
        box(comp, x - r, y - r - 2, FLOOR_Z - 2, x + r, y + r, FLOOR_Z + FLOOR_T + 1, CUT, 'BossNotch', body)
    screw_holes(comp, CARRIER_SCREWS, FLOOR_Z + FLOOR_T, body, counterbore=False)

    # SCD41: two rails with a groove for the board edges, open at the top, end stop at the bottom
    zb = SCD_ZT - SCD_PCB
    g = 0.15                                      # play of the board in the groove
    z_lip = zb - g - SCD_LIP
    yc = SCD_Y0 + SCD_L / 2
    for sx in (-1, 1):
        x_in, x_edge, x_out = SCD_W / 2 - SCD_LIP, SCD_W / 2 + g, SCD_W / 2 + g + 1.2
        pts = [(sx * x_in, z_lip), (sx * x_out, z_lip), (sx * x_out, FLOOR_Z), (sx * x_edge, FLOOR_Z),
               (sx * x_edge, zb - g), (sx * x_in, zb - g)]
        prism_y(comp, pts, y_lo, y_hi, JOIN, 'ScdRail', body)
        box(comp, sx * x_in, y_lo, z_lip, sx * x_out, SCD_Y0 - g, FLOOR_Z, JOIN, 'ScdEndStop', body)
    if abs(SCD_PAD_X) > 1e-6:
        # pads on a rail side: lip open in front of the pads, relief behind them for the solder joints
        pad_x = -SCD_PAD_X                        # seen from the front, right is -x
        sx = 1 if pad_x > 0 else -1
        x0, x1 = sorted((sx * (SCD_W / 2 - SCD_LIP - 0.1), sx * (SCD_W / 2 + g)))
        box(comp, x0, yc - 4.8, z_lip - 0.1, x1, yc + 4.8, zb - g + 0.01, CUT, 'ScdPadWindow', body)
        box(comp, pad_x - 1.2, y_lo - 0.1, FLOOR_Z - 0.01, pad_x + 1.2, SCD_TOP + 1.0, FLOOR_Z + 0.6, CUT,
            'ScdPadRelief', body)
    # spring tongue: U-shaped slot, thinned from the back so it bends back into its own pocket
    hw = SPRING_W / 2
    for x0, x1 in ((SPRING_X - hw - 0.6, SPRING_X - hw), (SPRING_X + hw, SPRING_X + hw + 0.6)):
        box(comp, x0, TONGUE_ROOT, FLOOR_Z - 1, x1, TONGUE_TIP + 0.6, FLOOR_Z + FLOOR_T + 1, CUT, 'TongueSlot', body)
    box(comp, SPRING_X - hw - 0.6, TONGUE_TIP, FLOOR_Z - 1, SPRING_X + hw + 0.6, TONGUE_TIP + 0.6,
        FLOOR_Z + FLOOR_T + 1, CUT, 'TongueSlot', body)
    box(comp, SPRING_X - hw, TONGUE_ROOT + 1.0, FLOOR_Z + SPRING_T, SPRING_X + hw, TONGUE_TIP + 0.1,
        FLOOR_Z + FLOOR_T + 1, CUT, 'TongueThinning', body)
    hook = [(HOOK_B, FLOOR_Z + 0.01), (HOOK_C, FLOOR_Z - SPRING_HOOK), (HOOK_A, FLOOR_Z + 0.01)]
    prism_x(comp, hook, SPRING_X - hw, SPRING_X + hw, JOIN, 'TongueHook', body)
    # notch for the boss of the lock insert in the housing, so the carrier lifts straight out of the back
    lx, r = LOCK_POINTS[0], BOSS_D / 2 + CLEARANCE
    box(comp, lx - r, y_lo - 0.1, FLOOR_Z - 0.5, lx + r, LOCK_BOSS_Y1 + CLEARANCE, FLOOR_Z + FLOOR_T + 0.5, CUT,
        'LockBossNotch', body)
    # cable notch for the SCD41 wires (seal with a drop of hot glue)
    box(comp, -SCD_W / 2 - 6, y_hi - 4, FLOOR_Z - 0.5, -SCD_W / 2 - 2, y_hi + 0.1, FLOOR_Z + FLOOR_T + 0.5,
        CUT, 'ScdCableNotch', body)

    # ESP32-C3: support ribs, side guides, end stops below the board (the cable pulls downwards).
    # Tolerant to other batches: crush ribs centre the board in guides with play, the lips take boards up
    # to C3_PCB_MAX thick, and the upper end is open, so the board length does not matter.
    top = FLOOR_Z + FLOOR_T
    for x in (C3_X - 6, C3_X + 6):
        box(comp, x - 0.75, C3_Y0, top, x + 0.75, y_hi, C3_Z0, JOIN, 'C3Rib', body)
    gx, wall = C3_W / 2 + C3_PLAY, 1.15             # inner face of the side guides, their thickness
    z_guide = C3_Z0 + C3_PCB_MAX + 0.5
    for x0, x1 in ((C3_X - gx - wall, C3_X - gx), (C3_X + gx, C3_X + gx + wall)):
        box(comp, x0, C3_Y0 - 1.2, top, x1, y_hi, z_guide, JOIN, 'C3SideGuide', body)
    # crush ribs: half cylinders reaching C3_RIB into the guide, their round flanks lead the board in
    r = 0.6
    ribs = [(C3_X + sx * (gx - C3_RIB + r), y) for sx in (-1, 1) for y in (C3_Y0 + 4.0, y_hi - 3.0)]
    cylinders(comp, ribs, 2 * r, top, z_guide, JOIN, 'C3CrushRib', body)
    for x0, x1 in ((C3_X - gx, C3_X - C3_W / 2 + 1.5), (C3_X + C3_W / 2 - 1.5, C3_X + gx)):
        box(comp, x0, C3_Y0 - 1.2, top, x1, C3_Y0 - 0.05, C3_Z0 + C3_PCB, JOIN, 'C3EndStop', body)
    # short groove at the lower end (no solder pads there): floor below and lip above the board edge
    z_lip = C3_Z0 + C3_PCB_MAX + 0.1
    for sx in (-1, 1):
        xa, xb = sorted((C3_X + sx * (C3_W / 2 - 0.5), C3_X + sx * gx))
        box(comp, xa, C3_Y0 - 0.05, top, xb, C3_Y0 + 1.2, C3_Z0, JOIN, 'C3GrooveFloor', body)
        la, lb = sorted((C3_X + sx * (C3_W / 2 - 0.6), C3_X + sx * (gx + wall)))   # grows out of the guide
        box(comp, la, C3_Y0 - 0.05, z_lip, lb, C3_Y0 + 1.2, z_lip + MIN_WALL + 0.1, JOIN, 'C3GrooveLip', body)

    label(comp, body, top, XL + 4, Y_CHIN_LOW + 4, SPRING_X - hw - 2.0, y_hi - 4,
          f'CARRIER v{VERSION}\nSCD {profile or "custom"}\nPRINT: EDGE DOWN', name='Label', height=1.5)
    return comp


def build_back_cover(root, ops):
    NEW, CUT, JOIN = ops
    comp = new_component(root, 'BackCover')
    s = 0.2
    body = box(comp, XL + s, Y_CHIN_LOW + s, COVER_Z, XR - s, Y_TOP_IN - s, DEPTH, NEW, 'Cover').bodies.item(0)
    body.name = 'BackCover'
    screw_holes(comp, COVER_SCREWS, DEPTH, body)
    open_head_recesses(comp, COVER_SCREWS, DEPTH, (XL + s, Y_CHIN_LOW + s, XR - s, Y_TOP_IN - s), body)
    # notch for the cable port module
    c = FIT / 2
    box(comp, PORT_X0 - c, Y_CHIN_LOW - 1, COVER_Z - 1, PORT_X1 + c, PORT_Y1 + c, DEPTH + 1, CUT, 'PortNotch', body)
    dovetail(comp, DEPTH, RAIL_FOOT, RAIL_HEAD, RAIL_H, RAIL_Y0, RAIL_Y0 + RAIL_L, JOIN, 'Rail', body)
    edges = [e for e in body.edges if _edge_in_plane(e, 'y', RAIL_Y0)
             and _edge_within(e, lambda p: p.z > cm(DEPTH) + 1e-4)]
    try_chamfer(comp, edges, RAIL_LEAD, 'RailLeadIn')
    label(comp, body, COVER_Z, -28, -6, 0, 6, f'BACK COVER v{VERSION}\nTHIS FACE DOWN', flip=True, name='Label')
    return comp


def build_port(root, ops, variant):
    """Cable port module, clamped between housing and back cover. Print it with the back face down.

    It fills the opening at the lower back edge. Variant 'back': the cable boot of a right-angle plug leaves
    through the back, the plug body is caught behind the module (strain relief). Variant 'bottom': the
    overmould of a straight plug leaves through the bottom and is held by a snug fit.
    """
    NEW, CUT, JOIN = ops
    name = 'PortBack' if variant == 'back' else 'PortBottom'
    comp = new_component(root, name)
    x0, x1 = PORT_X0, PORT_X1
    y_step = -BODY / 2 + WALL / 2
    # L-shaped body: stepped tongue in the bottom wall, tongue in the back cover
    body = box(comp, x0, -BODY / 2, PORT_Z0, x1, Y_CHIN_LOW, DEPTH, NEW, 'BottomTongue').bodies.item(0)
    body.name = name
    box(comp, x0 - PORT_STEP, y_step, PORT_Z0, x1 + PORT_STEP, Y_CHIN_LOW, DEPTH, JOIN, 'Step', body)
    box(comp, x0, Y_CHIN_LOW - 0.01, COVER_Z, x1, PORT_Y1, DEPTH, JOIN, 'BackTongue', body)
    # lip under the back cover: the module cannot leave towards the back
    box(comp, x0, PORT_Y1 - 0.5, COVER_Z - 0.8, x1, PORT_Y1 + 1.0, COVER_Z, JOIN, 'CoverLip', body)
    if variant == 'back':
        # boot hole, open to the +x side so the cable can be laid in (the back cover closes it)
        # oblong by BOOT_PLAY up and down: plugs and sockets of other makes put the boot a little higher or lower
        ends = [(C3_X, BOOT_Y - BOOT_PLAY), (C3_X, BOOT_Y + BOOT_PLAY)]
        cylinders(comp, ends, BOOT_D, COVER_Z - 1, DEPTH + 1, CUT, 'BootHole', body)
        box(comp, C3_X - BOOT_D / 2, BOOT_Y - BOOT_PLAY, COVER_Z - 1, C3_X + BOOT_D / 2, BOOT_Y + BOOT_PLAY, DEPTH + 1,
            CUT, 'BootHoleMiddle', body)
        box(comp, C3_X, BOOT_Y - BOOT_D / 2 - BOOT_PLAY, COVER_Z - 1, x1 + 1, BOOT_Y + BOOT_D / 2 + BOOT_PLAY,
            DEPTH + 1, CUT, 'BootSlot', body)
    else:
        g = 0.1
        box(comp, C3_X - PLUG_W / 2 - g, -BODY / 2 - 1, PLUG_Z - PLUG_H / 2 - g, C3_X + PLUG_W / 2 + g,
            Y_CHIN_LOW + 1, PLUG_Z + PLUG_H / 2 + g, CUT, 'PlugHole', body)
    return comp


def boot_travel(comp, z1, body):
    """Slot for the boot of the right-angle plug: it sticks out of the back and travels the 15 mm of the rail
    while the device is slid on, so the cable passage must be that much longer upwards (plus BOOT_PLAY)."""
    r = (BOOT_D - 0.6) / 2 + 0.5
    y0, y1 = BOOT_Y - r - BOOT_PLAY, BOOT_Y + r + BOOT_PLAY + RAIL_TRAVEL + 0.5
    cut = adsk.fusion.FeatureOperations.CutFeatureOperation
    box(comp, C3_X - r, y0, DEPTH - 1, C3_X + r, y1, z1, cut, 'BootTravel', body)


def build_wall_plate(root, ops, cable):
    NEW, CUT, JOIN = ops
    comp = new_component(root, 'WallPlate')
    body = box(comp, -PLATE / 2, -PLATE / 2, DEPTH, PLATE / 2, PLATE / 2, DEPTH + PLATE_T, NEW, 'Plate').bodies.item(0)
    body.name = 'WallPlate'
    rk = R_CORNER + (PLATE - BODY) / 2
    fillet(comp, z_edges(body, PLATE_T), rk, 'ConcentricCorners')
    fillet(comp, list(planar_face_at_z(body, DEPTH).edges), 2.0, 'FrontEdge')
    bed_foot(comp, body, DEPTH, PLATE / 2, PLATE / 2, rk, 2.0, 1, 'FrontBedFoot')
    z_wall = DEPTH + PLATE_T
    cylinders(comp, [(0, 0)], BOX_RIM_D, z_wall - BOX_RIM_T, z_wall + 1, CUT, 'BoxRimRecess', body)
    dovetail_slot(comp, body)
    box(comp, cable[0], cable[2] - 1, DEPTH - 1, cable[1], cable[3] + 1, z_wall + 1, CUT, 'CablePassage', body)
    boot_travel(comp, z_wall + 1, body)
    a = BOX_SCREW_SPACING / 2
    slots = [((-a - 2, -1.75, 0), (-a + 2, 1.75, 0)), ((a - 2, -1.75, 0), (a + 2, 1.75, 0))]
    extrude(comp, rect_sketch(comp, plane_z(comp, DEPTH + PLATE_T / 2), slots, 'ScrewSlots'), PLATE_T + 1, CUT,
            'ScrewSlots', body)
    heads = [((-a - 3.3, -3.3, 0), (-a + 3.3, 3.3, 0)), ((a - 3.3, -3.3, 0), (a + 3.3, 3.3, 0))]
    extrude(comp, rect_sketch(comp, plane_z(comp, DEPTH + 1.0), heads, 'ScrewHeadRecess'), 3.0, CUT,
            'ScrewHeadRecess', body)
    # insert for the optional lock tab, in the front face below the device
    lock_y = _lock_plate_y()
    cylinders(comp, [(LOCK_POINTS[1], lock_y)], INSERT_HOLE_D, DEPTH - 0.1, DEPTH + INSERT_HOLE_L, CUT, 'LockInsertHole',
              body)
    try_chamfer(comp, circular_edges(body, INSERT_HOLE_D / 2,
                                     lambda p: abs(p.z - cm(DEPTH)) < 1e-4 and abs(p.y - cm(lock_y)) < 1e-4),
                INSERT_LEAD, 'LockLeadIn')
    label(comp, body, z_wall - BOX_RIM_T, -20, 21, 20, 29, f'WALL PLATE v{VERSION}\nPRINT: FRONT FACE DOWN',
          name='Label')
    return comp


def _lock_plate_y():
    return -PLATE / 2 + 2.0 + INSERT_HOLE_D / 2 + 0.2


def build_lock_tab(root, ops):
    """Optional lock tab below the device: one screw into the housing, one into the wall plate."""
    NEW, CUT, JOIN = ops
    comp = new_component(root, 'LockTab')
    y_top = -BODY / 2 - 0.2
    z_front = LOCK_Z - 4.0
    body = box(comp, LOCK_X - 6, -PLATE / 2, z_front, LOCK_X + 6, y_top, DEPTH, NEW, 'Tab').bodies.item(0)
    body.name = 'LockTab'
    fillet(comp, [e for e in body.edges if _edge_in_plane(e, 'y', -PLATE / 2) and _edge_in_plane(e, 'z', z_front)],
           1.5, 'FrontEdge')
    # screw 1 upwards into the housing
    lx = LOCK_POINTS[0]
    cylinders_y(comp, [(lx, LOCK_Z)], SCREW_CLEAR_D, -PLATE / 2 - 1, y_top + 1, CUT, 'M2Clearance', body)
    cylinders_y(comp, [(lx, LOCK_Z)], HEAD_D, -PLATE / 2 - 1, y_top - 1.3, CUT, 'M2HeadRecess', body)
    # screw 2 backwards into the wall plate
    py = _lock_plate_y()
    cylinders(comp, [(LOCK_POINTS[1], py)], SCREW_CLEAR_D, z_front - 1, DEPTH + 1, CUT, 'M2Clearance', body)
    cylinders(comp, [(LOCK_POINTS[1], py)], HEAD_D, z_front - 1, DEPTH - 1.3, CUT, 'M2HeadRecess', body)
    if y_top - (py + HEAD_D / 2) < MIN_WALL:   # open the recess towards the top instead of leaving a thin skin
        box(comp, LOCK_POINTS[1] - HEAD_D / 2, py, z_front - 1, LOCK_POINTS[1] + HEAD_D / 2, y_top + 1, DEPTH - 1.3, CUT,
            'OpenHeadRecess', body)
    return comp


def build_desk_stand(root, ops, cable):
    NEW, CUT, JOIN = ops
    comp = new_component(root, 'DeskStand')
    t = math.tan(math.radians(TILT))
    z_front, z_back = -2.0, DEPTH + 24.0
    # In device coordinates the table plane rises towards the back, so the device leans back.
    y_foot = -BODY / 2 - STAND_GAP - t * (DEPTH - z_front)

    def y_table(z):
        return y_foot + t * (z - z_front)

    body = prism_x(comp, [(y_table(z_front), z_front), (y_table(z_back), z_back), (y_table(z_back) - 4, z_back),
                          (y_table(z_front) - 4, z_front)], -BODY / 2 + 4, BODY / 2 - 4, NEW, 'Foot').bodies.item(0)
    body.name = 'DeskStand'
    y_top = RAIL_Y0 + RAIL_L + RAIL_TRAVEL + 4
    prism_x(comp, [(y_table(DEPTH) - 2, DEPTH), (y_top, DEPTH), (y_top, DEPTH + 7), (y_table(DEPTH + 7) - 2, DEPTH + 7)],
            -14, 14, JOIN, 'Spine', body)
    prism_x(comp, [(y_table(DEPTH + 7) - 1, DEPTH + 7), (y_top - 12, DEPTH + 7), (y_table(DEPTH + 24) - 1, DEPTH + 24)],
            -1.5, 1.5, JOIN, 'SupportRib', body)
    dovetail_slot(comp, body)
    box(comp, cable[0], cable[2] - 1, DEPTH - 1, cable[1], cable[3] + 1, DEPTH + 8, CUT, 'CablePassage', body)
    boot_travel(comp, DEPTH + 8, body)
    prism_x(comp, [(y_table(z_back - 8) + 1, z_back - 8), (y_table(z_back) + 1, z_back + 1),
                   (y_table(z_back) - 5, z_back + 1), (y_table(z_back - 8) - 5, z_back - 8)], -4, 4, CUT,
            'CableNotch', body)
    try:
        edges = [e for e in body.edges if isinstance(e.geometry, adsk.core.Line3D)
                 and abs(e.length - cm(BODY - 8)) < 1e-4]
        fillet(comp, edges, 1.5, 'FootEdges')
    except RuntimeError:
        pass  # cosmetic only
    return comp


def build_dummies(root, ops):
    NEW = ops[0]
    lcd = new_component(root, 'Dummy_LCD_2inch')
    box(lcd, LCD_X - GLASS_W / 2 + 0.1, LCD_Y - GLASS_H / 2, LIP, LCD_X + GLASS_W / 2 + 0.1, LCD_Y + GLASS_H / 2,
        LIP + GLASS_T, NEW, 'Glass')
    box(lcd, BAY_X0 + CLEARANCE, BAY_Y0 + CLEARANCE, LIP + GLASS_T, BAY_X1 - CLEARANCE, BAY_Y1 - CLEARANCE,
        LIP + GLASS_T + LCD_PCB, NEW, 'Pcb')
    box(lcd, BAY_X0 + 4, LCD_Y - 10, LIP + GLASS_T + LCD_PCB, BAY_X0 + 10, LCD_Y + 10, LIP + GLASS_T + LCD_PCB + 6, NEW,
        'PH2Connector')
    scd = new_component(root, 'Dummy_SCD41')
    zb = SCD_ZT - SCD_PCB
    box(scd, -SCD_W / 2, SCD_Y0, zb, SCD_W / 2, SCD_TOP, SCD_ZT - 0.01, NEW, 'Pcb')
    sx, sy = -SCD_SENSOR_X, SCD_Y0 + SCD_L / 2 + SCD_SENSOR_Y
    box(scd, sx - 5.05, sy - 5.05, zb - SCD_H, sx + 5.05, sy + 5.05, zb, NEW, 'SCD41')
    esp = new_component(root, 'Dummy_ESP32_C3')
    box(esp, C3_X - C3_W / 2, C3_Y0, C3_Z0, C3_X + C3_W / 2, C3_Y0 + C3_H, C3_Z0 + C3_PCB, NEW, 'C3Pcb')
    box(esp, C3_X - C3_USB_W / 2, C3_MOUTH, C3_Z0 + C3_PCB, C3_X + C3_USB_W / 2, C3_Y0 + 7.0, SOCKET_TOP, NEW,
        'UsbCSocket')
    # envelope of the parts on the board (buttons, chip, antenna), so nothing may come closer than they reach
    parts = box(esp, C3_X - C3_W / 2 + 1.5, C3_Y0 + 7.5, C3_Z0 + C3_PCB, C3_X + C3_W / 2 - 1.5, C3_Y0 + C3_H - 0.5,
                C3_Z0 + C3_PCB + C3_PARTS_H, NEW, 'Parts').bodies.item(0)
    parts.isLightBulbOn = False   # only for the interference check, it would hide the board in the pictures
    angled = new_component(root, 'Dummy_PlugAngled')
    pb = box(angled, C3_X - PLUG_W / 2, C3_MOUTH - 11.0, PLUG_Z - PLUG_H / 2, C3_X + PLUG_W / 2, C3_MOUTH - 0.5,
             COVER_Z - 0.2, NEW, 'Body').bodies.item(0)
    cylinders(angled, [(C3_X, BOOT_Y)], BOOT_D - 0.6, COVER_Z - 0.21, DEPTH + 5, ops[2], 'Boot', pb)
    straight = new_component(root, 'Dummy_PlugStraight')
    box(straight, C3_X - PLUG_W / 2, -BODY / 2 - 12, PLUG_Z - PLUG_H / 2, C3_X + PLUG_W / 2, C3_MOUTH - 0.5,
        PLUG_Z + PLUG_H / 2, NEW, 'Overmould')
    # reference parts are never printed: show them see-through so nobody mistakes them for enclosure parts
    for comp in (lcd, scd, esp, angled, straight):
        for b in comp.bRepBodies:
            b.opacity = 0.45


# ----------------------------------------------------------------------------- appearances
APPEARANCES = {   # English and German names of the Fusion appearance library
    'part': ('Plastic - Matte (White)', 'Kunststoff - matt (Weiß)'),
    'pcb': ('Plastic - Matte (Blue)', 'Kunststoff - matt (Blau)'),
    'sensor': ('Plastic - Matte (Gray)', 'Kunststoff - matt (Grau)'),
    'black': ('Plastic - Matte (Black)', 'Kunststoff - matt (Schwarz)'),
    'glass': ('Glass - Dark Color', 'Glas - dunkle Farbe'),
    'metal': ('Steel - Satin', 'Stahl - satiniert'),
}
BODY_LOOK = {'Pcb': 'pcb', 'C3Pcb': 'pcb', 'SCD41': 'sensor', 'Glass': 'glass', 'UsbCSocket': 'metal'}


def find_appearance(design, names):
    for a in design.appearances:
        if a.name in names:
            return a
    app = adsk.core.Application.get()
    for lib in app.materialLibraries:
        for a in lib.appearances:
            if a.name in names:
                return design.appearances.addByCopy(a, a.name)
    return None


def apply_appearances(design, root):
    """Printed parts light, reference parts in their real colours. Missing appearances are skipped."""
    looks = {k: find_appearance(design, v) for k, v in APPEARANCES.items()}
    for occ in root.occurrences:
        dummy = occ.component.name.startswith('Dummy_')
        for b in occ.component.bRepBodies:
            look = BODY_LOOK.get(b.name.split(' ')[0], 'black') if dummy else 'part'
            if looks.get(look):
                b.appearance = looks[look]


# ----------------------------------------------------------------------------- assembly
def add_joints(root):
    """Device parts move together and slide on the wall plate (0 = mounted, 15 mm = released)."""
    occ = {o.component.name: o for o in root.occurrences}
    device = ['Housing', 'SensorCarrier', 'BackCover', 'PortBack', 'Dummy_LCD_2inch', 'Dummy_SCD41',
              'Dummy_ESP32_C3', 'Dummy_PlugAngled']
    group = adsk.core.ObjectCollection.create()
    for n in device:
        group.add(occ[n])
    root.rigidGroups.add(group, True)
    occ['WallPlate'].isGrounded = True
    plate_group = adsk.core.ObjectCollection.create()
    plate_group.add(occ['WallPlate'])
    plate_group.add(occ['LockTab'])
    root.rigidGroups.add(plate_group, True)
    target = pt(0, RAIL_Y0, DEPTH)
    vertex = min((v for b in occ['WallPlate'].bRepBodies for v in b.vertices),
                 key=lambda v: v.geometry.distanceTo(target))
    geo = adsk.fusion.JointGeometry.createByPoint(vertex)
    ji = root.asBuiltJoints.createInput(occ['Housing'], occ['WallPlate'], geo)
    ji.setAsSliderJointMotion(adsk.fusion.JointDirections.YAxisJointDirection)
    joint = root.asBuiltJoints.add(ji)
    joint.name = 'RailSlider'
    lim = joint.jointMotion.slideLimits
    lim.isMinimumValueEnabled = True
    lim.minimumValue = 0.0
    lim.isMaximumValueEnabled = True
    lim.maximumValue = cm(RAIL_TRAVEL)


# ----------------------------------------------------------------------------- checks and export
C3_RIB_SQUEEZE = 0.5   # mm3, the four crush ribs together press at most this far into the ESP32-C3 board


def check_interference(design, root, components):
    bodies = adsk.core.ObjectCollection.create()
    for occ in root.allOccurrences:
        if occ.component.name in components:
            for b in occ.bRepBodies:
                bodies.add(b)
    result = design.analyzeInterference(design.createInterferenceInput(bodies))
    # the hook of the spring tongue overlaps the SCD41 board on purpose: that is its preload
    preload = SPRING_PRELOAD ** 2 / 2 * SPRING_W * 1.05
    count = 0
    for r in result:
        pair = {r.entityOne.parentComponent.name, r.entityTwo.parentComponent.name}
        vol = r.interferenceBody.volume * 1000
        if pair == {'SensorCarrier', 'Dummy_SCD41'} and vol <= preload:
            continue
        if pair == {'SensorCarrier', 'Dummy_ESP32_C3'} and vol <= C3_RIB_SQUEEZE:
            continue   # the crush ribs press on the board edges on purpose
        print('INTERFERENCE', *sorted(pair), round(vol, 2), 'mm3')
        count += 1
    return count


PRINT_PARTS = {'Housing': 'housing', 'BackCover': 'back_cover',
               'PortBack': 'cable_port_back', 'PortBottom': 'cable_port_bottom', 'WallPlate': 'wall_plate',
               'LockTab': 'lock_tab', 'DeskStand': 'desk_stand'}


def check_scd_fit():
    """The SCD41 board with end stop and hook must fit the sensor chamber."""
    problems = []
    if TONGUE_TIP > Y_DIV_LOW - 0.2:
        problems.append(f'SCD_L {SCD_L:g} mm is too long for the chamber, at most about '
                        f'{SCD_L - (TONGUE_TIP - (Y_DIV_LOW - 0.2)):.1f} mm: mount the board the other way round')
    if SCD_W / 2 + 1.35 > XR - 6.0:
        problems.append(f'SCD_W {SCD_W:g} mm is too wide for the chamber')
    if SCD_ZT - SCD_PCB - SCD_H < WALL + 0.5:
        problems.append('SCD_PCB + SCD_H too high: the sensor would touch the front wall')
    for msg in problems:
        print('WARNING', msg)
    return problems


def scd_parameters():
    return {k: globals()[k] for k in SCD_BOARDS['14x22']}


def active_profile():
    """Name of the board profile the SCD_* parameters belong to, None for a custom board."""
    cur = scd_parameters()
    for name, prof in SCD_BOARDS.items():
        if all(abs(cur[k] - v) < 1e-6 for k, v in prof.items()):
            return name
    return None


def carrier_files():
    names = [f'sensor_carrier_{n}' for n in SCD_BOARDS]
    return names if active_profile() else names + ['sensor_carrier_custom']


def export_carriers(design, root, ops, stl_dir):
    """One sensor carrier per board profile: build it, export it, remove it again."""
    saved = scd_parameters()
    jobs = [(n, prof) for n, prof in SCD_BOARDS.items()]
    if active_profile() is None:
        jobs.append(('custom', saved))
    em = design.exportManager
    for name, prof in jobs:
        globals().update(prof)
        derive()
        comp = build_sensor_carrier(root, ops, f'Export_{name}', None if name == 'custom' else name)
        occ = next(o for o in root.occurrences if o.component == comp)
        opt = em.createSTLExportOptions(comp.bRepBodies.item(0), os.path.join(stl_dir, f'sensor_carrier_{name}.stl'))
        opt.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
        opt.isBinaryFormat = True
        em.execute(opt)
        print('carrier', name, 'volume cm3', round(comp.bRepBodies.item(0).volume, 2))
        occ.deleteMe()
    globals().update(saved)
    derive()


def export_files(design, root, ops):
    repo_cad = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    stl_dir, step_dir = os.path.join(repo_cad, 'stl'), os.path.join(repo_cad, 'step')
    os.makedirs(stl_dir, exist_ok=True)
    os.makedirs(step_dir, exist_ok=True)
    em = design.exportManager
    for occ in root.occurrences:
        if occ.component.name in PRINT_PARTS:
            for b in occ.bRepBodies:
                opt = em.createSTLExportOptions(b, os.path.join(stl_dir, PRINT_PARTS[occ.component.name] + '.stl'))
                opt.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
                opt.isBinaryFormat = True
                em.execute(opt)
    export_carriers(design, root, ops, stl_dir)
    em.execute(em.createSTEPExportOptions(os.path.join(step_dir, 'co2_wall_sensor_assembly.step'), root))
    # fingerprint of the parameters, the CI checks that the print files belong to the current parameters
    with open(os.path.join(repo_cad, 'build_info.json'), 'w', encoding='utf-8') as f:
        json.dump({'enclosure_version': VERSION, 'parameters_sha256': parameters_fingerprint(),
                   'parts': sorted(list(PRINT_PARTS.values()) + carrier_files())}, f, indent=2)
        f.write('\n')
    print('Exported to', repo_cad)


def run(_context: str):
    app = adsk.core.Application.get()
    doc = app.activeDocument
    old = adsk.fusion.Design.cast(app.activeProduct) if doc else None
    taken = load_user_parameters(old)
    if old and not doc.isSaved and any(o.component.name == 'WallPlate' for o in old.rootComponent.occurrences):
        doc.close(False)  # discard an unsaved previous run of this generator
    app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    design = adsk.fusion.Design.cast(app.activeProduct)
    design.designType = adsk.fusion.DesignTypes.ParametricDesignType
    write_user_parameters(design)
    root = design.rootComponent
    ops = (adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
           adsk.fusion.FeatureOperations.CutFeatureOperation,
           adsk.fusion.FeatureOperations.JoinFeatureOperation)

    scd_problems = check_scd_fit()
    build_housing(root, ops)
    build_sensor_carrier(root, ops, profile=active_profile())
    build_back_cover(root, ops)
    build_port(root, ops, 'back')
    build_port(root, ops, 'bottom')
    build_wall_plate(root, ops, CABLE)
    build_lock_tab(root, ops)
    build_desk_stand(root, ops, CABLE)
    build_dummies(root, ops)

    device = {'Housing', 'SensorCarrier', 'BackCover', 'Dummy_LCD_2inch', 'Dummy_SCD41', 'Dummy_ESP32_C3'}
    wall = check_interference(design, root, device | {'PortBack', 'Dummy_PlugAngled', 'WallPlate', 'LockTab'})
    bottom = check_interference(design, root, device | {'PortBottom', 'Dummy_PlugStraight', 'WallPlate', 'LockTab'})
    desk = check_interference(design, root, device | {'PortBack', 'Dummy_PlugAngled', 'DeskStand'})
    add_joints(root)
    try:
        apply_appearances(design, root)
    except RuntimeError as e:
        print('note: appearances skipped', e)
    for occ in root.occurrences:
        if occ.component.name in ('DeskStand', 'PortBottom', 'Dummy_PlugStraight'):
            occ.isLightBulbOn = False
    root.isJointsFolderLightBulbOn = False
    for comp in design.allComponents:
        for sk in comp.sketches:
            sk.isVisible = False
    app.userInterface.activeSelections.clear()
    app.activeViewport.fit()
    print('Parameters taken over from the previous design:', taken)
    print('Interference wall/back exit:', wall, '| wall/bottom exit:', bottom, '| desk:', desk)
    for msg in scd_problems:
        print('WARNING', msg)
    print('Device W x H x D mm:', BODY, BODY, DEPTH, '+ rail', RAIL_H, '| SCD41 profile:', active_profile() or 'custom')
    print('Volume cm3:', {o.component.name: round(sum(b.volume for b in o.bRepBodies), 2) for o in root.occurrences})
    if EXPORT:
        export_files(design, root, ops)
