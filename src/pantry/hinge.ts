import * as THREE from 'three/webgpu';
import RAPIER from '@dimforge/rapier3d-compat';
import { smooth } from './fx';

const wp = new THREE.Vector3();
const wq = new THREE.Quaternion();
const lc = new THREE.Vector3();

/**
 * Hinged door from the scene conventions (`hinge_axis`, `hinge_max_deg`, `hinge_open_sign`): the node origin is the hinge,
 * eased swing, kinematic Rapier body that follows. If the player is in the swept volume the door reverses (never traps).
 */
export class Hinge {
  p = 0; // eased progress 0..1
  target = 0;
  readonly collider: RAPIER.Collider;
  private body: RAPIER.RigidBody;
  private max: number;
  private sign: number;
  private axis: 'x' | 'y' | 'z';
  private cooldown = 0;
  bounced = 0;
  private locked = false;
  private shape: RAPIER.Cuboid;
  private center = new THREE.Vector3();

  constructor(readonly obj: THREE.Object3D, private world: RAPIER.World, private player: RAPIER.Collider, private duration = 0.8) {
    const u = obj.userData;
    this.axis = (u.hinge_axis as 'x' | 'y' | 'z') ?? 'y';
    this.max = THREE.MathUtils.degToRad(Number(u.hinge_max_deg) || 90);
    this.sign = Number(u.hinge_open_sign) < 0 ? -1 : 1;
    obj.updateWorldMatrix(true, false);
    obj.getWorldPosition(wp);
    obj.getWorldQuaternion(wq);
    this.body = world.createRigidBody(
      RAPIER.RigidBodyDesc.kinematicPositionBased()
        .setTranslation(wp.x, wp.y, wp.z)
        .setRotation({ x: wq.x, y: wq.y, z: wq.z, w: wq.w }),
    );
    // Closed-pose bounds relative to the hinge (doors are axis-aligned, unscaled; may be a Group of meshes).
    const b = new THREE.Box3().setFromObject(obj).translate(wp.negate());
    this.center.set((b.max.x + b.min.x) / 2, (b.max.y + b.min.y) / 2, (b.max.z + b.min.z) / 2);
    this.shape = new RAPIER.Cuboid(Math.max(0.005, (b.max.x - b.min.x) / 2), Math.max(0.005, (b.max.y - b.min.y) / 2), Math.max(0.005, (b.max.z - b.min.z) / 2));
    this.collider = world.createCollider(
      RAPIER.ColliderDesc.cuboid(
        Math.max(0.005, (b.max.x - b.min.x) / 2), Math.max(0.005, (b.max.y - b.min.y) / 2), Math.max(0.005, (b.max.z - b.min.z) / 2),
      ).setTranslation((b.max.x + b.min.x) / 2, (b.max.y + b.min.y) / 2, (b.max.z + b.min.z) / 2),
      this.body,
    );
  }

  get open() { return this.target === 1; }
  get moving() { return this.p !== this.target; }
  toggle() { this.target = this.target === 1 ? 0 : 1; this.cooldown = 0; return this.open; }

  /** Does the door, posed at the current obj transform, overlap the player? (tested against the pose it WILL have) */
  private blockedAt() {
    this.obj.updateWorldMatrix(false, false);
    this.obj.getWorldPosition(wp);
    this.obj.getWorldQuaternion(wq);
    lc.copy(this.center).applyQuaternion(wq).add(wp);
    const pid = this.player.handle;
    return !!this.world.intersectionWithShape(lc, wq, this.shape, undefined, undefined, this.collider, undefined, (c) => c.handle === pid);
  }

  private apply() {
    this.body.setNextKinematicTranslation(wp);
    this.body.setNextKinematicRotation(wq);
  }

  update(dt: number) {
    if (!this.moving) return;
    this.cooldown -= dt;
    const prev = this.p;
    const step = (dir: number) => {
      this.p = prev + dir * Math.min(Math.abs(this.target - prev), dt / this.duration);
      this.obj.rotation[this.axis] = this.sign * this.max * smooth(this.p);
      return this.blockedAt();
    };
    if (!step(Math.sign(this.target - prev))) { this.locked = false; this.apply(); return; }
    // Next pose would clip the player: hold, and reverse once (hysteresis: not again until a pose has been free).
    this.p = prev;
    this.obj.rotation[this.axis] = this.sign * this.max * smooth(prev);
    if (!this.locked && this.cooldown <= 0) {
      this.target = 1 - this.target;
      this.cooldown = 0.4;
      this.locked = true;
      this.bounced++;
    }
    this.blockedAt();
    this.apply();
  }
}
