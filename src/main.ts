import * as THREE from 'three/webgpu';
import { createRenderer } from './renderer';
import { createPhysics } from './physics';
import { FpsHud } from './hud/fps';

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

addEventListener('resize', () => {
  camera.aspect = innerWidth / innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(innerWidth, innerHeight);
});

renderer.setAnimationLoop(() => {
  physics.world.step();
  const t = body.translation();
  const r = body.rotation();
  cube.position.set(t.x, t.y, t.z);
  cube.quaternion.set(r.x, r.y, r.z, r.w);
  renderer.render(scene, camera);
  hud.tick();
});
