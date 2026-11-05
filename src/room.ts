import * as THREE from 'three/webgpu';
import RAPIER from '@dimforge/rapier3d-compat';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

/** Loads the Blender blockout and adds a static cuboid collider per mesh (skips `collider=none`). */
export async function loadRoom(world: RAPIER.World, scene: THREE.Scene): Promise<THREE.Object3D> {
  const gltf = await new GLTFLoader().loadAsync(`${import.meta.env.BASE_URL}models/room.glb`);
  const root = gltf.scene;
  scene.add(root);
  root.updateMatrixWorld(true);
  const pos = new THREE.Vector3();
  const quat = new THREE.Quaternion();
  const scl = new THREE.Vector3();
  const size = new THREE.Vector3();
  const center = new THREE.Vector3();
  let count = 0;
  const addBox = (o: THREE.Object3D, box: THREE.Box3) => {
    // Local-space box + world rotation, so rotated meshes get tight, oriented boxes.
    box.getSize(size);
    box.getCenter(center);
    o.matrixWorld.decompose(pos, quat, scl);
    size.multiply(scl);
    center.applyMatrix4(o.matrixWorld);
    world.createCollider(
      RAPIER.ColliderDesc.cuboid(Math.abs(size.x) / 2, Math.abs(size.y) / 2, Math.abs(size.z) / 2)
        .setTranslation(center.x, center.y, center.z)
        .setRotation({ x: quat.x, y: quat.y, z: quat.z, w: quat.w }),
    );
    count++;
  };
  // Blended surfaces never write depth (no overdraw/sort holes); glass draws after decals.
  root.traverse((o) => {
    const mesh = o as THREE.Mesh;
    if (!mesh.isMesh) return;
    for (const m of Array.isArray(mesh.material) ? mesh.material : [mesh.material]) {
      if (!m.transparent) continue;
      m.depthWrite = false;
      mesh.renderOrder = /^glass/.test(m.name) ? 2 : 1;
    }
  });
  root.traverse((o) => {
    if (!(o as THREE.Mesh).isMesh) return;
    if (o.userData.collider === 'none') return;
    if (o.userData.interact === 'grab') return; // grab items get dynamic bodies (GrabSystem)
    if (o.userData.use_kind === 'chair') return; // chairs get dynamic bodies (seating.ts)
    if (o.userData.hinge_axis) return; // hinged doors get kinematic bodies (pantry)
    const m = o as THREE.Mesh;
    if (!m.geometry.boundingBox) m.geometry.computeBoundingBox();
    if (o.userData.collider === 'islands') for (const b of islandBoxes(m.geometry)) addBox(o, b);
    else addBox(o, m.geometry.boundingBox!);
  });
  world.step(); // refresh the query pipeline so the character controller sees them
  console.log(`[room] ${count} colliders`);
  return root;
}

/**
 * One local-space box per connected piece of the mesh (pieces joined by shared vertex positions).
 * For hollow props (cabinet carcass, coffee machine) so bays/interiors stay open instead of one solid bbox.
 */
function islandBoxes(g: THREE.BufferGeometry): THREE.Box3[] {
  const posAttr = g.getAttribute('position');
  const index = g.getIndex();
  const parent = new Int32Array(posAttr.count).map((_, i) => i);
  const find = (i: number): number => { while (parent[i] !== i) i = parent[i] = parent[parent[i]]; return i; };
  const byKey = new Map<string, number>();
  for (let i = 0; i < posAttr.count; i++) {
    const k = `${Math.round(posAttr.getX(i) * 1e4)},${Math.round(posAttr.getY(i) * 1e4)},${Math.round(posAttr.getZ(i) * 1e4)}`;
    const j = byKey.get(k);
    if (j === undefined) byKey.set(k, i); else parent[find(i)] = find(j);
  }
  const n = index ? index.count : posAttr.count;
  for (let t = 0; t < n; t += 3) {
    const a = index ? index.getX(t) : t, b = index ? index.getX(t + 1) : t + 1, c = index ? index.getX(t + 2) : t + 2;
    parent[find(b)] = find(a);
    parent[find(c)] = find(a);
  }
  const boxes = new Map<number, THREE.Box3>();
  const v = new THREE.Vector3();
  for (let i = 0; i < posAttr.count; i++) {
    const r = find(i);
    let b = boxes.get(r);
    if (!b) boxes.set(r, (b = new THREE.Box3()));
    b.expandByPoint(v.fromBufferAttribute(posAttr, i));
  }
  return [...boxes.values()];
}
