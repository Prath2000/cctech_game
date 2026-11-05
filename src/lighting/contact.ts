import * as THREE from 'three/webgpu';
import RAPIER from '@dimforge/rapier3d-compat';

interface Blob {
  obj: THREE.Object3D;
  mesh: THREE.Mesh;
  mat: THREE.MeshBasicNodeMaterial;
  /** footprint centre offset from obj origin, bottom offset, half-size */
  off: THREE.Vector3;
  base: number;
  max: number;
}

const MAX_GAP = 0.6;

function radialTexture(): THREE.CanvasTexture {
  const c = document.createElement('canvas');
  c.width = c.height = 64;
  const g = c.getContext('2d')!;
  const grad = g.createRadialGradient(32, 32, 0, 32, 32, 32);
  grad.addColorStop(0, 'rgba(0,0,0,1)');
  grad.addColorStop(0.45, 'rgba(0,0,0,0.55)');
  grad.addColorStop(1, 'rgba(0,0,0,0)');
  g.fillStyle = grad;
  g.fillRect(0, 0, 64, 64);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}

/**
 * Soft blob contact shadows under grab items and chairs: a flat radial-gradient quad placed on the surface found
 * by a downward Rapier ray (static/kinematic colliders only); fades and widens with height. Updates run from
 * scene.onBeforeRender (before matrices update), so no per-frame allocations and no extra render passes.
 */
export class ContactShadows {
  private blobs: Blob[] = [];
  private ray = new RAPIER.Ray({ x: 0, y: 0, z: 0 }, { x: 0, y: -1, z: 0 });
  private p = new THREE.Vector3();

  constructor(private scene: THREE.Scene, private world: RAPIER.World) {
    scene.updateMatrixWorld(true);
    const tex = radialTexture();
    const box = new THREE.Box3();
    const size = new THREE.Vector3();
    const geo = new THREE.PlaneGeometry(1, 1).rotateX(-Math.PI / 2);
    scene.traverse((o) => {
      const chair = o.userData.use_kind === 'chair';
      if (o.userData.interact !== 'grab' && !chair) return;
      box.setFromObject(o);
      if (box.isEmpty()) return;
      box.getSize(size);
      const wp = o.getWorldPosition(new THREE.Vector3());
      const off = box.getCenter(new THREE.Vector3()).sub(wp);
      off.y = box.min.y - wp.y;
      const mat = new THREE.MeshBasicNodeMaterial({ map: tex, transparent: true, depthWrite: false, color: 0x000000 });
      mat.polygonOffset = true;
      mat.polygonOffsetFactor = -2;
      const mesh = new THREE.Mesh(geo, mat);
      mesh.renderOrder = 1;
      mesh.frustumCulled = false;
      mesh.visible = false;
      mesh.userData.reflect = false;
      scene.add(mesh);
      const max = Math.max(size.x, size.z);
      this.blobs.push({ obj: o, mesh, mat, off, base: chair ? 0.5 : 0.7, max: chair ? max * 1.15 : Math.max(max * 1.7, 0.1) });
    });
    const prev = scene.onBeforeRender;
    scene.onBeforeRender = (...a: Parameters<typeof prev>) => {
      prev.apply(scene, a);
      this.update();
    };
  }

  update(): void {
    for (let i = 0; i < this.blobs.length; i++) {
      const b = this.blobs[i];
      const p = b.obj.getWorldPosition(this.p);
      this.ray.origin.x = p.x + b.off.x;
      this.ray.origin.y = p.y + b.off.y + 0.04;
      this.ray.origin.z = p.z + b.off.z;
      const hit = this.world.castRay(this.ray, MAX_GAP + 0.1, true, RAPIER.QueryFilterFlags.EXCLUDE_DYNAMIC);
      if (!hit) { b.mesh.visible = false; continue; }
      const gap = Math.max(0, hit.timeOfImpact - 0.04);
      if (gap > MAX_GAP) { b.mesh.visible = false; continue; }
      const k = 1 - gap / MAX_GAP;
      const sc = b.max * (1 + gap * 1.2);
      b.mesh.visible = true;
      b.mesh.position.set(this.ray.origin.x, this.ray.origin.y - hit.timeOfImpact + 0.004, this.ray.origin.z);
      b.mesh.scale.set(sc, 1, sc);
      b.mat.opacity = b.base * k * k;
    }
  }
}
