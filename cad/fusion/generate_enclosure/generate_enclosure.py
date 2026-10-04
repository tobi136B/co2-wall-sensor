"""
CO2-Wandsensor: parametrischer Gehaeuse-Generator fuer Autodesk Fusion
=======================================================================

Erzeugt in einem neuen Fusion-Dokument alle Bauteile als eigene Komponenten:

    Gehaeuse                  Frontgehaeuse mit Displayfenster und Sensorkammer
    Rueckdeckel               mit Schwalbenschwanz-Schiene und Kabelaustritt
    Wandplatte_Hohlwanddose   82 x 82, verdeckt eine Hohlwanddose (Kabel aus der Wand)
    Tischstaender             gleiche Schiene, Geraet lehnt 12 Grad nach hinten
    Platzhalter_*             Display, SCD41, ESP32-C3 und USB-C Winkelstecker

Ausfuehren in Fusion:  Dienstprogramme > Skripte und Zusatzmodule > "+" >
diesen Ordner hinzufuegen > generate_enclosure > Ausfuehren.

Alle Masse stehen im Block PARAMETER (mm). Aendern, Skript neu ausfuehren, fertig.
Koordinaten: Front liegt in z = 0, Wandseite bei +z, +y zeigt nach oben.
"""
import math
import adsk.core, adsk.fusion

# ===================== PARAMETER =====================
W = 66.8            # Aussenmass Geraet (quadratisch)
WAND = 2.0
LIPPE = 2.0
D = 20.0            # Geraetetiefe ohne Schiene
DECKEL_T = 2.5
DS = D - DECKEL_T
R_AUSSEN = 4.0
R_FRONT = 2.5       # weiche Frontkante
FASE_FENSTER = 0.8  # Fase um das Displayfenster
NEIGUNG = 12.0      # Neigung auf dem Tischstaender in Grad
SPIEL = 0.3
LCD_B, LCD_H, LCD_PCB = 58.0, 35.0, 1.6
GLAS_B, GLAS_H, GLAS_T = 48.2, 34.7, 2.5
AKT_B, AKT_H = 40.8, 30.6
LCD_X = -2.1        # aktive Flaeche mittig
LOCH_X, LOCH_Y = 26.5, 15.0
TRENN = 2.5
ZB_Z, ZB_T = 10.0, 1.5          # Zwischenboden Sensor vorn / ESP hinten
RIPPE_H = 1.3                   # Abstand ESP ueber Zwischenboden
STECKER_T = 6.0                 # Dicke USB-C Winkelstecker
INS_D, INS_T = 4.0, 6.0         # M3 Einschmelzmutter
C3_B, C3_H, C3_PCB = 18.0, 22.5, 1.0
C3_X = 13.0
SCD_B, SCD_H, SCD_T = 24.0, 22.0, 7.0   # PLATZHALTER, nachmessen
# Schwalbenschwanz
SW_FUSS, SW_KOPF, SW_H, SW_L = 12.0, 16.0, 3.0, 14.0
SW_Y0 = -10.0       # Unterkante Schiene
SW_HUB = 15.0       # Einschubweg: Geraet wird eingesetzt und 15 mm nach unten geschoben
SW_SPIEL = 0.3
# Wandplatte
WP = 82.0
WP_T = 7.0
DOSE_RAND, DOSE_RAND_T = 78.0, 1.5

# ===================== ABGELEITETE MASSE =====================
H = W
XL, XR = -W / 2 + WAND, W / 2 - WAND
YTOP_IN = H / 2 - WAND
P_B, P_H = LCD_B + 2 * SPIEL, LCD_H + 2 * SPIEL
PX0, PX1 = LCD_X - P_B / 2, LCD_X + P_B / 2
PY1 = YTOP_IN
PY0 = PY1 - P_H
LCD_Y = (PY0 + PY1) / 2
YSEP_B = PY0 - TRENN
YCH_B = -H / 2 + WAND
YCM = (YCH_B + YSEP_B) / 2
VI = adsk.core.ValueInput


def c(v):
    return v / 10.0


def P(x, y, z):
    return adsk.core.Point3D.create(c(x), c(y), c(z))


def SP(sk, x, y, z):
    p = sk.modelToSketchSpace(P(x, y, z))
    p.z = 0
    return p


def _offset_plane(comp, base, val, axis):
    i = comp.constructionPlanes.createInput()
    i.setByOffset(base, VI.createByReal(c(val)))
    pl = comp.constructionPlanes.add(i)
    if abs(getattr(pl.geometry.origin, axis) - c(val)) > 1e-6:
        pl.deleteMe()
        i = comp.constructionPlanes.createInput()
        i.setByOffset(base, VI.createByReal(-c(val)))
        pl = comp.constructionPlanes.add(i)
    return pl


def plane_z(comp, z):
    if abs(z) < 1e-9:
        return comp.xYConstructionPlane
    return _offset_plane(comp, comp.xYConstructionPlane, z, 'z')


def plane_y(comp, y):
    return _offset_plane(comp, comp.xZConstructionPlane, y, 'y')


def plane_x(comp, x):
    return _offset_plane(comp, comp.yZConstructionPlane, x, 'x')


def rects(comp, plane, rlist, name):
    sk = comp.sketches.add(plane)
    sk.name = name
    for a, b in rlist:
        sk.sketchCurves.sketchLines.addTwoPointRectangle(SP(sk, *a), SP(sk, *b))
    return sk


def circles(comp, plane, clist, name):
    sk = comp.sketches.add(plane)
    sk.name = name
    for ctr, dia in clist:
        sk.sketchCurves.sketchCircles.addByCenterRadius(SP(sk, *ctr), c(dia / 2))
    return sk


def poly(comp, plane, pts, name):
    sk = comp.sketches.add(plane)
    sk.name = name
    L = sk.sketchCurves.sketchLines
    sp = [SP(sk, *p) for p in pts]
    for i in range(len(sp)):
        L.addByTwoPoints(sp[i], sp[(i + 1) % len(sp)])
    return sk


def allprof(sk):
    oc = adsk.core.ObjectCollection.create()
    for p in sk.profiles:
        oc.add(p)
    return oc


def sym(comp, sk, length, op, name, body=None):
    ei = comp.features.extrudeFeatures.createInput(allprof(sk), op)
    ei.setSymmetricExtent(VI.createByReal(c(length)), True)
    if body is not None:
        ei.participantBodies = [body]
    f = comp.features.extrudeFeatures.add(ei)
    f.name = name
    return f


def box(comp, x0, y0, z0, x1, y1, z1, op, name, body=None):
    return sym(comp, rects(comp, plane_z(comp, (z0 + z1) / 2), [((x0, y0, 0), (x1, y1, 0))], name),
               z1 - z0, op, name, body)


def cyl(comp, pts, dia, z0, z1, op, name, body=None):
    return sym(comp, circles(comp, plane_z(comp, (z0 + z1) / 2), [((x, y, 0), dia) for x, y in pts], name),
               z1 - z0, op, name, body)


def schwalbe(comp, z_fuss, fuss, kopf, hoehe, y0, y1, op, name, body=None):
    """Trapez (schmal am Fuss, breit am Kopf) entlang y extrudiert."""
    ym = (y0 + y1) / 2
    zk = z_fuss + hoehe
    pts = [(-fuss / 2, ym, z_fuss), (fuss / 2, ym, z_fuss), (kopf / 2, ym, zk), (-kopf / 2, ym, zk)]
    return sym(comp, poly(comp, plane_y(comp, ym), pts, name), y1 - y0, op, name, body)


def nut(comp, body):
    """Schwalbenschwanz-Nut mit verdecktem Einsetzfenster darueber."""
    sp = SW_SPIEL
    CUT = adsk.fusion.FeatureOperations.CutFeatureOperation
    y0, y1 = SW_Y0 - sp, SW_Y0 + SW_L + sp
    schwalbe(comp, D - 0.01, SW_FUSS + 2 * sp, SW_KOPF + 2 * sp, SW_H + sp, y0, y1, CUT, 'Schwalbenschwanz_Nut', body)
    kb = SW_KOPF / 2 + sp
    box(comp, -kb, y1 - 0.01, D - 0.01, kb, y1 + SW_HUB, D + SW_H + sp, CUT, 'Einsetzfenster', body)


def fillet(comp, edges, r, name):
    oc = adsk.core.ObjectCollection.create()
    for e in edges:
        oc.add(e)
    if oc.count == 0:
        return None
    fi = comp.features.filletFeatures.createInput()
    fi.addConstantRadiusEdgeSet(oc, VI.createByReal(c(r)), True)
    f = comp.features.filletFeatures.add(fi)
    f.name = name
    return f


def chamfer(comp, edges, d, name):
    oc = adsk.core.ObjectCollection.create()
    for e in edges:
        oc.add(e)
    if oc.count == 0:
        return None
    ci = comp.features.chamferFeatures.createInput2()
    ci.chamferEdgeSets.addEqualDistanceChamferEdgeSet(oc, VI.createByReal(c(d)), True)
    f = comp.features.chamferFeatures.add(ci)
    f.name = name
    return f


def prism_x(comp, pts_yz, x0, x1, op, name, body=None):
    """Polygon in der YZ-Ebene, entlang x extrudiert."""
    xm = (x0 + x1) / 2
    sk = poly(comp, plane_x(comp, xm), [(xm, y, z) for y, z in pts_yz], name)
    return sym(comp, sk, x1 - x0, op, name, body)


def vert_edges(body, length, pred=lambda s: True):
    out = []
    for e in body.edges:
        g = e.geometry
        if isinstance(g, adsk.core.Line3D):
            s, t = g.startPoint, g.endPoint
            if (abs(s.x - t.x) < 1e-6 and abs(s.y - t.y) < 1e-6
                    and abs(abs(s.z - t.z) - c(length)) < 1e-5 and pred(s)):
                out.append(e)
    return out


def planar_face(body, z):
    return [f for f in body.faces if abs(f.pointOnFace.z - c(z)) < 1e-6
            and isinstance(f.geometry, adsk.core.Plane)][0]


def new_comp(root, name):
    occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    occ.component.name = name
    return occ.component


def run(_context: str):
    app = adsk.core.Application.get()
    act = app.activeDocument
    d0 = adsk.fusion.Design.cast(app.activeProduct) if act else None
    if d0 and not act.isSaved and any(o.component.name == 'Wandplatte_Hohlwanddose'
                                      for o in d0.rootComponent.occurrences):
        act.close(False)  # vorherigen ungespeicherten Lauf dieses Generators verwerfen
    app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    design = adsk.fusion.Design.cast(app.activeProduct)
    design.designType = adsk.fusion.DesignTypes.ParametricDesignType
    root = design.rootComponent
    NB = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    CUT = adsk.fusion.FeatureOperations.CutFeatureOperation
    JOIN = adsk.fusion.FeatureOperations.JoinFeatureOperation

    # ================= Gehaeuse =================
    fc = new_comp(root, 'Gehaeuse')
    body = box(fc, -W / 2, -H / 2, 0, W / 2, H / 2, D, NB, 'Grundkoerper').bodies.item(0)
    body.name = 'Gehaeuse'
    fillet(fc, vert_edges(body, D), R_AUSSEN, 'Ecken_R4')
    fillet(fc, list(planar_face(body, 0).edges), R_FRONT, 'Frontkante_R2.5')
    box(fc, XL, YCH_B, DS, XR, YTOP_IN, D + 1, CUT, 'Deckelsitz')

    # Displaytasche + Fenster
    box(fc, PX0, PY0, LIPPE, PX1, PY1, DS + 1, CUT, 'Displaytasche')
    wb, wh = AKT_B + 1.0, AKT_H + 1.0
    box(fc, -wb / 2, LCD_Y - wh / 2, -1, wb / 2, LCD_Y + wh / 2, LIPPE + 0.5, CUT, 'Displayfenster')
    fillet(fc, vert_edges(body, LIPPE, lambda s: abs(abs(s.x) - c(wb / 2)) < 1e-5), 1.0, 'Fenster_R1')
    ff = planar_face(body, 0)
    inner = [e for lp in ff.loops if not lp.isOuter for e in lp.edges]
    chamfer(fc, inner, FASE_FENSTER, 'Fenster_Fase')
    pts_lcd = [(LCD_X + sx * LOCH_X, LCD_Y + sy * LOCH_Y) for sx in (-1, 1) for sy in (-1, 1)]
    cyl(fc, pts_lcd, 4.4, LIPPE, LIPPE + GLAS_T, JOIN, 'LCD_Dome', body)
    cyl(fc, pts_lcd, 1.7, LIPPE + 0.5, LIPPE + GLAS_T + 0.1, CUT, 'LCD_M2_Bohrung')

    # Kinn: Sensor vorn, ESP hinten, Zwischenboden
    box(fc, XL, YCH_B, WAND, XR, YSEP_B, DS + 1, CUT, 'Kinn')
    box(fc, XL, YCH_B, ZB_Z, XR, YSEP_B, ZB_Z + ZB_T, JOIN, 'Zwischenboden', body)
    box(fc, XL + 2, YSEP_B - 4, ZB_Z - 0.5, XL + 8, YSEP_B + 0.1, ZB_Z + ZB_T + 0.5, CUT, 'Kabelkerbe_Sensor')
    # Durchbruch Trennwand fuer USB-Winkelstecker
    box(fc, C3_X - 10, YSEP_B - 0.5, ZB_Z + ZB_T, C3_X + 10, PY0 + 0.5, DS + 1, CUT, 'Durchbruch_Stecker')

    # Deckelbefestigung: unten 2x M3 Einschmelzmutter, oben 2 Einhaengetaschen
    bpts = [(XL + 4.0, YCH_B + 4.0), (XR - 4.0, YCH_B + 4.0)]
    cyl(fc, bpts, 7.5, ZB_Z + ZB_T, DS, JOIN, 'Dome_unten', body)
    cyl(fc, bpts, INS_D, DS - INS_T, DS + 0.1, CUT, 'M3_Einschmelzmuttern')
    for x in (-15.0, 15.0):
        box(fc, x - 4.3, YTOP_IN - 0.1, DS - 0.1, x + 4.3, YTOP_IN + 1.4, D - 0.8, CUT, 'Einhaengetasche')

    # C3 Auflage
    for x in (C3_X - 6, C3_X + 6):
        box(fc, x - 0.75, YCH_B + 2, ZB_Z + ZB_T, x + 0.75, YCH_B + 18, ZB_Z + ZB_T + RIPPE_H, JOIN, 'C3_Rippe', body)
    box(fc, C3_X - C3_B / 2 - 1.2, YCH_B, ZB_Z + ZB_T, C3_X - C3_B / 2, YCH_B + 15, ZB_Z + ZB_T + 2.5, JOIN,
        'C3_Seitenfuehrung', body)

    # Designfuge

    # Lueftung: unten + seitlich (nur Sensorkammer), Front bleibt geschlossen
    pb = plane_y(fc, -H / 2 + WAND / 2)
    xs = [-21 + 3.5 * i for i in range(13)]
    sym(fc, rects(fc, pb, [((x - 0.7, 0, 3.5), (x + 0.7, 0, ZB_Z - 1.5)) for x in xs], 'Schlitze_Unten'),
        WAND + 1, CUT, 'Schlitze_Unten')
    for xs_ in (-W / 2 + WAND / 2, W / 2 - WAND / 2):
        px = plane_x(fc, xs_)
        sl = [((0, YCM + o - 0.7, 3.5), (0, YCM + o + 0.7, ZB_Z - 1.5)) for o in (-7, -3.5, 0)]
        sym(fc, rects(fc, px, sl, 'Schlitze_Seite'), WAND + 1, CUT, 'Schlitze_Seite')

    # ================= Rueckdeckel mit Schiene =================
    dc = new_comp(root, 'Rueckdeckel')
    s = 0.2
    db = box(dc, XL + s, YCH_B + s, DS, XR - s, YTOP_IN - s, D, NB, 'Deckel').bodies.item(0)
    db.name = 'Rueckdeckel'
    for x in (-15.0, 15.0):
        box(dc, x - 4.0, YTOP_IN - s - 0.1, DS + 0.1, x + 4.0, YTOP_IN + 1.2, D - 1.0, JOIN, 'Einhaengenase', db)
    hs = dc.sketches.add(planar_face(db, D))
    hs.name = 'Schraubloecher'
    hp = adsk.core.ObjectCollection.create()
    for x, y in bpts:
        hp.add(hs.sketchPoints.add(SP(hs, x, y, D)))
    hi = dc.features.holeFeatures.createCountersinkInput(
        VI.createByReal(c(3.4)), VI.createByReal(c(6.4)), VI.createByString('90 deg'))
    hi.setPositionBySketchPoints(hp)
    hi.setAllExtent(adsk.fusion.ExtentDirections.PositiveExtentDirection)
    hi.participantBodies = [db]
    dc.features.holeFeatures.add(hi).name = 'Senkung_M3'
    # Kabelaustritt hinten (Winkelstecker)
    KX0, KX1, KY0, KY1 = C3_X - 7, C3_X + 7, YSEP_B - 1, PY0 + 9
    box(dc, KX0, KY0, DS - 1, KX1, KY1, D + 1, CUT, 'Kabelaustritt', db)
    # Andruecker ESP
    cyl(dc, [(C3_X - 6, YCH_B + 4), (C3_X + 6, YCH_B + 4)], 3.0, ZB_Z + ZB_T + RIPPE_H + C3_PCB + 1.2, DS, JOIN,
        'C3_Andruecker', db)
    # Schwalbenschwanz-Schiene
    schwalbe(dc, D, SW_FUSS, SW_KOPF, SW_H, SW_Y0, SW_Y0 + SW_L, JOIN, 'Schiene', db)

    # ================= Wandplatte =================
    wc = new_comp(root, 'Wandplatte_Hohlwanddose')
    wb_ = box(wc, -WP / 2, -WP / 2, D, WP / 2, WP / 2, D + WP_T, NB, 'Platte').bodies.item(0)
    wb_.name = 'Wandplatte'
    fillet(wc, vert_edges(wb_, WP_T), R_AUSSEN + (WP - W) / 2, 'Ecken_konzentrisch')
    fillet(wc, list(planar_face(wb_, D).edges), 2.0, 'Frontkante_R2')
    zw = D + WP_T
    cyl(wc, [(0, 0)], DOSE_RAND, zw - DOSE_RAND_T, zw + 1, CUT, 'Aussparung_Dosenrand', wb_)
    nut(wc, wb_)
    box(wc, KX0, KY0 - 1, D - 1, KX1, KY1 + 1, zw + 1, CUT, 'Kabeldurchlass', wb_)
    sl = [((-30 - 2, -1.75, 0), (-30 + 2, 1.75, 0)), ((30 - 2, -1.75, 0), (30 + 2, 1.75, 0))]
    sym(wc, rects(wc, plane_z(wc, D + WP_T / 2), sl, 'Langloecher'), WP_T + 1, CUT, 'Langloecher', wb_)
    sk2 = [((-30 - 3.3, -3.3, 0), (-30 + 3.3, 3.3, 0)), ((30 - 3.3, -3.3, 0), (30 + 3.3, 3.3, 0))]
    sym(wc, rects(wc, plane_z(wc, D + 1.0), sk2, 'Kopfsenkung'), 3.0, CUT, 'Kopfsenkung', wb_)

    # ================= Tischstaender (gleiche Schiene) =================
    tc = new_comp(root, 'Tischstaender')
    t = math.tan(math.radians(NEIGUNG))
    Z_V, Z_H = -2.0, 46.0                  # Standflaeche vorn / hinten
    # Standebene steigt im Geraetekoordinatensystem nach hinten an -> Geraet lehnt nach hinten.
    # 5 mm Luftspalt an der hinteren Unterkante, Lueftung unten bleibt frei.
    YF = -H / 2 - 5.0 - t * (D - Z_V)
    yb = lambda z: YF + t * (z - Z_V)      # Oberkante Fuss
    tb = prism_x(tc, [(yb(Z_V), Z_V), (yb(Z_H), Z_H), (yb(Z_H) - 4, Z_H), (yb(Z_V) - 4, Z_V)],
                 -W / 2 + 4, W / 2 - 4, NB, 'Fuss').bodies.item(0)
    tb.name = 'Tischstaender'
    y_top = SW_Y0 + SW_L + SW_HUB + 4
    prism_x(tc, [(yb(D) - 2, D), (y_top, D), (y_top, D + 7), (yb(D + 7) - 2, D + 7)], -14, 14, JOIN, 'Ruecken', tb)
    # Stuetzrippe hinten
    prism_x(tc, [(yb(D + 7) - 1, D + 7), (y_top - 12, D + 7), (yb(D + 24) - 1, D + 24)], -1.5, 1.5, JOIN,
            'Stuetzrippe', tb)
    nut(tc, tb)
    box(tc, KX0, KY0 - 1, D - 1, KX1, KY1 + 1, D + 8, CUT, 'Kabeldurchlass', tb)
    prism_x(tc, [(yb(Z_H - 8) + 1, Z_H - 8), (yb(Z_H) + 1, Z_H + 1), (yb(Z_H) - 5, Z_H + 1), (yb(Z_H - 8) - 5, Z_H - 8)],
            -4, 4, CUT, 'Kabelkerbe', tb)
    for e_len in (W - 8,):
        try:
            edges = [e for e in tb.edges if isinstance(e.geometry, adsk.core.Line3D)
                     and abs(e.length - c(e_len)) < 1e-4]
            fillet(tc, edges, 1.5, 'Fuss_Kanten')
        except Exception:
            pass

    lc = new_comp(root, 'Platzhalter_LCD_2inch')
    box(lc, LCD_X - GLAS_B / 2 + 0.1, LCD_Y - GLAS_H / 2, LIPPE, LCD_X + GLAS_B / 2 + 0.1, LCD_Y + GLAS_H / 2,
        LIPPE + GLAS_T, NB, 'Glas')
    box(lc, PX0 + SPIEL, PY0 + SPIEL, LIPPE + GLAS_T, PX1 - SPIEL, PY1 - SPIEL, LIPPE + GLAS_T + LCD_PCB, NB, 'Platine')
    box(lc, PX0 + 4, LCD_Y - 10, LIPPE + GLAS_T + LCD_PCB, PX0 + 10, LCD_Y + 10, LIPPE + GLAS_T + LCD_PCB + 6, NB,
        'PH2_Stecker')
    sc = new_comp(root, 'Platzhalter_SCD41')
    box(sc, -SCD_B / 2, YCM - SCD_H / 2, WAND + 0.5, SCD_B / 2, YCM + SCD_H / 2, WAND + 0.5 + SCD_T, NB, 'SCD41')
    cc = new_comp(root, 'Platzhalter_ESP32_C3')
    z0 = ZB_Z + ZB_T + RIPPE_H
    y0 = YCH_B + 1.0
    box(cc, C3_X - C3_B / 2, y0, z0, C3_X + C3_B / 2, y0 + C3_H, z0 + C3_PCB, NB, 'C3_Platine')
    yu = y0 + C3_H
    box(cc, C3_X - 4.5, yu - 7.0, z0 + C3_PCB, C3_X + 4.5, yu + 0.5, z0 + C3_PCB + 3.2, NB, 'USB_C_Buchse')
    zm = z0 + C3_PCB + 1.6
    box(cc, C3_X - 6, yu + 0.5, zm - STECKER_T / 2, C3_X + 6, yu + 12.5, zm + STECKER_T / 2, NB, 'Winkelstecker')

    bodies = adsk.core.ObjectCollection.create()
    for occ in root.allOccurrences:
        if occ.component.name != 'Tischstaender':
            for b in occ.bRepBodies:
                bodies.add(b)
    res = design.analyzeInterference(design.createInterferenceInput(bodies))
    for r in res:
        print('KOLLISION', r.entityOne.parentComponent.name, r.entityOne.name, '<->',
              r.entityTwo.parentComponent.name, r.entityTwo.name, round(r.interferenceBody.volume * 1000, 2), 'mm3')
    for occ in root.occurrences:
        if occ.component.name == 'Tischstaender':
            occ.isLightBulbOn = False
    app.activeViewport.fit()
    print('Kollisionen:', res.count)
    print('Geraet B x H x T mm:', W, H, D, '+ Schiene', SW_H)
    print('Volumen cm3:', {o.component.name: round(sum(b.volume for b in o.bRepBodies), 2) for o in root.occurrences})
