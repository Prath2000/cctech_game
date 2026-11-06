import * as THREE from 'three/webgpu';
import RAPIER from '@dimforge/rapier3d-compat';

/** `?debug=1` test objects: a grab cube (0.3 kg), a use box and a look panel. */
export function addDebugObjects(scene: THREE.Scene, world: RAPIER.World) {
  const mk = (name: string, geo: THREE.BufferGeometry, color: number, pos: [number, number, number], ud: Record<string, unknown>) => {
    const m = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ color }));
    m.name = name;
    m.position.set(...pos);
    m.userData = { caption_id: name, ...ud };
    scene.add(m);
    if (ud.interact !== 'grab') {
      const h = geo.boundingBox ?? (geo.computeBoundingBox(), geo.boundingBox!);
      const s = h.getSize(new THREE.Vector3());
      world.createCollider(RAPIER.ColliderDesc.cuboid(s.x / 2, s.y / 2, s.z / 2).setTranslation(...pos));
    }
    return m;
  };
  mk('debug_cube', new THREE.BoxGeometry(0.2, 0.2, 0.2), 0xff6b35, [3.0, 1.0, 5.0], { interact: 'grab', mass: 0.3 });
  mk('debug_box', new THREE.BoxGeometry(0.4, 0.4, 0.4), 0xffd166, [3.4, 0.2, 5.8], { interact: 'use', use_kind: 'debug' });
  mk('debug_panel', new THREE.BoxGeometry(0.05, 0.6, 0.9), 0x8fd3ff, [3.4, 1.2, 4.2], { interact: 'look' });
}
