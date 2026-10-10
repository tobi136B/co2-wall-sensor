// Sensor carrier of the CO2 Wall Sensor, built in the browser.
//
// The same features in the same order as build_sensor_carrier() in
// cad/fusion/generate_enclosure/generate_enclosure.py. The enclosure values come from
// carrier_params.json (written by tools/build_site.py from the generator), only the six
// SCD41 values and what follows from them are computed here. tools/configurator_check.py
// compares the result with the Fusion export of every known board in the CI.
//
// Coordinates in mm as in the generator: front face z = 0, wall towards +z, y up.

/** The values that follow from the SCD41 board (same formulas as derive() in the generator). */
export function deriveBoard(base, board) {
  const p = { ...base, ...board };
  p.SCD_Y0 = p.Y_CHIN_LOW + 0.2 + p.SCD_STOP + 0.15;
  p.SCD_TOP = p.SCD_Y0 + p.SCD_L;
  p.SCD_ZT = p.FLOOR_Z;
  p.HOOK_B = p.SCD_TOP - p.SPRING_PRELOAD;
  p.HOOK_C = p.HOOK_B + p.SPRING_HOOK;
  p.HOOK_A = p.HOOK_C + p.SPRING_HOOK;
  p.TONGUE_TIP = p.HOOK_A + 0.1;
  p.TONGUE_ROOT = p.TONGUE_TIP - p.SPRING_L;
  return p;
}

/** Problems that keep a board out of the sensor chamber (same rules as check_scd_fit()). */
export function checkBoard(base, board) {
  const p = deriveBoard(base, board);
  const problems = [];
  if (p.TONGUE_TIP > p.Y_DIV_LOW - 0.2) problems.push("length");
  if (p.SCD_W / 2 + 1.35 > p.XR - 6.0) problems.push("width");
  if (p.SCD_ZT - p.SCD_PCB - p.SCD_H < p.WALL + 0.5) problems.push("height");
  return problems;
}

function ccw(points) {
  let area = 0;
  for (let i = 0; i < points.length; i++) {
    const [x0, y0] = points[i];
    const [x1, y1] = points[(i + 1) % points.length];
    area += x0 * y1 - x1 * y0;
  }
  return area < 0 ? points.slice().reverse() : points;
}

/** Build the carrier. wasm is the initialised manifold-3d module. Returns a Manifold. */
export function buildCarrier(wasm, base, board) {
  const { Manifold, CrossSection } = wasm;
  const p = deriveBoard(base, board);
  const SEG = 48;

  // Boxes are 2 micrometres larger on every side: faces that Fusion merges because they lie exactly in one
  // plane then overlap a little, and the mesh stays watertight (no edges that only touch).
  const E = 0.002;
  const box = (x0, y0, z0, x1, y1, z1) =>
    Manifold.cube([Math.abs(x1 - x0) + 2 * E, Math.abs(y1 - y0) + 2 * E, Math.abs(z1 - z0) + 2 * E]).translate([
      Math.min(x0, x1) - E, Math.min(y0, y1) - E, Math.min(z0, z1) - E,
    ]);
  // polygon (x, z) in the XZ plane, extruded along y from y0 to y1
  const prismY = (pts, y0, y1) =>
    Manifold.extrude(new CrossSection([ccw(pts)]), y1 - y0).rotate([90, 0, 0]).translate([0, y1, 0]);
  // polygon (y, z) in the YZ plane, extruded along x from x0 to x1
  const prismX = (pts, x0, x1) =>
    Manifold.extrude(new CrossSection([ccw(pts)]), x1 - x0)
      .transform([0, 1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, x0, 0, 0, 1]);
  const cylZ = (centres, d, z0, z1) =>
    Manifold.union(centres.map(([x, y]) => Manifold.cylinder(z1 - z0, d / 2, d / 2, SEG).translate([x, y, z0])));

  let body;
  const add = (m) => { body = body.add(m); };
  const cut = (m) => { body = body.subtract(m); };

  const s = 0.2;
  const yLo = p.Y_CHIN_LOW + s, yHi = p.Y_DIV_LOW - s;
  body = box(p.XL + s, yLo, p.FLOOR_Z, p.XR - s, yHi, p.FLOOR_Z + p.FLOOR_T);
  // notches around the two full-height cover bosses
  let r = p.BOSS_D / 2 + 0.3 + p.BOSS_FILLET;
  for (const [x, y] of p.COVER_SCREWS.slice(0, 2)) cut(box(x - r, y - r - 2, p.FLOOR_Z - 2, x + r, y + r, p.FLOOR_Z + p.FLOOR_T + 1));
  cut(cylZ(p.CARRIER_SCREWS, p.SCREW_CLEAR_D, p.FLOOR_Z + p.FLOOR_T - 10, p.FLOOR_Z + p.FLOOR_T + 0.1));

  // SCD41 rails with end stop
  const zb = p.SCD_ZT - p.SCD_PCB, g = 0.15, zLip = zb - g - p.SCD_LIP;
  const yc = p.SCD_Y0 + p.SCD_L / 2;
  for (const sx of [-1, 1]) {
    const xIn = p.SCD_W / 2 - p.SCD_LIP, xEdge = p.SCD_W / 2 + g, xOut = p.SCD_W / 2 + g + 1.2;
    add(prismY([[sx * xIn, zLip], [sx * xOut, zLip], [sx * xOut, p.FLOOR_Z], [sx * xEdge, p.FLOOR_Z],
      [sx * xEdge, zb - g], [sx * xIn, zb - g]], yLo, yHi));
    add(box(sx * xIn, yLo, zLip, sx * xOut, p.SCD_Y0 - g, p.FLOOR_Z));
  }
  if (Math.abs(p.SCD_PAD_X) > 1e-6) {
    const padX = -p.SCD_PAD_X, sx = padX > 0 ? 1 : -1;
    const xa = sx * (p.SCD_W / 2 - p.SCD_LIP - 0.1), xb = sx * (p.SCD_W / 2 + g);
    cut(box(Math.min(xa, xb), yc - 4.8, zLip - 0.1, Math.max(xa, xb), yc + 4.8, zb - g + 0.01));
    cut(box(padX - 1.2, yLo - 0.1, p.FLOOR_Z - 0.01, padX + 1.2, p.SCD_TOP + 1.0, p.FLOOR_Z + 0.6));
  }
  // spring tongue
  const hw = p.SPRING_W / 2;
  for (const [x0, x1] of [[p.SPRING_X - hw - 0.6, p.SPRING_X - hw], [p.SPRING_X + hw, p.SPRING_X + hw + 0.6]])
    cut(box(x0, p.TONGUE_ROOT, p.FLOOR_Z - 1, x1, p.TONGUE_TIP + 0.6, p.FLOOR_Z + p.FLOOR_T + 1));
  cut(box(p.SPRING_X - hw - 0.6, p.TONGUE_TIP, p.FLOOR_Z - 1, p.SPRING_X + hw + 0.6, p.TONGUE_TIP + 0.6, p.FLOOR_Z + p.FLOOR_T + 1));
  cut(box(p.SPRING_X - hw, p.TONGUE_ROOT + 1.0, p.FLOOR_Z + p.SPRING_T, p.SPRING_X + hw, p.TONGUE_TIP + 0.1, p.FLOOR_Z + p.FLOOR_T + 1));
  add(prismX([[p.HOOK_B, p.FLOOR_Z + 0.01], [p.HOOK_C, p.FLOOR_Z - p.SPRING_HOOK], [p.HOOK_A, p.FLOOR_Z + 0.01]],
    p.SPRING_X - hw, p.SPRING_X + hw));
  // pocket for the body of the 90 degree adapter
  r = p.ADAPTER_W / 2 + 0.5;
  cut(box(p.C3_X - r, yLo - 0.1, p.FLOOR_Z + p.MIN_WALL, p.C3_X + r, p.C3_Y0 - 1.3, p.FLOOR_Z + p.FLOOR_T + 1.0));
  // SCD41 wires: narrow slot and wire channel with snap lip
  const slotX = -(p.SCD_W / 2 + g + 1.2 + p.MIN_WALL + p.SCD_SLOT_W / 2);
  cut(box(slotX - p.SCD_SLOT_W / 2, yHi - 4.0, p.FLOOR_Z - 0.5, slotX + p.SCD_SLOT_W / 2, yHi + 0.1, p.FLOOR_Z + p.FLOOR_T + 0.5));
  let top = p.FLOOR_Z + p.FLOOR_T;
  const yw = p.Y_DIV_LOW - p.SCD_CHANNEL_W, hc = 2.5;
  const cx0 = slotX + p.SCD_SLOT_W / 2 + p.MIN_WALL, cx1 = p.SPRING_X - p.SPRING_W / 2 - 1.6;
  if (cx1 - cx0 > 2.0) {
    add(prismX([[yw - hc - 1.0, top - 0.01], [yw - 1.0, top + hc], [yw, top + hc], [yw, top - 0.01]], cx0, cx1));
    add(box(cx0, yw - 0.01, top + hc - p.CLIP_LIP, cx1, yw + p.CLIP_LIP, top + hc));
  }

  // ESP32-C3: ribs, sled above the divider, guides over the whole length, end stops, grooves
  top = p.FLOOR_Z + p.FLOOR_T;
  const gx = p.C3_W / 2 + p.C3_PLAY, wall = 1.15;
  for (const x of [p.C3_X - 6, p.C3_X + 6]) add(box(x - 0.75, p.C3_Y0, top, x + 0.75, yHi, p.C3_Z0));
  add(box(p.C3_X - gx - wall, yHi - 0.01, p.EXT_Z0, p.C3_X + gx + wall, p.C3_EXT_Y1, p.C3_Z0));
  const zGuide = p.C3_Z0 + p.C3_PCB_MAX + 0.5;
  for (const [x0, x1] of [[p.C3_X - gx - wall, p.C3_X - gx], [p.C3_X + gx, p.C3_X + gx + wall]])
    add(box(x0, p.C3_Y0 - 1.2, p.EXT_Z0, x1, p.C3_TOP + 0.5, zGuide));
  const rr = 0.6;
  const ribs = [];
  for (const sx of [-1, 1]) for (const y of [p.C3_Y0 + 4.0, p.C3_TOP - 3.0]) ribs.push([p.C3_X + sx * (gx - p.C3_RIB + rr), y]);
  add(cylZ(ribs, 2 * rr, p.EXT_Z0, zGuide));
  for (const [x0, x1] of [[p.C3_X - gx, p.C3_X - p.C3_W / 2 + 1.5], [p.C3_X + p.C3_W / 2 - 1.5, p.C3_X + gx]])
    add(box(x0, p.C3_Y0 - 1.2, top, x1, p.C3_Y0 - 0.05, p.C3_Z0 + p.C3_PCB));
  const zl = p.C3_Z0 + p.C3_PCB_MAX + 0.1;
  for (const sx of [-1, 1]) {
    const xa = p.C3_X + sx * (p.C3_W / 2 - 0.5), xb = p.C3_X + sx * gx;
    add(box(Math.min(xa, xb), p.C3_Y0 - 0.05, top, Math.max(xa, xb), p.C3_Y0 + 1.2, p.C3_Z0));
    const la = p.C3_X + sx * (p.C3_W / 2 - 0.6), lb = p.C3_X + sx * (gx + wall);
    add(box(Math.min(la, lb), p.C3_Y0 - 0.05, zl, Math.max(la, lb), p.C3_Y0 + 1.2, zl + p.MIN_WALL + 0.1));
  }
  // spring tongue with hook behind the upper board edge
  const h3 = p.SPRING_W / 2;
  for (const [x0, x1] of [[p.C3_X - h3 - 0.6, p.C3_X - h3], [p.C3_X + h3, p.C3_X + h3 + 0.6]])
    cut(box(x0, p.C3_ROOT, p.EXT_Z0 - 1, x1, p.C3_TIP + 0.6, p.C3_Z0 + 1));
  cut(box(p.C3_X - h3 - 0.6, p.C3_TIP, p.EXT_Z0 - 1, p.C3_X + h3 + 0.6, p.C3_TIP + 0.6, p.C3_Z0 + 1));
  cut(box(p.C3_X - h3, p.C3_ROOT + 1.0, p.EXT_Z0 - 1, p.C3_X + h3, p.C3_TIP + 0.1, p.C3_Z0 - p.SPRING_T));
  add(prismX([[p.C3_HOOK_Y, p.C3_Z0 - 0.01], [p.C3_HOOK_Y, p.C3_Z0 + p.C3_HOOK], [p.C3_HOOK_Y + 0.3, p.C3_Z0 + p.C3_HOOK],
    [p.C3_HOOK_Y + 0.31 + p.C3_HOOK, p.C3_Z0 - 0.01]], p.C3_X - h3, p.C3_X + h3));
  // bridge for the display cable
  const zc = p.C3_Z0 + p.BRIDGE_H, xp = gx + wall + 0.3;
  add(box(p.C3_X - xp - 1.2, p.BRIDGE_Y0, p.EXT_Z0, p.C3_X + xp + 1.2, p.C3_EXT_Y1, p.C3_Z0));
  const post = [[p.BRIDGE_Y0, p.C3_Z0 - 0.01], [p.BRIDGE_Y0 + p.BRIDGE_H, zc], [p.C3_EXT_Y1, zc], [p.C3_EXT_Y1, p.C3_Z0 - 0.01]];
  for (const sx of [-1, 1]) {
    const xa = p.C3_X + sx * xp, xb = p.C3_X + sx * (xp + 1.2);
    add(prismX(post, Math.min(xa, xb), Math.max(xa, xb)));
  }
  add(box(p.C3_X - xp - 0.01, p.BRIDGE_Y0 + p.BRIDGE_H, zc - p.BRIDGE_BAR, p.C3_X + xp + 0.01, p.C3_EXT_Y1, zc));
  return body;
}

/** Index map that joins the duplicated vertices manifold-3d keeps along property seams (watertight output). */
export function mergedIndex(mesh) {
  const map = new Map();
  const from = mesh.mergeFromVert || [], to = mesh.mergeToVert || [];
  for (let i = 0; i < from.length; i++) map.set(from[i], to[i]);
  return (v) => (map.has(v) ? map.get(v) : v);
}

/**
 * Binary STL of a Manifold. In print orientation (default) the lower edge (-y) lies on the bed, like in the
 * 3MF plates; with printOrientation = false the part stays in the model coordinates of cad/stl.
 */
export function toStl(manifold, name = "sensor_carrier", printOrientation = true) {
  let placed = manifold;
  if (printOrientation) {
    // rotate +90 degrees about x (lower edge onto the bed), then move it onto z = 0
    const turned = manifold.rotate([90, 0, 0]);
    const bb = turned.boundingBox();
    placed = turned.translate([-(bb.min[0] + bb.max[0]) / 2, -(bb.min[1] + bb.max[1]) / 2, -bb.min[2]]);
  }
  const mesh = placed.getMesh();
  const at = mergedIndex(mesh);
  const n = mesh.triVerts.length / 3, np = mesh.numProp, v = mesh.vertProperties;
  const buf = new ArrayBuffer(84 + 50 * n);
  const dv = new DataView(buf);
  const header = `${name} - CO2 Wall Sensor configurator`.slice(0, 80);
  for (let i = 0; i < header.length; i++) dv.setUint8(i, header.charCodeAt(i));
  dv.setUint32(80, n, true);
  let o = 84;
  for (let t = 0; t < n; t++) {
    const P = [0, 1, 2].map((k) => {
      const i = at(mesh.triVerts[3 * t + k]) * np;
      return [v[i], v[i + 1], v[i + 2]];
    });
    const a = P[1].map((c, i) => c - P[0][i]), b = P[2].map((c, i) => c - P[0][i]);
    const nx = a[1] * b[2] - a[2] * b[1], ny = a[2] * b[0] - a[0] * b[2], nz = a[0] * b[1] - a[1] * b[0];
    const len = Math.hypot(nx, ny, nz) || 1;
    for (const c of [nx / len, ny / len, nz / len]) { dv.setFloat32(o, c, true); o += 4; }
    for (const q of P) for (const c of q) { dv.setFloat32(o, c, true); o += 4; }
    dv.setUint16(o, 0, true); o += 2;
  }
  return buf;
}
