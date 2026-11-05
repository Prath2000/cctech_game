import * as THREE from 'three/webgpu';
import RAPIER from '@dimforge/rapier3d-compat';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

/** Loads the Blender blockout and adds a static cuboid collider per mesh (skips `collider=none`). */
export async function loadRoom(world: RAPIER.World, scene: THREE.Scene): Promise<THREE.Object3D> {
  const gltf = await new GLTFLoader().loadAsync(`${import.meta.env.BASE_URL}models/room_blockout.glb`);
  const root = gltf.scene;
  scene.add(root);
  root.updateMatrixWorld(true);
  const box = new THREE.Box3();
  const size = new THREE.Vector3();
  const center = new THREE.Vector3();
  let count = 0;
  root.traverse((o) => {
    if (!(o as THREE.Mesh).isMesh) return;
    if (o.userData.collider === 'none') return;
    box.setFromObject(o).getSize(size);
    box.getCenter(center);
    world.createCollider(
      RAPIER.ColliderDesc.cuboid(size.x / 2, size.y / 2, size.z / 2).setTranslation(center.x, center.y, center.z),
    );
    count++;
  });
  world.step(); // refresh the query pipeline so the character controller sees them
  console.log(`[room] ${count} colliders`);
  return root;
}
