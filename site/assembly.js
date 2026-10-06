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
  en: { step: (i, n) => `Step ${i} of ${n}`, next: 'Next', restart: 'Start over', play: '▶', pause: '❚❚' },
  de: { step: (i, n) => `Schritt ${i} von ${n}`, next: 'Weiter', restart: 'Von vorn', play: '▶', pause: '❚❚' },
}[LANG];

const FLY_TIME = 1.1;      // s, a new part flies into place
const STAGGER = 0.16;      // s between parts of the same step
const CAMERA_TIME = 1.3;   // s, camera move to the view of a step
const DRAW_TIME = 1.8;     // s, wires are drawn on
const AUTOPLAY = 5.5;      // s per step
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
  const geo = new THREE.TubeGeometry(curve, 120, 0.42, 8, false);
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
    spec, group, explode: v3(spec.explode),
    glow: spec.meshes.some((m) => m.type === 'stl') ? 0.14 : 0.3,   // large printed parts glow less
    base: new THREE.Vector3(), path: null, // base offset (stage plus fly-in), animated along path
    wires: group.children.filter((c) => c.userData.wire),
    materials: group.children.filter((c) => c.material && !c.userData.wire && c.material.emissive).map((c) => c.material),
  };
}

// ----------------------------------------------------------------------------- state
let data, parts = {}, current = -1, explode = 0, xray = false, playing = null;
let anim = { t0: 0, camT0: 0, camFrom: null, camTo: null, draw: [] };
const clock = new THREE.Clock();

function introStep(id) {
  return data.steps.findIndex((s) => (s.new || []).includes(id));
}

function stageOffset(part, stage) {
  const off = new THREE.Vector3();
  const s = data.stages[stage] || {};
  for (const g of part.spec.groups) if (s[g]) off.add(v3(s[g]));
  return off;
}

function pathTo(part, end, startOffset = null, delay = 0) {
  const from = startOffset ? end.clone().add(startOffset) : part.base.clone();
  part.path = { points: [from, end], delay };
}

function goTo(index, { instant = false } = {}) {
  index = Math.max(0, Math.min(data.steps.length - 1, index));
  const step = data.steps[index];
  const forward = index === current + 1;
  const stage = step.stage || '';
  let k = 0;
  for (const part of Object.values(parts)) {
    const intro = introStep(part.spec.id);
    const visible = intro >= 0 && intro <= index;
    const wasVisible = part.group.visible;
    part.group.visible = visible;
    if (!visible) continue;
    const end = stageOffset(part, stage);
    if (step.slide && part.spec.groups.includes('device')) {
      part.path = { points: [part.base.clone(), v3(data.slide.engage), end], delay: 0 };
    } else if (intro === index && (forward || !wasVisible) && step.from) {
      pathTo(part, end, v3(step.from), STAGGER * k++);
    } else {
      pathTo(part, end);
    }
    if (instant || REDUCED) {
      part.base.copy(end);
      part.path = null;
    }
  }
  // wires: drawn on in their step, complete afterwards
  anim.draw = [];
  for (const part of Object.values(parts)) {
    if (!part.wires.length) continue;
    const draw = step.draw && (step.new || []).includes(part.spec.id) && !instant && !REDUCED;
    part.wires.forEach((w, i) => {
      const count = w.geometry.index.count;
      w.geometry.setDrawRange(0, draw ? 0 : count);
      if (draw) anim.draw.push({ mesh: w, count, delay: 0.35 + i * 0.09 });
    });
  }
  current = index;
  anim.t0 = clock.getElapsedTime();
  flyCamera(step.camera, instant);
  if (instant) camera.lookAt(controls.target);
  render();
  updatePanel();
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
function along(points, t) {
  if (points.length === 2) return points[0].clone().lerp(points[1], t);
  // two legs: first onto the rail, then down the rail
  const u = t * 2;
  return u < 1 ? points[0].clone().lerp(points[1], ease(u)) : points[1].clone().lerp(points[2], ease(u - 1));
}

function tick() {
  const now = clock.getElapsedTime();
  const dt = now - anim.t0;
  let busy = false;
  for (const part of Object.values(parts)) {
    if (part.path) {
      const { points, delay } = part.path;
      const duration = points.length === 3 ? FLY_TIME * 2 : FLY_TIME;
      const t = clamp01((dt - delay) / duration);
      part.base.copy(points.length === 3 ? along(points, t) : along(points, ease(t)));
      if (t >= 1) part.path = null;
      busy = true;
    }
    part.group.position.copy(part.base).addScaledVector(part.explode, explode * 1.0);
    // the parts of the current step light up
    const fresh = (data.steps[current].new || []).includes(part.spec.id);
    // flashes while it arrives, then fades so the true colours stay visible
    const glow = fresh ? part.glow * (0.6 + 0.4 * Math.sin(dt * 5)) * clamp01((4 - dt) / 1.2) : 0;
    for (const m of part.materials) {
      m.emissive.copy(ACCENT);
      m.emissiveIntensity = glow;
    }
    for (const w of part.wires) {
      w.material.opacity = 1 - clamp01(explode * 6);
      w.visible = w.material.opacity > 0.01;
    }
  }
  for (const d of anim.draw) {
    const t = clamp01((dt - d.delay) / DRAW_TIME);
    d.mesh.geometry.setDrawRange(0, Math.floor(ease(t) * d.count / 3) * 3);
    if (t < 1) busy = true;
  }
  if (anim.camFrom) {
    const t = ease(clamp01((now - anim.camT0) / CAMERA_TIME));
    camera.position.lerpVectors(anim.camFrom.eye, anim.camTo.eye, t);
    controls.target.lerpVectors(anim.camFrom.target, anim.camTo.target, t);
    if (t >= 1) anim.camFrom = null;
    busy = true;
  }
  controls.update();
  renderer.render(scene, camera);
  return busy;
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

function setPlaying(on) {
  clearInterval(playing);
  playing = on ? setInterval(next, AUTOPLAY * 1000) : null;
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
  window.assemblyGuide = { goTo, setExplode: (v) => { explode = v; $('explode').value = v; }, setXray, parts, data };
}

main().catch((err) => {
  console.error(err);
  $('loading').textContent = String(err);
});
