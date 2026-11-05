import * as THREE from 'three/webgpu';
import RAPIER from '@dimforge/rapier3d-compat';

const RADIUS = 0.3;
const HALF_CYL = 0.55; // capsule total height 1.7 m
const EYE = 1.6;
const WALK = 2.2;
const SPRINT = 4.2;
const GRAVITY = -9.81;

/** Rapier kinematic character controller: WASD + mouse look (pointer lock), Shift sprint. */
export class FirstPersonController {
  readonly collider: RAPIER.Collider;
  private kcc: RAPIER.KinematicCharacterController;
  private keys = new Set<string>();
  private vy = 0;
  yaw = 0;
  pitch = 0;
  enabled = true;
  /** feet position */
  readonly feet = new THREE.Vector3();

  constructor(private world: RAPIER.World, private camera: THREE.PerspectiveCamera, dom: HTMLElement) {
    this.collider = world.createCollider(RAPIER.ColliderDesc.capsule(HALF_CYL, RADIUS));
    const k = (this.kcc = world.createCharacterController(0.01));
    k.setUp({ x: 0, y: 1, z: 0 });
    k.enableAutostep(0.3, 0.1, false);
    k.enableSnapToGround(0.2);
    k.setMaxSlopeClimbAngle(Math.PI / 4);
    k.setSlideEnabled(true);
    k.setApplyImpulsesToDynamicBodies(false);

    addEventListener('keydown', (e) => this.keys.add(e.code));
    addEventListener('keyup', (e) => this.keys.delete(e.code));
    addEventListener('blur', () => this.keys.clear());
    dom.addEventListener('click', () => {
      if (this.enabled && document.pointerLockElement !== dom) dom.requestPointerLock?.();
    });
    addEventListener('mousemove', (e) => {
      if (!this.enabled || document.pointerLockElement !== dom) return;
      this.look(-e.movementX * 0.0022, -e.movementY * 0.0022);
    });
  }

  look(dyaw: number, dpitch: number) {
    this.yaw += dyaw;
    this.pitch = THREE.MathUtils.clamp(this.pitch + dpitch, -1.5, 1.5);
  }

  /** Feet position + yaw (degrees, 0 looks -z, + turns left). */
  teleport(x: number, y: number, z: number, yawDeg = 0) {
    this.feet.set(x, y, z);
    this.yaw = THREE.MathUtils.degToRad(yawDeg);
    this.pitch = 0;
    this.vy = 0;
    this.collider.setTranslation({ x, y: y + HALF_CYL + RADIUS, z });
    this.syncCamera();
  }

  /** Test hook: hold a key for the next updates. */
  press(code: string, down = true) {
    if (down) this.keys.add(code);
    else this.keys.delete(code);
  }

  update(dt: number) {
    if (!this.enabled) return;
    dt = Math.min(dt, 0.05);
    const k = this.keys;
    const f = (k.has('KeyW') || k.has('ArrowUp') ? 1 : 0) - (k.has('KeyS') || k.has('ArrowDown') ? 1 : 0);
    const r = (k.has('KeyD') || k.has('ArrowRight') ? 1 : 0) - (k.has('KeyA') || k.has('ArrowLeft') ? 1 : 0);
    const speed = k.has('ShiftLeft') || k.has('ShiftRight') ? SPRINT : WALK;
    const sin = Math.sin(this.yaw);
    const cos = Math.cos(this.yaw);
    // forward = (-sin, -cos), right = (cos, -sin)
    let dx = -sin * f + cos * r;
    let dz = -cos * f - sin * r;
    const len = Math.hypot(dx, dz);
    if (len > 0) {
      dx = (dx / len) * speed;
      dz = (dz / len) * speed;
    }
    this.vy = this.kcc.computedGrounded() ? -1 : this.vy + GRAVITY * dt;
    this.kcc.computeColliderMovement(this.collider, { x: dx * dt, y: this.vy * dt, z: dz * dt });
    const m = this.kcc.computedMovement();
    const p = this.collider.translation();
    const n = { x: p.x + m.x, y: p.y + m.y, z: p.z + m.z };
    this.collider.setTranslation(n);
    this.feet.set(n.x, n.y - HALF_CYL - RADIUS, n.z);
    this.syncCamera();
  }

  private syncCamera() {
    this.camera.position.set(this.feet.x, this.feet.y + EYE, this.feet.z);
    this.camera.rotation.set(this.pitch, this.yaw, 0, 'YXZ');
  }
}
