"""
CO2 Wall Sensor: parametric enclosure generator for Autodesk Fusion
===================================================================

Creates a new Fusion design that contains every part as its own component:

    Housing        front housing with display window and isolated sensor chamber
    BackCover      back cover with dovetail rail and cable exit
    WallPlate      82 x 82 plate that covers a German flush wall box (cable from the wall)
    DeskStand      desk stand using the same rail, device leans back by 12 degrees
    Dummy_*        reference bodies for display, SCD41, ESP32-C3 and the USB-C plug

Run it in Fusion: Utilities > Scripts and Add-Ins > "+" > add this folder >
select generate_enclosure > Run.

All dimensions live in the PARAMETERS block (millimetres). Change a value,
run the script again, done. Set EXPORT = True to also write STL and STEP files
into cad/stl and cad/step next to this repository.

Coordinate system: front face at z = 0, wall side towards +z, +y points up.
"""
import math
import os

import adsk.core
import adsk.fusion

# ===================== PARAMETERS =====================
# --- device body ---
BODY = 66.8             # outer width and height of the device
WALL = 2.0              # wall thickness
LIP = 2.0               # front lip in front of the display glass
DEPTH = 20.0            # device depth without rail
COVER_T = 2.5           # back cover thickness
R_CORNER = 4.0          # outer corner radius
R_FRONT = 2.5           # soft front edge
WINDOW_CHAMFER = 0.8    # chamfer around the display window
CLEARANCE = 0.3         # fit clearance per side
# --- Waveshare 2inch LCD (ST7789V), mounted in landscape ---
LCD_W, LCD_H, LCD_PCB = 58.0, 35.0, 1.6
GLASS_W, GLASS_H, GLASS_T = 48.2, 34.7, 2.5     # GLASS_T is an assumption, measure it
ACTIVE_W, ACTIVE_H = 40.8, 30.6
LCD_X = -2.1            # PCB offset so the active area is centred in the window
LCD_HOLE_X, LCD_HOLE_Y = 26.5, 15.0
# --- chin: sensor chamber in front, ESP32-C3 behind ---
DIVIDER = 2.5           # wall between display bay and chin
FLOOR_Z, FLOOR_T = 10.0, 1.5    # floor separating sensor chamber and ESP bay
RIB_H = 1.3             # ESP32-C3 sits this far above the floor
PLUG_T = 6.0            # thickness of the right-angle USB-C plug
INSERT_D, INSERT_L = 4.0, 6.0   # hole for M3 heat-set insert
C3_W, C3_H, C3_PCB = 18.0, 22.5, 1.0
C3_X = 13.0
SCD_W, SCD_H, SCD_T = 24.0, 22.0, 7.0          # PLACEHOLDER, measure your SCD41 board
# --- dovetail rail ---
RAIL_FOOT, RAIL_HEAD, RAIL_H, RAIL_L = 12.0, 16.0, 3.0, 14.0
RAIL_Y0 = -10.0         # lower end of the rail
RAIL_TRAVEL = 15.0      # insert the device, then slide it 15 mm down
RAIL_CLEARANCE = 0.3
# --- wall plate for flush wall box (68 mm hole, 60 mm screw spacing) ---
PLATE = 82.0
PLATE_T = 7.0
BOX_RIM_D, BOX_RIM_T = 78.0, 1.5
BOX_SCREW_SPACING = 60.0
# --- desk stand ---
TILT = 12.0             # device leans back by this angle
STAND_GAP = 5.0         # air gap below the device, keeps the vents free
# --- output ---
EXPORT = False          # True: write STL + STEP into ../../stl and ../../step

# ===================== DERIVED DIMENSIONS =====================
COVER_Z = DEPTH - COVER_T
XL, XR = -BODY / 2 + WALL, BODY / 2 - WALL
Y_TOP_IN = BODY / 2 - WALL
BAY_W, BAY_H = LCD_W + 2 * CLEARANCE, LCD_H + 2 * CLEARANCE
BAY_X0, BAY_X1 = LCD_X - BAY_W / 2, LCD_X + BAY_W / 2
BAY_Y1 = Y_TOP_IN
BAY_Y0 = BAY_Y1 - BAY_H
LCD_Y = (BAY_Y0 + BAY_Y1) / 2
Y_DIV_LOW = BAY_Y0 - DIVIDER
Y_CHIN_LOW = -BODY / 2 + WALL
Y_CHIN_MID = (Y_CHIN_LOW + Y_DIV_LOW) / 2
VI = adsk.core.ValueInput


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
    return f


def box(comp, x0, y0, z0, x1, y1, z1, op, name, body=None):
    sk = rect_sketch(comp, plane_z(comp, (z0 + z1) / 2), [((x0, y0, 0), (x1, y1, 0))], name)
    return extrude(comp, sk, z1 - z0, op, name, body)


def cylinders(comp, centres, dia, z0, z1, op, name, body=None):
    sk = circle_sketch(comp, plane_z(comp, (z0 + z1) / 2), [((x, y, 0), dia) for x, y in centres], name)
    return extrude(comp, sk, z1 - z0, op, name, body)


def prism_x(comp, points_yz, x0, x1, op, name, body=None):
    """Polygon in the YZ plane, extruded along x."""
    xm = (x0 + x1) / 2
    sk = poly_sketch(comp, plane_x(comp, xm), [(xm, y, z) for y, z in points_yz], name)
    return extrude(comp, sk, x1 - x0, op, name, body)


def dovetail(comp, z_foot, foot, head, height, y0, y1, op, name, body=None):
    """Trapezoid (narrow at the foot, wide at the head) extruded along y."""
    ym = (y0 + y1) / 2
    zh = z_foot + height
    pts = [(-foot / 2, ym, z_foot), (foot / 2, ym, z_foot), (head / 2, ym, zh), (-head / 2, ym, zh)]
    return extrude(comp, poly_sketch(comp, plane_y(comp, ym), pts, name), y1 - y0, op, name, body)


def dovetail_slot(comp, body):
    """Dovetail slot with a hidden insertion window above it (shared by wall plate and stand)."""
    c = RAIL_CLEARANCE
    cut = adsk.fusion.FeatureOperations.CutFeatureOperation
    y0, y1 = RAIL_Y0 - c, RAIL_Y0 + RAIL_L + c
    dovetail(comp, DEPTH - 0.01, RAIL_FOOT + 2 * c, RAIL_HEAD + 2 * c, RAIL_H + c, y0, y1, cut, 'DovetailSlot', body)
    hw = RAIL_HEAD / 2 + c
    box(comp, -hw, y1 - 0.01, DEPTH - 0.01, hw, y1 + RAIL_TRAVEL, DEPTH + RAIL_H + c, cut, 'InsertionWindow', body)


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
    inp.chamferEdgeSets.addEqualDistanceChamferEdgeSet(oc, VI.createByReal(cm(dist)), True)
    f = comp.features.chamferFeatures.add(inp)
    f.name = name
    return f


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


# ----------------------------------------------------------------------------- parts
def build_housing(root, ops):
    NEW, CUT, JOIN = ops
    comp = new_component(root, 'Housing')
    body = box(comp, -BODY / 2, -BODY / 2, 0, BODY / 2, BODY / 2, DEPTH, NEW, 'BaseBody').bodies.item(0)
    body.name = 'Housing'
    fillet(comp, z_edges(body, DEPTH), R_CORNER, 'CornerRadius')
    fillet(comp, list(planar_face_at_z(body, 0).edges), R_FRONT, 'SoftFrontEdge')
    box(comp, XL, Y_CHIN_LOW, COVER_Z, XR, Y_TOP_IN, DEPTH + 1, CUT, 'CoverSeat')

    # display bay and window
    box(comp, BAY_X0, BAY_Y0, LIP, BAY_X1, BAY_Y1, COVER_Z + 1, CUT, 'DisplayBay')
    ww, wh = ACTIVE_W + 1.0, ACTIVE_H + 1.0
    box(comp, -ww / 2, LCD_Y - wh / 2, -1, ww / 2, LCD_Y + wh / 2, LIP + 0.5, CUT, 'DisplayWindow')
    fillet(comp, z_edges(body, LIP, lambda p: abs(abs(p.x) - cm(ww / 2)) < 1e-5), 1.0, 'WindowCorners')
    front = planar_face_at_z(body, 0)
    chamfer(comp, [e for lp in front.loops if not lp.isOuter for e in lp.edges], WINDOW_CHAMFER, 'WindowChamfer')
    holes = [(LCD_X + sx * LCD_HOLE_X, LCD_Y + sy * LCD_HOLE_Y) for sx in (-1, 1) for sy in (-1, 1)]
    cylinders(comp, holes, 4.4, LIP, LIP + GLASS_T, JOIN, 'LcdBosses', body)
    cylinders(comp, holes, 1.7, LIP + 0.5, LIP + GLASS_T + 0.1, CUT, 'LcdScrewHoles')

    # chin: sensor chamber in front, ESP bay behind
    box(comp, XL, Y_CHIN_LOW, WALL, XR, Y_DIV_LOW, COVER_Z + 1, CUT, 'Chin')
    box(comp, XL, Y_CHIN_LOW, FLOOR_Z, XR, Y_DIV_LOW, FLOOR_Z + FLOOR_T, JOIN, 'ChamberFloor', body)
    box(comp, XL + 2, Y_DIV_LOW - 4, FLOOR_Z - 0.5, XL + 8, Y_DIV_LOW + 0.1, FLOOR_Z + FLOOR_T + 0.5, CUT,
        'SensorCableNotch')
    box(comp, C3_X - 10, Y_DIV_LOW - 0.5, FLOOR_Z + FLOOR_T, C3_X + 10, BAY_Y0 + 0.5, COVER_Z + 1, CUT,
        'PlugPassage')

    # cover fixing: 2x M3 heat-set insert at the bottom, 2 hook pockets at the top
    bosses = [(XL + 4.0, Y_CHIN_LOW + 4.0), (XR - 4.0, Y_CHIN_LOW + 4.0)]
    cylinders(comp, bosses, 7.5, FLOOR_Z + FLOOR_T, COVER_Z, JOIN, 'ScrewBosses', body)
    cylinders(comp, bosses, INSERT_D, COVER_Z - INSERT_L, COVER_Z + 0.1, CUT, 'M3InsertHoles')
    for x in (-15.0, 15.0):
        box(comp, x - 4.3, Y_TOP_IN - 0.1, COVER_Z - 0.1, x + 4.3, Y_TOP_IN + 1.4, DEPTH - 0.8, CUT, 'HookPocket')

    # ESP32-C3 support ribs and side guide
    for x in (C3_X - 6, C3_X + 6):
        box(comp, x - 0.75, Y_CHIN_LOW + 2, FLOOR_Z + FLOOR_T, x + 0.75, Y_CHIN_LOW + 18,
            FLOOR_Z + FLOOR_T + RIB_H, JOIN, 'C3Rib', body)
    box(comp, C3_X - C3_W / 2 - 1.2, Y_CHIN_LOW, FLOOR_Z + FLOOR_T, C3_X - C3_W / 2, Y_CHIN_LOW + 15,
        FLOOR_Z + FLOOR_T + 2.5, JOIN, 'C3SideGuide', body)

    # vents: bottom and sides of the sensor chamber only, the front stays closed
    bottom = plane_y(comp, -BODY / 2 + WALL / 2)
    xs = [-21 + 3.5 * i for i in range(13)]
    extrude(comp, rect_sketch(comp, bottom, [((x - 0.7, 0, 3.5), (x + 0.7, 0, FLOOR_Z - 1.5)) for x in xs],
                              'BottomVents'), WALL + 1, CUT, 'BottomVents')
    for xp in (-BODY / 2 + WALL / 2, BODY / 2 - WALL / 2):
        slots = [((0, Y_CHIN_MID + o - 0.7, 3.5), (0, Y_CHIN_MID + o + 0.7, FLOOR_Z - 1.5)) for o in (-7, -3.5, 0)]
        extrude(comp, rect_sketch(comp, plane_x(comp, xp), slots, 'SideVents'), WALL + 1, CUT, 'SideVents')
    return comp, bosses


def build_back_cover(root, ops, bosses):
    NEW, CUT, JOIN = ops
    comp = new_component(root, 'BackCover')
    s = 0.2
    body = box(comp, XL + s, Y_CHIN_LOW + s, COVER_Z, XR - s, Y_TOP_IN - s, DEPTH, NEW, 'Cover').bodies.item(0)
    body.name = 'BackCover'
    for x in (-15.0, 15.0):
        box(comp, x - 4.0, Y_TOP_IN - s - 0.1, COVER_Z + 0.1, x + 4.0, Y_TOP_IN + 1.2, DEPTH - 1.0, JOIN, 'Hook', body)
    sk = comp.sketches.add(planar_face_at_z(body, DEPTH))
    sk.name = 'ScrewHoles'
    points = adsk.core.ObjectCollection.create()
    for x, y in bosses:
        points.add(sk.sketchPoints.add(sketch_pt(sk, x, y, DEPTH)))
    hole = comp.features.holeFeatures.createCountersinkInput(
        VI.createByReal(cm(3.4)), VI.createByReal(cm(6.4)), VI.createByString('90 deg'))
    hole.setPositionBySketchPoints(points)
    hole.setAllExtent(adsk.fusion.ExtentDirections.PositiveExtentDirection)
    hole.participantBodies = [body]
    comp.features.holeFeatures.add(hole).name = 'M3Countersink'
    cable = (C3_X - 7, C3_X + 7, Y_DIV_LOW - 1, BAY_Y0 + 9)
    box(comp, cable[0], cable[2], COVER_Z - 1, cable[1], cable[3], DEPTH + 1, CUT, 'CableExit', body)
    cylinders(comp, [(C3_X - 6, Y_CHIN_LOW + 4), (C3_X + 6, Y_CHIN_LOW + 4)], 3.0,
              FLOOR_Z + FLOOR_T + RIB_H + C3_PCB + 1.2, COVER_Z, JOIN, 'C3HoldDown', body)
    dovetail(comp, DEPTH, RAIL_FOOT, RAIL_HEAD, RAIL_H, RAIL_Y0, RAIL_Y0 + RAIL_L, JOIN, 'Rail', body)
    return comp, cable


def build_wall_plate(root, ops, cable):
    NEW, CUT, JOIN = ops
    comp = new_component(root, 'WallPlate')
    body = box(comp, -PLATE / 2, -PLATE / 2, DEPTH, PLATE / 2, PLATE / 2, DEPTH + PLATE_T, NEW, 'Plate').bodies.item(0)
    body.name = 'WallPlate'
    fillet(comp, z_edges(body, PLATE_T), R_CORNER + (PLATE - BODY) / 2, 'ConcentricCorners')
    fillet(comp, list(planar_face_at_z(body, DEPTH).edges), 2.0, 'FrontEdge')
    z_wall = DEPTH + PLATE_T
    cylinders(comp, [(0, 0)], BOX_RIM_D, z_wall - BOX_RIM_T, z_wall + 1, CUT, 'BoxRimRecess', body)
    dovetail_slot(comp, body)
    box(comp, cable[0], cable[2] - 1, DEPTH - 1, cable[1], cable[3] + 1, z_wall + 1, CUT, 'CablePassage', body)
    a = BOX_SCREW_SPACING / 2
    slots = [((-a - 2, -1.75, 0), (-a + 2, 1.75, 0)), ((a - 2, -1.75, 0), (a + 2, 1.75, 0))]
    extrude(comp, rect_sketch(comp, plane_z(comp, DEPTH + PLATE_T / 2), slots, 'ScrewSlots'), PLATE_T + 1, CUT,
            'ScrewSlots', body)
    heads = [((-a - 3.3, -3.3, 0), (-a + 3.3, 3.3, 0)), ((a - 3.3, -3.3, 0), (a + 3.3, 3.3, 0))]
    extrude(comp, rect_sketch(comp, plane_z(comp, DEPTH + 1.0), heads, 'ScrewHeadRecess'), 3.0, CUT,
            'ScrewHeadRecess', body)
    return comp


def build_desk_stand(root, ops, cable):
    NEW, CUT, JOIN = ops
    comp = new_component(root, 'DeskStand')
    t = math.tan(math.radians(TILT))
    z_front, z_back = -2.0, 46.0
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
    box(scd, -SCD_W / 2, Y_CHIN_MID - SCD_H / 2, WALL + 0.5, SCD_W / 2, Y_CHIN_MID + SCD_H / 2, WALL + 0.5 + SCD_T, NEW,
        'SCD41')
    esp = new_component(root, 'Dummy_ESP32_C3')
    z0 = FLOOR_Z + FLOOR_T + RIB_H
    y0 = Y_CHIN_LOW + 1.0
    box(esp, C3_X - C3_W / 2, y0, z0, C3_X + C3_W / 2, y0 + C3_H, z0 + C3_PCB, NEW, 'C3Pcb')
    yu = y0 + C3_H
    box(esp, C3_X - 4.5, yu - 7.0, z0 + C3_PCB, C3_X + 4.5, yu + 0.5, z0 + C3_PCB + 3.2, NEW, 'UsbCSocket')
    zm = z0 + C3_PCB + 1.6
    box(esp, C3_X - 6, yu + 0.5, zm - PLUG_T / 2, C3_X + 6, yu + 12.5, zm + PLUG_T / 2, NEW, 'RightAnglePlug')


# ----------------------------------------------------------------------------- checks and export
def check_interference(design, root, components):
    bodies = adsk.core.ObjectCollection.create()
    for occ in root.allOccurrences:
        if occ.component.name in components:
            for b in occ.bRepBodies:
                bodies.add(b)
    result = design.analyzeInterference(design.createInterferenceInput(bodies))
    for r in result:
        print('INTERFERENCE', r.entityOne.parentComponent.name, '<->', r.entityTwo.parentComponent.name,
              round(r.interferenceBody.volume * 1000, 2), 'mm3')
    return result.count


def export_files(design, root):
    repo_cad = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    stl_dir, step_dir = os.path.join(repo_cad, 'stl'), os.path.join(repo_cad, 'step')
    os.makedirs(stl_dir, exist_ok=True)
    os.makedirs(step_dir, exist_ok=True)
    em = design.exportManager
    names = {'Housing': 'housing', 'BackCover': 'back_cover', 'WallPlate': 'wall_plate', 'DeskStand': 'desk_stand'}
    for occ in root.occurrences:
        if occ.component.name in names:
            for b in occ.bRepBodies:
                opt = em.createSTLExportOptions(b, os.path.join(stl_dir, names[occ.component.name] + '.stl'))
                opt.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
                opt.isBinaryFormat = True
                em.execute(opt)
    em.execute(em.createSTEPExportOptions(os.path.join(step_dir, 'co2_wall_sensor_assembly.step'), root))
    print('Exported to', repo_cad)


def run(_context: str):
    app = adsk.core.Application.get()
    doc = app.activeDocument
    old = adsk.fusion.Design.cast(app.activeProduct) if doc else None
    if old and not doc.isSaved and any(o.component.name == 'WallPlate' for o in old.rootComponent.occurrences):
        doc.close(False)  # discard an unsaved previous run of this generator
    app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    design = adsk.fusion.Design.cast(app.activeProduct)
    design.designType = adsk.fusion.DesignTypes.ParametricDesignType
    root = design.rootComponent
    ops = (adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
           adsk.fusion.FeatureOperations.CutFeatureOperation,
           adsk.fusion.FeatureOperations.JoinFeatureOperation)

    _, bosses = build_housing(root, ops)
    _, cable = build_back_cover(root, ops, bosses)
    build_wall_plate(root, ops, cable)
    build_desk_stand(root, ops, cable)
    build_dummies(root, ops)

    wall = check_interference(design, root, {'Housing', 'BackCover', 'WallPlate', 'Dummy_LCD_2inch', 'Dummy_SCD41',
                                             'Dummy_ESP32_C3'})
    desk = check_interference(design, root, {'Housing', 'BackCover', 'DeskStand', 'Dummy_ESP32_C3'})
    for occ in root.occurrences:
        if occ.component.name == 'DeskStand':
            occ.isLightBulbOn = False
    app.activeViewport.fit()
    print('Interference wall assembly:', wall, '| desk assembly:', desk)
    print('Device W x H x D mm:', BODY, BODY, DEPTH, '+ rail', RAIL_H)
    print('Volume cm3:', {o.component.name: round(sum(b.volume for b in o.bRepBodies), 2) for o in root.occurrences})
    if EXPORT:
        export_files(design, root)
