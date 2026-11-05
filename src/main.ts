import * as THREE from 'three/webgpu';
import { createRenderer } from './renderer';
import { createPhysics } from './physics';
import { FpsHud } from './hud/fps';
import { applyPose, poseTable } from './poses';

const { renderer, backend } = await createRenderer();
const physics = await createPhysics();
const hud = new FpsHud(backend);

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x202428);
const camera = new THREE.PerspectiveCamera(60, innerWidth / innerHeight, 0.1, 100);
camera.position.set(3, 2.5, 4);
camera.lookAt(0, 0.8, 0);

const ground = new THREE.Mesh(
  new THREE.PlaneGeometry(50, 50),
  new THREE.MeshStandardMaterial({ color: 0x888888, roughness: 0.9 }),
);
ground.rotation.x = -Math.PI / 2;
scene.add(ground);

const cube = new THREE.Mesh(
  new THREE.BoxGeometry(1, 1, 1),
  new THREE.MeshStandardMaterial({ color: 0xc86432, roughness: 0.5 }),
);
scene.add(cube);
const body = physics.addBox([0, 4, 0], 0.5);
body.setRotation({ x: 0.2, y: 0.3, z: 0.1, w: 0.93 }, true);

scene.add(new THREE.HemisphereLight(0xbfd4ff, 0x444444, 1));
const sun = new THREE.DirectionalLight(0xffffff, 3);
sun.position.set(4, 8, 3);
scene.add(sun);

// Camera poses: `?pose=<name>` pins the camera (input frozen).
let currentPose: string | null = new URLSearchParams(location.search).get('pose');
if (currentPose && !applyPose(camera, currentPose)) {
  console.warn(`[pose] unknown pose "${currentPose}"`);
  currentPose = null;
}

addEventListener('resize', () => {
  camera.aspect = innerWidth / innerHeight;
  if (currentPose) applyPose(camera, currentPose);
  else camera.updateProjectionMatrix();
  renderer.setSize(innerWidth, innerHeight);
});

const fpsSamples: number[] = [];
let frames = 0;
let lastT = performance.now();
let markReady!: () => void;
const ready = new Promise<void>((r) => (markReady = r));
(window as any).__game = {
  ready,
  backend,
  poses: Object.keys(poseTable),
  fpsSamples,
  setPose(name: string) {
    if (!applyPose(camera, name)) return false;
    currentPose = name;
    return true;
  },
};

renderer.setAnimationLoop(() => {
  const now = performance.now();
  fpsSamples.push(now - lastT);
  lastT = now;
  if (fpsSamples.length > 20000) fpsSamples.shift();
  if (++frames === 5) markReady();

  physics.world.step();
  const t = body.translation();
  const r = body.rotation();
  cube.position.set(t.x, t.y, t.z);
  cube.quaternion.set(r.x, r.y, r.z, r.w);
  renderer.render(scene, camera);
  hud.tick();
});
