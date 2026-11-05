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
    if (o.userData.collider === 'boxes') {
      // Hollow props: explicit [cx,cy,cz,hx,hy,hz] boxes (object-local, game axes) so bays/interiors stay open.
      for (const [cx, cy, cz, hx, hy, hz] of JSON.parse(String(o.userData.collider_boxes))) {
        addBox(o, new THREE.Box3(new THREE.Vector3(cx - hx, cy - hy, cz - hz), new THREE.Vector3(cx + hx, cy + hy, cz + hz)));
      }
    }
    else addBox(o, m.geometry.boundingBox!);
  });
  world.step(); // refresh the query pipeline so the character controller sees them
  console.log(`[room] ${count} colliders`);
  return root;
}
