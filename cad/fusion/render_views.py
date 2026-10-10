"""
Renders for the documentation, run in Fusion after generate_enclosure.py (same open design).

    render_views(out_dir)              every still image of docs/images, 1600 x 1200, transparent
    render_hero(out_dir, first, n)     frames of the README animation (tools/build_gif.py makes the GIF)

The camera is given as a viewing direction in model coordinates (front z = 0, wall towards +z,
y up): the view is fitted to the visible parts and then zoomed. Reference parts are shown opaque.
"""
import math
import os

import adsk.core
import adsk.fusion

DEVICE = {'Housing', 'BackCover', 'Dummy_LCD_2inch'}
TILT = math.radians(12.0)   # desk stand: device leans back by TILT

# name: (visible components, view direction (eye - target), target in mm, zoom after fit, tilted with the stand)
VIEWS = {
    'hero_wall': (DEVICE | {'WallPlate'}, (-0.55, 0.30, -0.78), (0, 0, 15), 1.0, False),
    'desk_stand': (DEVICE | {'DeskStand', 'Dummy_Adapter'}, (-0.55, 0.22, -0.80), (0, -15, 25), 1.0, True),
    'interior': ({'Housing', 'SensorCarrier', 'Dummy_LCD_2inch', 'Dummy_SCD41', 'Dummy_ESP32_C3', 'Dummy_Adapter'},
                 (-0.20, 0.17, 0.96), (0, 0, 12), 1.0, False),
    'sensor_carrier_front': ({'SensorCarrier', 'Dummy_SCD41'}, (-0.55, 0.40, -0.73), (-3, -21, 10), 1.0, False),
    'sensor_carrier_back': ({'SensorCarrier', 'Dummy_ESP32_C3'}, (-0.30, 0.45, 0.84), (0, -12, 14), 1.0, False),
    'cable_port_back': ({'Housing', 'BackCover', 'Dummy_Adapter'}, (-0.40, -0.45, 0.80), (0, 0, 12), 0.9, False),
    'cable_port_bottom': ({'Housing', 'BackCover', 'Dummy_PlugStraight'}, (-0.35, -0.75, 0.56),
                          (0, 0, 12), 0.9, False),
    'vent_mesh': ({'Housing', 'BackCover'}, (-0.25, -0.85, -0.46), (0, -34, 8), 0.8, False),
}

EXPLODE_VIEW = ((-0.90, 0.30, -0.32), (0, -5, 40), 1.15)


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


def render_views(out_dir, names=None):
    os.makedirs(out_dir, exist_ok=True)
    design = _design()
    root = design.rootComponent
    _prepare(design)
    _place(root, {}, 0.0)
    adsk.core.Application.get().activeViewport.visualStyle = \
        adsk.core.VisualStyles.ShadedWithVisibleEdgesOnlyVisualStyle
    for name, (visible, direction, target, zoom, tilted) in VIEWS.items():
        if names and name not in names:
            continue
        _show(root, visible)
        _camera(direction, target, zoom, tilted)
        _save(os.path.join(out_dir, name + '.png'))
    # exploded view: the last frame of the README animation, every part on its collision-free path
    import json
    with open(HERO_MOTION, encoding='utf-8') as f:
        motion = json.load(f)
    _show(root, set(motion['ids']))
    _place(root, motion['parts'], 1.0)
    _camera(*EXPLODE_VIEW)
    _save(os.path.join(out_dir, 'exploded_view.png'))
    _place(root, motion['parts'], 0.0)


def ease(t):
    return 0.5 - 0.5 * math.cos(math.pi * t)


# ----------------------------------------------------------------------------- README animation
# The parts leave one after another along free paths (cad/fusion/hero_motion.json, checked for collisions by
# tools/assembly_check.py). Frames are rendered for t = 0 (assembled) to 1 (apart); tools/build_gif.py plays
# them forwards and backwards, so the device takes itself apart and assembles itself again.
HERO_MOTION = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hero_motion.json')
HERO_VIEW = (-0.90, 0.30, -0.32)        # viewing direction, as in the first README animation
HERO_TARGET = ((0, 0, 14), (0, -8, 42))  # look-at point assembled and apart
HERO_TURN = math.radians(16)            # the camera turns a little while the device opens


def _track(keys, t):
    if t <= keys[0][0]:
        return keys[0][1]
    for (t0, a), (t1, b) in zip(keys, keys[1:]):
        if t <= t1:
            u = ease((t - t0) / (t1 - t0)) if t1 > t0 else 1.0
            return [a[k] + (b[k] - a[k]) * u for k in range(3)]
    return keys[-1][1]


def _place(root, tracks, t):
    for occ in root.occurrences:
        keys = tracks.get(occ.component.name)
        x, y, z = _track(keys, t) if keys else (0, 0, 0)
        m = adsk.core.Matrix3D.create()
        m.translation = adsk.core.Vector3D.create(x / 10, y / 10, z / 10)
        occ.transform2 = m


def render_hero(out_dir, first, n, count=90, width=1600, height=1000):
    """Frames hero_XXX.png for t = i / (count - 1), rendered at twice the GIF size for clean edges."""
    import json
    os.makedirs(out_dir, exist_ok=True)
    app = adsk.core.Application.get()
    design = _design()
    root = design.rootComponent
    with open(HERO_MOTION, encoding='utf-8') as f:
        motion = json.load(f)
    tracks = motion['parts']
    if first == 0:
        _prepare(design)
    _show(root, set(motion['ids']))
    vp = app.activeViewport
    vp.visualStyle = adsk.core.VisualStyles.ShadedWithVisibleEdgesOnlyVisualStyle
    dist = []
    for t in (0.0, 1.0):   # camera distance that fits the assembled and the opened device
        _place(root, tracks, t)
        _camera(HERO_VIEW, HERO_TARGET[0], 1.0)
        cam = vp.camera
        dist.append(cam.eye.distanceTo(cam.target))
    for i in range(first, min(first + n, count)):
        t = i / (count - 1)
        _place(root, tracks, t)
        s = ease(min(1.0, t / 0.4))   # the wall plate and the cover travel furthest, and they leave first
        a = HERO_TURN * ease(t)
        dx, dy, dz = HERO_VIEW
        d = (dx * math.cos(a) - dz * math.sin(a), dy, dx * math.sin(a) + dz * math.cos(a))
        norm = math.sqrt(sum(v * v for v in d))
        target = [(p + (q - p) * s) / 10 for p, q in zip(*HERO_TARGET)]
        r = (dist[0] + (dist[1] - dist[0]) * s) * 1.04
        cam = vp.camera
        cam.isSmoothTransition = False
        cam.target = adsk.core.Point3D.create(*target)
        cam.eye = adsk.core.Point3D.create(*(target[k] + r * d[k] / norm for k in range(3)))
        cam.upVector = adsk.core.Vector3D.create(0, 1, 0)
        vp.camera = cam
        vp.refresh()
        _save(os.path.join(out_dir, f'hero_{i:03d}.png'), width, height)
    if first + n >= count:
        _place(root, tracks, 0.0)
