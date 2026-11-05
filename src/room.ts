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
  root.traverse((o) => {
    if (!(o as THREE.Mesh).isMesh) return;
    if (o.userData.collider === 'none') return;
    // Local-space box + world rotation, so rotated meshes get tight, oriented boxes.
    const m = o as THREE.Mesh;
    if (!m.geometry.boundingBox) m.geometry.computeBoundingBox();
    m.geometry.boundingBox!.getSize(size);
    m.geometry.boundingBox!.getCenter(center);
    o.matrixWorld.decompose(pos, quat, scl);
    size.multiply(scl);
    center.applyMatrix4(o.matrixWorld);
    world.createCollider(
      RAPIER.ColliderDesc.cuboid(Math.abs(size.x) / 2, Math.abs(size.y) / 2, Math.abs(size.z) / 2)
        .setTranslation(center.x, center.y, center.z)
        .setRotation({ x: quat.x, y: quat.y, z: quat.z, w: quat.w }),
    );
    count++;
  });
  world.step(); // refresh the query pipeline so the character controller sees them
  console.log(`[room] ${count} colliders`);
  return root;
}
