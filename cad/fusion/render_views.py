"""
Renders for the documentation, run in Fusion after generate_enclosure.py (same open design).

    render_views(out_dir)              every still image of docs/images, 1600 x 1200, transparent
    render_hero(out_dir, first, n)     frames of the README animation (tools/build_gif.py makes the GIFs)

The camera is given as a viewing direction in model coordinates (front z = 0, wall towards +z,
y up): the view is fitted to the visible parts and then zoomed. Reference parts are shown opaque.
"""
import math
import os

import adsk.core
import adsk.fusion

DEVICE = {'Housing', 'BackCover', 'PortBack', 'Dummy_LCD_2inch'}
TILT = math.radians(12.0)   # desk stand: device leans back by TILT

# name: (visible components, view direction (eye - target), target in mm, zoom after fit, tilted with the stand)
VIEWS = {
    'hero_wall': (DEVICE | {'WallPlate'}, (-0.55, 0.30, -0.78), (0, 0, 15), 1.0, False),
    'desk_stand': (DEVICE | {'DeskStand', 'Dummy_PlugAngled'}, (-0.55, 0.22, -0.80), (0, -15, 25), 1.0, True),
    'interior': ({'Housing', 'SensorCarrier', 'PortBack', 'Dummy_LCD_2inch', 'Dummy_SCD41', 'Dummy_ESP32_C3',
                  'Dummy_PlugAngled'}, (-0.20, 0.17, 0.96), (0, 0, 12), 1.0, False),
    'sensor_carrier_front': ({'SensorCarrier', 'Dummy_SCD41'}, (-0.55, 0.40, -0.73), (-3, -21, 10), 1.0, False),
    'sensor_carrier_back': ({'SensorCarrier', 'Dummy_ESP32_C3'}, (-0.30, 0.45, 0.84), (0, -21, 14), 1.0, False),
    'lock_tab': (DEVICE | {'WallPlate', 'LockTab', 'Dummy_PlugAngled'}, (-0.45, -0.70, -0.55), (-10, -38, 20),
                 0.5, False),
    'cable_port_back': ({'Housing', 'BackCover', 'PortBack', 'Dummy_PlugAngled'}, (-0.40, -0.45, 0.80), (0, 0, 12),
                        0.9, False),
    'cable_port_bottom': ({'Housing', 'BackCover', 'PortBottom', 'Dummy_PlugStraight'}, (-0.35, -0.75, 0.56),
                          (0, 0, 12), 0.9, False),
    'vent_mesh': ({'Housing', 'BackCover', 'PortBack'}, (-0.25, -0.85, -0.46), (0, -34, 8), 0.8, False),
}

# exploded view: offsets in mm (x, y, z) per component, the device flies apart along z
EXPLODE = {
    'Dummy_LCD_2inch': (0, 0, -45), 'Housing': (0, 0, 0), 'Dummy_SCD41': (0, -4, 22), 'SensorCarrier': (0, -4, 38),
    'Dummy_ESP32_C3': (0, -4, 54), 'PortBack': (0, -18, 64), 'Dummy_PlugAngled': (0, -30, 72),
    'BackCover': (0, 0, 84), 'WallPlate': (0, 0, 116), 'LockTab': (0, -22, 116),
}
EXPLODE_VIEW = ((-0.90, 0.30, -0.32), (0, -5, 40), 1.0)


def _design():
    return adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)


def _prepare(design):
    """Opaque reference parts; joints and rigid groups off so parts can be moved for the exploded view."""
    root = design.rootComponent
    for occ in root.occurrences:
        for b in occ.bRepBodies:
            b.opacity = 1.0
    for g in root.rigidGroups:
        g.isSuppressed = True
    for j in list(root.asBuiltJoints) + list(root.joints):
        j.isSuppressed = True
    root.isJointsFolderLightBulbOn = False


def _show(root, visible):
    for occ in root.occurrences:
        occ.isLightBulbOn = occ.component.name in visible


def _rot_x(v, a):
    x, y, z = v
    return (x, y * math.cos(a) - z * math.sin(a), y * math.sin(a) + z * math.cos(a))


def _camera(direction, target_mm, zoom, tilted=False):
    vp = adsk.core.Application.get().activeViewport
    d = direction
    up = (0, 1, 0)
    if tilted:
        d, up = _rot_x(d, -TILT), _rot_x(up, -TILT)
    n = math.sqrt(sum(c * c for c in d))
    t = [c / 10 for c in target_mm]
    cam = vp.camera
    cam.isSmoothTransition = False
    cam.target = adsk.core.Point3D.create(*t)
    cam.eye = adsk.core.Point3D.create(*(t[i] + 60 * d[i] / n for i in range(3)))
    cam.upVector = adsk.core.Vector3D.create(*up)
    vp.camera = cam
    vp.fit()
    cam = vp.camera
    cam.isSmoothTransition = False
    # perspective camera: zoom by moving the eye towards the target; close-ups look at the given target
    off = [(cam.eye.x - cam.target.x) * zoom, (cam.eye.y - cam.target.y) * zoom, (cam.eye.z - cam.target.z) * zoom]
    centre = t if zoom < 0.99 else [cam.target.x, cam.target.y, cam.target.z]
    cam.target = adsk.core.Point3D.create(*centre)
    cam.eye = adsk.core.Point3D.create(*(centre[i] + off[i] for i in range(3)))
    vp.camera = cam
    vp.refresh()


def _save(path, width=1600, height=1200):
    opt = adsk.core.SaveImageFileOptions.create(path)
    opt.width, opt.height = width, height
    opt.isBackgroundTransparent = True
    opt.isAntiAliased = True
    adsk.core.Application.get().activeViewport.saveAsImageFileWithOptions(opt)


def _explode(root, f):
    """Move the parts to f (0 = assembled, 1 = fully exploded)."""
    for occ in root.occurrences:
        dx, dy, dz = EXPLODE.get(occ.component.name, (0, 0, 0))
        m = adsk.core.Matrix3D.create()
        m.translation = adsk.core.Vector3D.create(dx * f / 10, dy * f / 10, dz * f / 10)
        occ.transform2 = m


def render_views(out_dir, names=None):
    os.makedirs(out_dir, exist_ok=True)
    design = _design()
    root = design.rootComponent
    _prepare(design)
    _explode(root, 0)
    for name, (visible, direction, target, zoom, tilted) in VIEWS.items():
        if names and name not in names:
            continue
        _show(root, visible)
        _camera(direction, target, zoom, tilted)
        _save(os.path.join(out_dir, name + '.png'))
    _show(root, set(EXPLODE))
    _explode(root, 1)
    _camera(*EXPLODE_VIEW)
    _save(os.path.join(out_dir, 'exploded_view.png'))
    _explode(root, 0)


def ease(t):
    return 0.5 - 0.5 * math.cos(math.pi * t)


# ----------------------------------------------------------------------------- hero animation
# parts leave one after another (front to back) and come back in reverse order
HERO_ORDER = ['Dummy_LCD_2inch', 'BackCover', 'Dummy_PlugAngled', 'PortBack', 'Dummy_ESP32_C3', 'SensorCarrier',
              'Dummy_SCD41', 'WallPlate', 'LockTab']
HERO_TARGET = (0, -2, 30)
HERO_ELEVATION = math.radians(16)
# active area of the display, seen from the front: (x, y) corners top left, top right, bottom right, bottom left
ACTIVE_W, ACTIVE_H, LCD_Y, LIP = 40.8, 30.6, 10.1, 2.0


def hero_state(i, count):
    """Global explode progress, per-part progress and camera azimuth of frame i (seamless loop)."""
    t = i / count
    if t < 0.12:
        g, out = 0.0, True
    elif t < 0.42:
        g, out = (t - 0.12) / 0.30, True
    elif t < 0.58:
        g, out = 1.0, True
    elif t < 0.88:
        g, out = 1.0 - (t - 0.58) / 0.30, False
    else:
        g, out = 0.0, False
    n = len(HERO_ORDER)
    stagger = 0.45
    parts = {}
    for k, name in enumerate(HERO_ORDER):
        delay = stagger * (k if out else n - 1 - k) / (n - 1)
        if out:
            x = (g - delay) / (1 - stagger)
        else:   # coming back: the last part out is the first one in
            x = 1 - ((1 - g) - delay) / (1 - stagger)
        parts[name] = ease(min(max(x, 0.0), 1.0))
    azimuth = math.radians(-32 + 14 * math.sin(2 * math.pi * t))
    return parts, azimuth


def _explode_parts(root, parts):
    for occ in root.occurrences:
        dx, dy, dz = EXPLODE.get(occ.component.name, (0, 0, 0))
        f = parts.get(occ.component.name, parts.get('Housing', 0.0))
        m = adsk.core.Matrix3D.create()
        m.translation = adsk.core.Vector3D.create(dx * f / 10, dy * f / 10, dz * f / 10)
        occ.transform2 = m


def render_hero(out_dir, first, n, count=96, distance=36.0):
    """Frames of the README animation at viewport size, plus the screen corners of the display in each frame."""
    import json
    os.makedirs(out_dir, exist_ok=True)
    app = adsk.core.Application.get()
    design = _design()
    root = design.rootComponent
    if first == 0:
        _prepare(design)
    _show(root, set(EXPLODE))
    vp = app.activeViewport
    corners_model = [(ACTIVE_W / 2, LCD_Y + ACTIVE_H / 2), (-ACTIVE_W / 2, LCD_Y + ACTIVE_H / 2),
                     (-ACTIVE_W / 2, LCD_Y - ACTIVE_H / 2), (ACTIVE_W / 2, LCD_Y - ACTIVE_H / 2)]
    for i in range(first, min(first + n, count)):
        parts, az = hero_state(i, count)
        _explode_parts(root, parts)
        d = (math.sin(az) * math.cos(HERO_ELEVATION), math.sin(HERO_ELEVATION), -math.cos(az) * math.cos(HERO_ELEVATION))
        t = [v / 10 for v in HERO_TARGET]
        cam = vp.camera
        cam.isSmoothTransition = False
        cam.target = adsk.core.Point3D.create(*t)
        cam.eye = adsk.core.Point3D.create(*(t[k] + distance * d[k] for k in range(3)))
        cam.upVector = adsk.core.Vector3D.create(0, 1, 0)
        vp.camera = cam
        vp.refresh()
        z = LIP + EXPLODE['Dummy_LCD_2inch'][2] * parts['Dummy_LCD_2inch']
        cam = vp.camera
        _save(os.path.join(out_dir, f'hero_{i:03d}.png'), vp.width, vp.height)
        # camera and display corners in mm: tools/build_gif.py projects the display content onto the glass
        with open(os.path.join(out_dir, f'hero_{i:03d}.json'), 'w', encoding='utf-8') as f:
            json.dump({'eye': [v * 10 for v in cam.eye.asArray()], 'target': [v * 10 for v in cam.target.asArray()],
                       'up': list(cam.upVector.asArray()), 'fov': cam.perspectiveAngle,
                       'size': [vp.width, vp.height],
                       'screen': [[x, y, z] for x, y in corners_model]}, f)
    if first + n >= count:
        _explode(root, 0)
