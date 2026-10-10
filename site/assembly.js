// Interactive 3D assembly guide of the CO2 Wall Sensor.
//
// The data comes from tools/assembly_model.py: the printed parts as STL files in their assembled
// position, the bought parts as simple boxes and cylinders built from the generator parameters,
// and the steps of site/assembly_steps.yaml. Coordinates in mm: front face z = 0, wall towards +z, y up.

import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { STLLoader } from 'three/addons/loaders/STLLoader.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { toCreasedNormals } from 'three/addons/utils/BufferGeometryUtils.js';

const LANG = document.documentElement.lang === 'de' ? 'de' : 'en';
const BASE = document.body.dataset.models;
const UI = {
  en: { step: (i, n) => `Step ${i} of ${n}`, next: 'Next', restart: 'Start over', play: '▶', pause: '❚❚', need: 'You need', tip: 'Tip' },
  de: { step: (i, n) => `Schritt ${i} von ${n}`, next: 'Weiter', restart: 'Von vorn', play: '▶', pause: '❚❚', need: 'Du brauchst', tip: 'Tipp' },
}[LANG];

const CAMERA_TIME = 1.3;   // s, camera move to the view of a step
const DRAW_TIME = 1.8;     // s, wires are drawn on
const AUTOPLAY_HOLD = 2.5; // s the finished step stays on screen while playing
const ACCENT = new THREE.Color('#ff7a1a');
const REDUCED = matchMedia('(prefers-reduced-motion: reduce)').matches;

const $ = (id) => document.getElementById(id);
const stageEl = $('stage');
const ease = (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
const clamp01 = (t) => Math.min(1, Math.max(0, t));
const v3 = (a) => new THREE.Vector3(a[0], a[1], a[2]);

// ----------------------------------------------------------------------------- scene
const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.05;
stageEl.prepend(renderer.domElement);

const scene = new THREE.Scene();
const pmrem = new THREE.PMREMGenerator(renderer);
scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
scene.environmentIntensity = 0.85;
const sun = new THREE.DirectionalLight(0xffffff, 1.6);
sun.position.set(-80, 140, -60);
scene.add(sun, new THREE.HemisphereLight(0xffffff, 0x8a8f96, 0.6));

const camera = new THREE.PerspectiveCamera(32, 1, 1, 3000);
camera.position.set(-90, 70, 170);
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.08;
controls.minDistance = 40;
controls.maxDistance = 600;
controls.target.set(0, 0, 12);

function resize() {
  const { clientWidth: w, clientHeight: h } = stageEl;
  renderer.setSize(w, h, false);
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
}
new ResizeObserver(resize).observe(stageEl);

// ----------------------------------------------------------------------------- materials and meshes
const MATERIAL = {
  print: { roughness: 0.78, metalness: 0.0 },
  plastic: { roughness: 0.55, metalness: 0.0 },
  metal: { roughness: 0.32, metalness: 0.9 },
  brass: { roughness: 0.3, metalness: 1.0 },
  rubber: { roughness: 0.9, metalness: 0.0 },
  glass: { roughness: 0.08, metalness: 0.3 },
};

function material(spec) {
  return new THREE.MeshStandardMaterial({ color: spec.color, ...MATERIAL[spec.mat || 'plastic'] });
}

function boxMesh(m) {
  const size = [0, 1, 2].map((i) => m.max[i] - m.min[i]);
  const mesh = new THREE.Mesh(new THREE.BoxGeometry(...size), material(m));
  mesh.position.set(...[0, 1, 2].map((i) => (m.min[i] + m.max[i]) / 2));
  return mesh;
}

function cylMesh(m) {
  const d = v3(m.d).normalize();
  const mesh = new THREE.Mesh(new THREE.CylinderGeometry(m.r, m.r, m.len, 28), material(m));
  mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), d);
  mesh.position.copy(v3(m.p).addScaledVector(d, m.len / 2));
  return mesh;
}

function tubeMesh(m) {
  const curve = new THREE.CatmullRomCurve3(m.points.map(v3), false, 'centripetal');
  const geo = new THREE.TubeGeometry(curve, Math.max(120, m.points.length * 2), m.r || 0.42, 8, false);
  const mesh = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ color: m.color, roughness: 0.45, transparent: true }));
  mesh.userData.wire = true;
  return mesh;
}

function screenMesh(m) {
  const tex = new THREE.TextureLoader().load(`${BASE}screen_${LANG}.png`);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.anisotropy = 8;
  const mesh = new THREE.Mesh(new THREE.PlaneGeometry(m.size[0], m.size[1]),
    new THREE.MeshBasicMaterial({ map: tex, toneMapped: false }));
  mesh.rotation.y = Math.PI;   // faces the front (-z); the left edge of the image lands at +x, left as seen from the front
  mesh.position.set(...m.centre);
  return mesh;
}

const stlLoader = new STLLoader();
const stlCache = new Map();
function loadStl(file) {
  if (!stlCache.has(file)) {
    stlCache.set(file, stlLoader.loadAsync(BASE + file).then((geo) => {
      geo.deleteAttribute('normal');
      return toCreasedNormals(geo, THREE.MathUtils.degToRad(28));
    }));
  }
  return stlCache.get(file);
}

async function stlMesh(m) {
  const geo = await loadStl(m.file);
  const mesh = new THREE.Mesh(geo, material(m));
  const edges = new THREE.LineSegments(new THREE.EdgesGeometry(geo, 32),
    new THREE.LineBasicMaterial({ color: 0x000000, transparent: true, opacity: 0.22 }));
  edges.userData.edges = true;
  mesh.add(edges);
  return mesh;
}

async function buildPart(spec) {
  const group = new THREE.Group();
  group.name = spec.id;
  for (const m of spec.meshes) {
    const mesh = m.type === 'stl' ? await stlMesh(m)
      : m.type === 'box' ? boxMesh(m)
      : m.type === 'cyl' ? cylMesh(m)
      : m.type === 'tube' ? tubeMesh(m)
      : screenMesh(m);
    mesh.userData.part = spec.id;
    group.add(mesh);
  }
  group.visible = false;
  scene.add(group);
  return {
    spec, group,
    glow: spec.meshes.some((m) => m.type === 'stl') ? 0.14 : 0.3,   // large printed parts glow less
    base: new THREE.Vector3(),   // offset from the assembled position (stage and fly-in), without the explode
    path: null,                  // {points, t0, duration}: travelled at constant speed with ease in and out
    shown: false,
    wires: group.children.filter((c) => c.userData.wire),
    materials: group.children.filter((c) => c.material && !c.userData.wire && c.material.emissive).map((c) => c.material),
  };
}

// ----------------------------------------------------------------------------- motion
// The same rules as tools/assembly_check.py, which replays every motion and proves that no part passes
// through another one. Change both together.
let data, parts = {}, current = -1, explode = 0, xray = false, playing = 0;
let anim = { t0: 0, camT0: 0, camFrom: null, camTo: null, draw: [], end: 0 };
const clock = new THREE.Clock();

function introStep(id) {
  return data.steps.findIndex((s) => (s.new || []).includes(id));
}

function stageWaypoints(part, stage) {
  const s = data.stages[stage || ''] || {};
  const g = part.spec.groups.find((name) => s[name]);
  return g ? s[g].map(v3) : [];
}

function stageEnd(part, stage) {
  const w = stageWaypoints(part, stage);
  return w.length ? w[w.length - 1] : new THREE.Vector3();
}

function stagePath(part, a, b) {
  // back along the waypoints of stage a, then out along those of stage b
  const wa = stageWaypoints(part, a), wb = stageWaypoints(part, b);
  if (a === b || (!wa.length && !wb.length)) return [stageEnd(part, b)];
  const pts = [stageEnd(part, a), ...wa.slice(0, -1).reverse(), new THREE.Vector3(), ...wb];
  return pts.filter((p, i) => i === 0 || p.distanceTo(pts[i - 1]) > 1e-9);
}

function pathLength(points) {
  let l = 0;
  for (let i = 1; i < points.length; i++) l += points[i].distanceTo(points[i - 1]);
  return l;
}

function pathDuration(points) {
  return points.length > 1 ? Math.max(data.timing.min_time, pathLength(points) / data.timing.speed) : 0;
}

function pointAt(points, u) {
  let s = u * pathLength(points);
  for (let i = 1; i < points.length; i++) {
    const seg = points[i].distanceTo(points[i - 1]);
    if (s <= seg) return points[i - 1].clone().lerp(points[i], seg ? s / seg : 1);
    s -= seg;
  }
  return points[points.length - 1].clone();
}

function goTo(index, { instant = false } = {}) {
  index = Math.max(0, Math.min(data.steps.length - 1, index));
  const step = data.steps[index];
  const prevStage = current >= 0 ? data.steps[current].stage || '' : step.stage || '';
  const stage = step.stage || '';
  const fresh = new Set(step.new || []);
  const animate = !instant && !REDUCED;
  // 1. the parts already in place follow their stage waypoints
  let tStage = 0;
  for (const part of Object.values(parts)) {
    const intro = introStep(part.spec.id);
    if (intro < 0 || intro >= index || !part.shown) continue;
    const points = stagePath(part, prevStage, stage);
    points[0] = part.base.clone();
    part.path = { points, t0: 0, duration: pathDuration(points) };
    tStage = Math.max(tStage, part.path.duration);
  }
  // 2. then the new parts fly in, one after the other
  let start = tStage + data.timing.pause;
  for (const part of Object.values(parts)) {
    const id = part.spec.id;
    const intro = introStep(id);
    if (intro > index || intro < 0) {
      part.shown = false;
      part.path = null;
      part.base.set(0, 0, 0);
    } else if (intro < index && !part.shown) {
      part.shown = true;   // jumped over its step: appears in place
      part.base.copy(stageEnd(part, stage));
      part.path = null;
    }
  }
  for (const id of step.new || []) {
    const part = parts[id];
    const end = stageEnd(part, stage);
    const off = (step.from_part || {})[id] || step.from;
    const points = off && animate ? [end.clone().add(v3(off)), end] : [end];
    part.path = { points, t0: start, duration: pathDuration(points) };
    part.base.copy(points[0]);
    part.shown = !animate;
    start += part.path.duration + data.timing.pause;
  }
  if (!animate) {
    for (const part of Object.values(parts)) {
      if (part.path) part.base.copy(part.path.points[part.path.points.length - 1]);
      part.path = null;
      if (introStep(part.spec.id) >= 0 && introStep(part.spec.id) <= index) part.shown = true;
    }
  }
  // 3. wires: drawn on in their step after everything else has moved, complete afterwards
  anim.draw = [];
  for (const part of Object.values(parts)) {
    if (!part.wires.length) continue;
    const draw = step.draw && fresh.has(part.spec.id) && animate;
    part.wires.forEach((w, i) => {
      const count = w.geometry.index.count;
      w.geometry.setDrawRange(0, draw ? 0 : count);
      if (draw) anim.draw.push({ mesh: w, count, delay: start + i * 0.09 });
    });
  }
  anim.end = animate ? start + (step.draw ? DRAW_TIME + 1.2 : 0) : 0;
  current = index;
  anim.t0 = clock.getElapsedTime();
  flyCamera(step.camera, !animate);
  if (!animate) camera.lookAt(controls.target);
  render();
  updatePanel();
  if (playing) schedule();
}

// take apart: one move after the other, only the moves of the parts on screen
function explodeOffsets() {
  const out = new Map();
  if (explode <= 0) return out;
  const moves = data.explode.filter((m) => Object.keys(m).some((id) => parts[id] && parts[id].shown));
  const n = moves.length;
  moves.forEach((move, k) => {
    const u = ease(clamp01(explode * n - k));
    if (u <= 0) return;
    for (const [id, v] of Object.entries(move)) {
      if (!out.has(id)) out.set(id, new THREE.Vector3());
      out.get(id).addScaledVector(v3(v), u);
    }
  });
  return out;
}

function cameraFor(cam) {
  // narrow screens: step back so the parts stay in the picture
  const eye = v3(cam.eye), target = v3(cam.target);
  const f = camera.aspect < 1.2 ? Math.min(1.9, 1.2 / camera.aspect) : 1;
  eye.sub(target).multiplyScalar(f).add(target);
  return { eye, target };
}

function flyCamera(cam, instant) {
  const to = cameraFor(cam);
  if (instant || REDUCED) {
    camera.position.copy(to.eye);
    controls.target.copy(to.target);
    anim.camFrom = null;
    return;
  }
  anim.camFrom = { eye: camera.position.clone(), target: controls.target.clone() };
  anim.camTo = to;
  anim.camT0 = clock.getElapsedTime();
}

controls.addEventListener('start', () => { anim.camFrom = null; hideHint(); });

// ----------------------------------------------------------------------------- frame loop
function tick() {
  const now = clock.getElapsedTime();
  const dt = now - anim.t0;
  const exploded = explodeOffsets();
  for (const part of Object.values(parts)) {
    if (part.path) {
      const { points, t0, duration } = part.path;
      if (dt >= t0) {
        part.shown = true;
        const u = duration > 0 ? clamp01((dt - t0) / duration) : 1;
        part.base.copy(pointAt(points, ease(u)));
        if (u >= 1) part.path = null;
      }
    }
    part.group.visible = part.shown;
    part.group.position.copy(part.base);
    if (exploded.has(part.spec.id)) part.group.position.add(exploded.get(part.spec.id));
    // the parts of the current step light up while they arrive, then fade so the true colours stay visible
    const fresh = (data.steps[current].new || []).includes(part.spec.id);
    const since = part.path ? 0 : dt - (anim.end || 0);
    const glow = fresh ? part.glow * (0.6 + 0.4 * Math.sin(now * 5)) * clamp01((3 - Math.max(0, since)) / 1.2) : 0;
    for (const m of part.materials) {
      m.emissive.copy(ACCENT);
      m.emissiveIntensity = glow;
    }
    for (const w of part.wires) {
      w.material.opacity = 1 - clamp01(explode * 12);
      w.visible = part.shown && w.material.opacity > 0.01;
    }
  }
  for (const d of anim.draw) {
    const t = clamp01((dt - d.delay) / DRAW_TIME);
    d.mesh.geometry.setDrawRange(0, Math.floor(ease(t) * d.count / 3) * 3);
  }
  if (anim.camFrom) {
    const t = ease(clamp01((now - anim.camT0) / CAMERA_TIME));
    camera.position.lerpVectors(anim.camFrom.eye, anim.camTo.eye, t);
    controls.target.lerpVectors(anim.camFrom.target, anim.camTo.target, t);
    if (t >= 1) anim.camFrom = null;
  }
  controls.update();
  renderer.render(scene, camera);
}

let raf = 0;
function loop() {
  raf = requestAnimationFrame(loop);
  tick();
}
function render() {
  if (!raf) loop();
}

// ----------------------------------------------------------------------------- panel
const list = $('list');
function updatePanel() {
  const step = data.steps[current];
  const n = data.steps.length;
  $('count').textContent = UI.step(current + 1, n);
  $('step-title').textContent = step.title[LANG];
  $('step-text').textContent = step.text[LANG];
  const plain = (s) => (s || '').replace(/\[([^\]]+)\]\([^)]+\)/g, '$1');   // markdown links to plain text
  $('step-need').replaceChildren(Object.assign(document.createElement('b'), { textContent: UI.need + ': ' }),
    plain(step.need && step.need[LANG]));
  $('step-tip').textContent = step.tip ? `${UI.tip}: ${plain(step.tip[LANG])}` : '';
  $('badge').textContent = current + 1;
  $('progress').style.width = `${((current + 1) / n) * 100}%`;
  $('chips').replaceChildren(...(step.new || []).map((id) => {
    const li = document.createElement('li');
    li.textContent = parts[id].spec.name[LANG];
    return li;
  }));
  $('prev').disabled = current === 0;
  $('next').textContent = current === n - 1 ? UI.restart : UI.next;
  [...list.children].forEach((li, i) => {
    li.className = i < current ? 'done' : i === current ? 'now' : '';
    li.firstChild.setAttribute('aria-current', i === current ? 'step' : 'false');
  });
  if (list.scrollHeight > list.clientHeight + 4) {   // only the list scrolls, never the page
    const li = list.children[current];
    list.scrollTo({ top: li.offsetTop - list.clientHeight / 2, behavior: REDUCED ? 'auto' : 'smooth' });
  }
  history.replaceState(null, '', `#step-${current + 1}`);
}

function next() {
  goTo(current === data.steps.length - 1 ? 0 : current + 1);
}

function schedule() {
  clearTimeout(playing);
  playing = setTimeout(next, (Math.max(anim.end, CAMERA_TIME) + AUTOPLAY_HOLD) * 1000);
}

function setPlaying(on) {
  clearTimeout(playing);
  playing = 0;
  if (on) schedule();
  $('play').textContent = on ? UI.pause : UI.play;
}

function hideHint() {
  $('hint').style.opacity = 0;
}

function bindUi() {
  data.steps.forEach((s, i) => {
    const li = document.createElement('li');
    const b = document.createElement('button');
    b.textContent = s.title[LANG];
    b.addEventListener('click', () => { setPlaying(false); goTo(i); });
    li.append(b);
    list.append(li);
  });
  $('next').addEventListener('click', () => { setPlaying(false); next(); });
  $('prev').addEventListener('click', () => { setPlaying(false); goTo(current - 1); });
  $('play').addEventListener('click', () => {
    if (!playing && current === data.steps.length - 1) goTo(0);
    setPlaying(!playing);
  });
  $('view').addEventListener('click', () => flyCamera(data.steps[current].camera, false));
  $('explode').addEventListener('input', (e) => { explode = +e.target.value; hideHint(); });
  $('xray').addEventListener('change', (e) => setXray(e.target.checked));
  document.addEventListener('keydown', (e) => {
    if (e.target.tagName === 'INPUT') return;
    if (e.key === 'ArrowRight' || e.key === ' ') { e.preventDefault(); setPlaying(false); next(); }
    if (e.key === 'ArrowLeft') { setPlaying(false); goTo(current - 1); }
  });
  setTimeout(hideHint, 9000);
}

function setXray(on) {
  xray = on;
  $('xray').checked = on;
  for (const id of ['housing', 'cover', 'wall_plate']) {
    parts[id].group.traverse((o) => {
      if (!o.material) return;
      if (o.userData.edges) { o.material.opacity = on ? 0.35 : 0.22; return; }
      o.material.transparent = on;
      o.material.opacity = on ? 0.18 : 1;
      o.material.depthWrite = !on;
      o.material.needsUpdate = true;
    });
  }
}

// part names under the pointer
const raycaster = new THREE.Raycaster();
const pointer = new THREE.Vector2();
const tip = $('tip');
let tipTimer = 0;
renderer.domElement.addEventListener('pointermove', (e) => {
  if (e.buttons || !data) return;
  cancelAnimationFrame(tipTimer);
  tipTimer = requestAnimationFrame(() => {
    const r = renderer.domElement.getBoundingClientRect();
    pointer.set(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1);
    raycaster.setFromCamera(pointer, camera);
    const targets = Object.values(parts).filter((p) => p.group.visible).map((p) => p.group);
    const hits = raycaster.intersectObjects(targets, true).filter((h) => !h.object.userData.edges && h.object.visible
      && !(xray && ['housing', 'cover', 'wall_plate'].includes(h.object.userData.part)));
    if (hits.length) {
      tip.textContent = parts[hits[0].object.userData.part].spec.name[LANG];
      tip.style.left = `${e.clientX - r.left}px`;
      tip.style.top = `${e.clientY - r.top}px`;
      tip.style.opacity = 1;
    } else {
      tip.style.opacity = 0;
    }
  });
});
renderer.domElement.addEventListener('pointerleave', () => { tip.style.opacity = 0; });

// ----------------------------------------------------------------------------- start
async function main() {
  resize();
  data = await (await fetch(`${BASE}assembly.json`)).json();
  const built = await Promise.all(data.parts.map(buildPart));
  for (const p of built) parts[p.spec.id] = p;
  bindUi();
  const m = location.hash.match(/step-(\d+)/);
  const start = m ? +m[1] - 1 : 0;
  if (start === 0) {   // the first part flies in
    flyCamera(data.steps[0].camera, true);
    goTo(0);
  } else {
    goTo(start, { instant: true });
  }
  $('loading').classList.add('done');
  window.assemblyGuide = { goTo, setExplode: (v) => { explode = v; $('explode').value = v; }, setXray, parts, data, camera, controls };
}

main().catch((err) => {
  console.error(err);
  $('loading').textContent = String(err);
});
