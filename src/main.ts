import * as THREE from 'three/webgpu';
import { createRenderer } from './renderer';
import { createPhysics } from './physics';
import { FpsHud } from './hud/fps';
import { loadRoom } from './room';
import { FirstPersonController } from './controller';
import { Interaction } from './interact';
import { GrabSystem } from './interact/grab';
import { addDebugObjects } from './interact/debug';
import { applyPose, poseTable } from './poses';

const { renderer, backend } = await createRenderer();
const physics = await createPhysics();
const hud = new FpsHud(backend);

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x202428);
const camera = new THREE.PerspectiveCamera(60, innerWidth / innerHeight, 0.1, 100);
camera.position.set(3, 2.5, 4);
camera.lookAt(0, 0.8, 0);

await loadRoom(physics.world, scene);
if (new URLSearchParams(location.search).get('debug') === '1') addDebugObjects(scene, physics.world);
const interaction = new Interaction(scene, camera, physics.world);
const player = new FirstPersonController(physics.world, camera, renderer.domElement);
// Start just inside the west-wall door (z 3.2-4.4), facing east into the room.
player.teleport(1.0, 0, 3.3, -90);
const grab = new GrabSystem(physics.world, camera, interaction, player.collider, renderer.domElement);
grab.register(scene, scene);
interaction.refresh();

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
  player,
  interaction,
  scene,
  grab,
  /** Deterministic physics stepping for scripts (no rendering). */
  stepPhysics(n = 1) {
    for (let i = 0; i < n; i++) { grab.beforeStep(); physics.world.step(); grab.afterStep(); }
  },
};

const STEP = 1 / 60;
const MAX_SUBSTEPS = 4;
let acc = 0;
physics.world.timestep = STEP;

renderer.setAnimationLoop(() => {
  const now = performance.now();
  fpsSamples.push(now - lastT);
  lastT = now;
  if (fpsSamples.length > 40000) fpsSamples.splice(0, 20000); // bulk trim: amortised O(1), no per-frame shift()
  if (++frames === 5) markReady();

  // Fixed 1/60 s physics steps (capped), independent of display refresh rate.
  acc = Math.min(acc + (fpsSamples[fpsSamples.length - 1] / 1000), STEP * MAX_SUBSTEPS);
  let steps = 0;
  for (; acc >= STEP; acc -= STEP, steps++) { grab.beforeStep(); physics.world.step(); }
  if (steps) grab.afterStep();
  else physics.world.propagateModifiedBodyPositionsToColliders(); // queries must reflect bodies moved/teleported since the last step
  player.enabled = !currentPose; // a pinned ?pose= is never overridden by the controller
  player.update(Math.min(0.05, fpsSamples[fpsSamples.length - 1] / 1000));
  interaction.update();
  renderer.render(scene, camera);
  hud.tick();
});
