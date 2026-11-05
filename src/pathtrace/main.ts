// Path-traced renders of room.glb (three-gpu-pathtracer, WebGL). Query: ?pose=<name>&spp=<n>&w=1600&h=1000
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { RGBELoader } from 'three/addons/loaders/RGBELoader.js';
import { WebGLPathTracer, PhysicalCamera } from 'three-gpu-pathtracer';
import hdrUrl from '../../assets/raw/polyhaven/kloofendal/kloofendal_2k.hdr?url';
import poses from './poses.json';

const q = new URLSearchParams(location.search);
const poseName = q.get('pose') ?? 'hall';
const targetSpp = Number(q.get('spp') ?? 600);
const W = Number(q.get('w') ?? 1600), H = Number(q.get('h') ?? 1000);
const pose = (poses as Record<string, { position: number[]; yaw: number; pitch: number; hfov: number }>)[poseName];

const renderer = new THREE.WebGLRenderer({ antialias: false, preserveDrawingBuffer: true });
renderer.setPixelRatio(1);
renderer.setSize(W, H);
renderer.toneMapping = THREE.AgXToneMapping;
renderer.toneMappingExposure = Number(q.get('exp') ?? 1);
document.body.appendChild(renderer.domElement);

const scene = new THREE.Scene();
const gltf = await new GLTFLoader().loadAsync(`${import.meta.env.BASE_URL}models/room.glb`);
scene.add(gltf.scene);
gltf.scene.traverse((o) => {
  const mesh = o as THREE.Mesh;
  if (!mesh.isMesh) return;
  if (q.get('noglass') && mesh.name.startsWith('window_glass')) { mesh.visible = false; return; }
  if (mesh.name === 'window_backdrop') { mesh.visible = false; return; } // emissive plane outside would block the sun
  const mats = (Array.isArray(mesh.material) ? mesh.material : [mesh.material]).map((m) => {
    // glTF gives plain MeshStandardMaterial for blended glass; upgrade so `transmission` exists.
    if (!/^(glass_clear|glass_black|sx_vend_glass|sx_clear_vinyl|sx_tumbler_glass)$/.test(m.name) || (m as THREE.MeshPhysicalMaterial).isMeshPhysicalMaterial) return m;
    const p = new THREE.MeshPhysicalMaterial();
    p.copy(m as THREE.MeshStandardMaterial);
    p.name = m.name;
    return p;
  });
  mesh.material = Array.isArray(mesh.material) ? mats : mats[0];
  for (const m of mats) {
    const mat = m as THREE.MeshPhysicalMaterial;
    mat.lightMap = null; // real GI replaces the baked maps
    if (/^(glass_clear|glass_black|sx_vend_glass|sx_clear_vinyl|sx_tumbler_glass)$/.test(mat.name)) {
      mat.transparent = false; mat.opacity = 1; mat.depthWrite = true;
      mat.transmission = mat.name === 'glass_black' ? 0.85 : 1;
      mat.ior = 1.05; if (mat.name === 'glass_clear') mat.color.setRGB(0.92, 0.97, 1); mat.specularColor?.setRGB(1, 1, 1); mat.roughness = 0.02; mat.thickness = 0.01;
      mat.side = THREE.DoubleSide;
    } else if (mat.transparent) mat.depthWrite = true;
    mat.needsUpdate = true;
  }
});

// Sky + sun. Windows at z=0; sun enters from -z, ~38 deg elevation, slightly toward +x.
const hdr = await new RGBELoader().loadAsync(hdrUrl);
hdr.mapping = THREE.EquirectangularReflectionMapping;
scene.environment = hdr;
scene.background = hdr;
scene.environmentIntensity = 1;
const el = THREE.MathUtils.degToRad(38), az = THREE.MathUtils.degToRad(Number(q.get('az') ?? 25));
const toSun = new THREE.Vector3(Math.sin(az) * Math.cos(el), Math.sin(el), -Math.cos(az) * Math.cos(el));
const sunI = Number(q.get('sun') ?? 12);
// Soft angular size: several slightly offset directional lights share the intensity (penumbra ~0.5 deg disc).
const tmp = new THREE.Vector3();
const up = new THREE.Vector3(0, 1, 0);
const side = new THREE.Vector3().crossVectors(toSun, up).normalize();
const up2 = new THREE.Vector3().crossVectors(side, toSun).normalize();
const N = 7;
for (let i = 0; i < N; i++) {
  const r = i === 0 ? 0 : 0.0065, a = (i / 6) * Math.PI * 2; // 0.0065 rad ~ 0.37 deg
  tmp.copy(toSun).addScaledVector(side, Math.cos(a) * r).addScaledVector(up2, Math.sin(a) * r).normalize();
  const l = new THREE.DirectionalLight(0xffe2b8, sunI / N);
  l.position.copy(tmp).multiplyScalar(40);
  l.target.position.set(6, 0, 3.75);
  scene.add(l, l.target);
}

const cam = new PhysicalCamera(pose.hfov, W / H, 0.05, 200);
cam.fov = THREE.MathUtils.radToDeg(2 * Math.atan(Math.tan(THREE.MathUtils.degToRad(pose.hfov) / 2) / (W / H)));
cam.position.fromArray(pose.position);
cam.rotation.set(THREE.MathUtils.degToRad(pose.pitch), THREE.MathUtils.degToRad(pose.yaw), 0, 'YXZ');
cam.fStop = 11; cam.focusDistance = 3; // physical camera: gentle depth of field
cam.updateProjectionMatrix();
cam.updateMatrixWorld(true);

const pt = new WebGLPathTracer(renderer);
pt.renderScale = 1;
pt.tiles.set(2, 2);
pt.bounces = 6;
pt.transmissiveBounces = 6;
pt.filterGlossyFactor = 0.5;
pt.dynamicLowRes = false;
pt.rasterizeScene = false;
pt.minSamples = 0;
pt.renderDelay = 0;
pt.fadeDuration = 0;
pt.setScene(scene, cam);

const w = window as unknown as { __pt: object };
let done = false;
w.__pt = { get samples() { return pt.samples; }, get done() { return done; }, target: targetSpp, pose: poseName };
const loop = () => {
  if (pt.samples < targetSpp) { pt.renderSample(); requestAnimationFrame(loop); } else done = true;
};
loop();
