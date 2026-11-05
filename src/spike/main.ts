// TASK-1.4 lighting spike: baked ambient-cube lightmaps (6 axes) + normal map + SH-ish probes on a sphere.
import * as THREE from 'three/webgpu';
import {
  Fn, float, vec3, vec2, uv, texture, uniform, mix, step, normalWorld, normalMap, normalView,
  cameraWorldMatrix, transformDirection, normalize, positionWorld,
} from 'three/tsl';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { EXRLoader } from 'three/examples/jsm/loaders/EXRLoader.js';
import { createRenderer } from '../renderer';
import { applyPose } from '../poses';

const q = new URLSearchParams(location.search);
const { renderer, backend } = await createRenderer();
const base = '/spike/';
const meta = await (await fetch(base + 'meta.json')).json();
const RANGE: number = meta.range;

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(60, innerWidth / innerHeight, 0.05, 100);
applyPose(camera, q.get('pose') ?? 'spike');
if (q.get('tm') === 'none') renderer.toneMapping = THREE.NoToneMapping; // debug: compare with Blender 'Standard'
renderer.toneMappingExposure = Number(q.get('exposure') ?? 0.85);

// ---- lightmaps: sRGB8 PNG, decoded by hardware; value = irradiance E / RANGE ----
const loader = new THREE.TextureLoader();
const loadLM = (n: string) => new Promise<THREE.Texture>((res) => {
  const t = loader.load(`${base}lm_${n}.png`, () => res(t));
  t.colorSpace = THREE.SRGBColorSpace; t.flipY = false; t.generateMipmaps = false;
  t.minFilter = THREE.LinearFilter; t.magFilter = THREE.LinearFilter;
});
const names = ['px', 'nx', 'py', 'ny', 'pz', 'nz'];
const lms = Object.fromEntries(await Promise.all(names.map(async (n) => [n, await loadLM(n)])));
const normalTex = await loader.loadAsync(base + 'panel_normal.png');
normalTex.flipY = false; normalTex.colorSpace = THREE.NoColorSpace; normalTex.wrapS = normalTex.wrapT = THREE.RepeatWrapping;

// Blender (x, y, z) -> three (x, z, -y): three +X=px, -X=nx, +Y=pz, -Y=nz, +Z=ny, -Z=py.
// Ambient cube (Valve): E(n) = n.x^2 * E(+-X) + n.y^2 * E(+-Y) + n.z^2 * E(+-Z)
type V3 = ReturnType<typeof vec3>;
const ambientCube = (n: any, c: { px: V3; nx: V3; py: V3; ny: V3; pz: V3; nz: V3 }) => {
  const n2 = n.mul(n);
  const cx = mix(c.nx, c.px, step(0, n.x));
  const cy = mix(c.nz, c.pz, step(0, n.y));   // three Y = blender Z
  const cz = mix(c.py, c.ny, step(0, n.z));   // three +Z = blender -Y
  return cx.mul(n2.x).add(cy.mul(n2.y)).add(cz.mul(n2.z));
};
const lmUV = uv(1);
const lmSample = Object.fromEntries(names.map((n) => [n, texture(lms[n], lmUV).rgb.mul(RANGE)])) as any;

const albedoOf = (name: string) => vec3(...(meta.albedo[name] as [number, number, number]));
const matFor = (name: string) => {
  const m = new THREE.MeshBasicNodeMaterial();
  let n: any = normalWorld;
  if (name === 'panel' && q.get('nomap') !== '1') {
    const nv = normalMap(texture(normalTex), vec2(1, 1));
    n = normalize(transformDirection(nv, cameraWorldMatrix));
  }
  const E = ambientCube(n, lmSample);
  m.colorNode = albedoOf(name).mul(E);
  return m;
};

const gltf = await new GLTFLoader().loadAsync(base + 'room.glb');
gltf.scene.traverse((o) => {
  const mesh = o as THREE.Mesh;
  if (!mesh.isMesh) return;
  mesh.material = Array.isArray(mesh.material)
    ? mesh.material.map((m) => matFor(m.name)) : matFor((mesh.material as THREE.Material).name);
});
scene.add(gltf.scene);

// ---- sky through the window ----
try {
  const sky = await new EXRLoader().loadAsync(base + 'sky.exr');
  sky.mapping = THREE.EquirectangularReflectionMapping;
  scene.background = sky;
  scene.backgroundRotation.y = Number(q.get('skyrot') ?? 0);
  scene.backgroundIntensity = 1;
} catch (e) { console.warn('no sky', e); scene.background = new THREE.Color(0x88aadd); }

// ---- probes -> sphere ----
const g = meta.probes.grid as { x: number[]; y: number[]; z: number[] };
const items = meta.probes.items as { pos: number[]; cube: number[][] }[];
const probeU = Object.fromEntries(names.map((n) => [n, uniform(new THREE.Vector3())])) as Record<string, any>;
const tmp = [0, 0, 0];
function sampleProbes(bx: number, by: number, bz: number) {
  const axis = (arr: number[], v: number) => {
    const c = Math.min(Math.max(v, arr[0]), arr[arr.length - 1]);
    let i = 0; while (i < arr.length - 2 && c > arr[i + 1]) i++;
    return [i, (c - arr[i]) / (arr[i + 1] - arr[i])] as const;
  };
  const [ix, fx] = axis(g.x, bx), [iy, fy] = axis(g.y, by), [iz, fz] = axis(g.z, bz);
  for (let f = 0; f < 6; f++) {
    tmp[0] = tmp[1] = tmp[2] = 0;
    for (let dx = 0; dx < 2; dx++) for (let dy = 0; dy < 2; dy++) for (let dz = 0; dz < 2; dz++) {
      const w = (dx ? fx : 1 - fx) * (dy ? fy : 1 - fy) * (dz ? fz : 1 - fz);
      const p = items[((ix + dx) * g.y.length + (iy + dy)) * g.z.length + (iz + dz)].cube[f];
      tmp[0] += w * p[0]; tmp[1] += w * p[1]; tmp[2] += w * p[2];
    }
    probeU[names[f]].value.set(tmp[0], tmp[1], tmp[2]);
  }
}
const sphereMat = new THREE.MeshBasicNodeMaterial();
sphereMat.colorNode = vec3(...(meta.sphere.albedo as [number, number, number]))
  .mul(ambientCube(normalWorld, probeU as any));
const sphere = new THREE.Mesh(new THREE.SphereGeometry(meta.sphere.radius, 64, 32), sphereMat);
scene.add(sphere);
// sphere position in Blender coords: ?sphere=x,y,z ; ?anim=1 sweeps from the sun patch into the shadowed side
const sp = (q.get('sphere') ?? '3.2,3.6,0.3').split(',').map(Number);
const place = (bx: number, by: number, bz: number) => { sphere.position.set(bx, bz, -by); sampleProbes(bx, by, bz); };
place(sp[0], sp[1], sp[2]);

addEventListener('resize', () => {
  camera.aspect = innerWidth / innerHeight; renderer.setSize(innerWidth, innerHeight);
  applyPose(camera, q.get('pose') ?? 'spike');
});
applyPose(camera, q.get('pose') ?? 'spike');

let frames = 0; let markReady!: () => void;
const ready = new Promise<void>((r) => (markReady = r));
(window as any).__game = { ready, backend, place };
const anim = q.get('anim') === '1';
renderer.setAnimationLoop((t) => {
  if (anim) place(sp[0], 3 + 2.2 * Math.sin(t / 1500), sp[2]);
  renderer.render(scene, camera);
  if (++frames === 5) markReady();
});
