"""
Renders for the documentation, run in Fusion after generate_enclosure.py (same open design).

    render_views(out_dir)              every still image of docs/images, 1600 x 1200, transparent
    render_frames(out_dir, first, n)   frames of the exploded animation (tools/build_gif.py makes the GIF)

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
ASSEMBLED_TARGET = (0, 0, 14)


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


def frame_state(i, count):
    """Explode factor and camera swing of frame i: apart, hold, together, hold; the camera swings once."""
    phase = i / count
    if phase < 0.4:
        f = ease(phase / 0.4)
    elif phase < 0.5:
        f = 1.0
    elif phase < 0.9:
        f = 1.0 - ease((phase - 0.5) / 0.4)
    else:
        f = 0.0
    swing = math.radians(18) * math.sin(2 * math.pi * phase)
    return f, swing


def render_frames(out_dir, first, n, count=48, width=800, height=500):
    os.makedirs(out_dir, exist_ok=True)
    design = _design()
    root = design.rootComponent
    if first == 0:
        _prepare(design)
    _show(root, set(EXPLODE))
    (dx, dy, dz), target, zoom = EXPLODE_VIEW
    dist = []
    for f in (0.0, 1.0):   # camera distance that fits the assembled and the exploded device
        _explode(root, f)
        _camera((dx, dy, dz), target, 1.0)
        cam = adsk.core.Application.get().activeViewport.camera
        dist.append(cam.eye.distanceTo(cam.target))
    for i in range(first, min(first + n, count)):
        f, swing = frame_state(i, count)
        _explode(root, f)
        c, s = math.cos(swing), math.sin(swing)
        d = (dx * c - dz * s, dy, dx * s + dz * c)
        vp = adsk.core.Application.get().activeViewport
        cam = vp.camera
        cam.isSmoothTransition = False
        # camera follows the parts: close on the assembled device, wide on the exploded one
        t = [(a + (b - a) * f) / 10 for a, b in zip(ASSEMBLED_TARGET, target, strict=True)]
        norm = math.sqrt(sum(v * v for v in d))
        r = (dist[0] + (dist[1] - dist[0]) * f) * 1.05
        cam.target = adsk.core.Point3D.create(*t)
        cam.eye = adsk.core.Point3D.create(*(t[k] + r * d[k] / norm for k in range(3)))
        cam.upVector = adsk.core.Vector3D.create(0, 1, 0)
        vp.camera = cam
        vp.refresh()
        _save(os.path.join(out_dir, f'frame_{i:03d}.png'), width, height)
    if first + n >= count:
        _explode(root, 0)
