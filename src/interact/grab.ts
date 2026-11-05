import * as THREE from 'three/webgpu';
import RAPIER from '@dimforge/rapier3d-compat';
import { captionFor } from './captions';
import type { Interaction } from './index';

const HOLD_DIST = 1.1;
const MIN_DIST = 0.45;
const FOLLOW_GAIN = 14;
const MAX_FOLLOW_SPEED = 9;
const BREAK_DIST = 1.6; // held item stuck behind geometry -> let go
const TOSS_SPEED = 7;
// Collision groups: high 16 bits = membership, low 16 = filter. Player = bit 0 (see controller), free grab items = bit 1,
// held items = bit 2 and they ignore the player (so carrying never shoves or blocks you).
const FREE_GROUPS = 0x0002_ffff;
const HELD_GROUPS = 0x0004_fffe;

interface Item {
  obj: THREE.Object3D;
  body: RAPIER.RigidBody;
  colliders: RAPIER.Collider[];
  awake: boolean;
  home: { p: THREE.Vector3; q: THREE.Quaternion };
}

/** Grab items (userData.interact = 'grab') become dynamic Rapier bodies; click to hold, click/Q/right-click to drop/toss. */
export class GrabSystem {
  readonly items: Item[] = [];
  held: Item | null = null;
  /** Items that left the world (y < -3) and were put back at their start; should stay 0. */
  respawns = 0;
  private fwd = new THREE.Vector3();
  private tgt = new THREE.Vector3();

  constructor(
    private world: RAPIER.World,
    private camera: THREE.PerspectiveCamera,
    private interaction: Interaction,
    private playerCollider: RAPIER.Collider,
    dom: HTMLElement,
  ) {
    interaction.heldInfo = () => (this.held ? { obj: this.held.obj, hint: 'Drop [click] · Toss [Q / right-click]' } : null);
    dom.addEventListener('mousedown', (e) => {
      if (document.pointerLockElement !== dom) return;
      if (e.button === 0) this.held ? this.drop() : this.pickTarget();
      else if (e.button === 2) this.toss();
    });
    dom.addEventListener('contextmenu', (e) => e.preventDefault());
    addEventListener('keydown', (e) => { if (e.code === 'KeyQ') this.toss(); });
  }

  /** Create bodies for every grab object under `root` (re-parented to the scene root, world transform kept). */
  register(root: THREE.Object3D, scene: THREE.Scene) {
    const found: THREE.Object3D[] = [];
    root.traverse((o) => { if (o.userData.interact === 'grab' && !this.items.some((i) => i.obj === o)) found.push(o); });
    for (const o of found) {
      scene.attach(o);
      o.updateMatrixWorld(true);
      this.items.push(this.makeItem(o));
    }
  }

  private makeItem(o: THREE.Object3D): Item {
    const mass = Number(o.userData.mass) > 0 ? Number(o.userData.mass) : 1;
    const p = o.position, q = o.quaternion, s = o.scale;
    const body = this.world.createRigidBody(
      RAPIER.RigidBodyDesc.dynamic()
        .setTranslation(p.x, p.y, p.z)
        .setRotation({ x: q.x, y: q.y, z: q.z, w: q.w })
        .setCcdEnabled(true)
        .setLinearDamping(0.05)
        .setAngularDamping(0.5)
        .setCanSleep(true),
    );
    const colliders: RAPIER.Collider[] = [];
    const meshes: THREE.Mesh[] = [];
    o.traverse((m) => { if ((m as THREE.Mesh).isMesh) meshes.push(m as THREE.Mesh); });
    const inv = o.matrixWorld.clone().invert();
    const v = new THREE.Vector3();
    const mk = (desc: RAPIER.ColliderDesc | null) => {
      if (!desc) return;
      desc.setMass(mass / Math.max(1, meshes.length)).setFriction(0.7).setRestitution(0.15).setCollisionGroups(FREE_GROUPS);
      colliders.push(this.world.createCollider(desc, body));
    };
    for (const m of meshes) {
      m.updateMatrixWorld(true);
      const rel = inv.clone().multiply(m.matrixWorld); // mesh -> body frame
      const pos = m.geometry.getAttribute('position');
      if (o.userData.collider === 'convex') {
        const pts = new Float32Array(pos.count * 3);
        for (let i = 0; i < pos.count; i++) v.fromBufferAttribute(pos, i).applyMatrix4(rel).toArray(pts, i * 3);
        mk(RAPIER.ColliderDesc.convexHull(pts));
      } else {
        const box = new THREE.Box3();
        for (let i = 0; i < pos.count; i++) box.expandByPoint(v.fromBufferAttribute(pos, i).applyMatrix4(rel));
        const sz = box.getSize(new THREE.Vector3()), c = box.getCenter(new THREE.Vector3());
        const half = (n: number) => Math.max(0.005, n / 2);
        mk(RAPIER.ColliderDesc.cuboid(half(sz.x), half(sz.y), half(sz.z)).setTranslation(c.x, c.y, c.z));
      }
    }
    void s;
    return { obj: o, body, colliders, awake: true, home: { p: p.clone(), q: q.clone() } };
  }

  private itemOf(o: THREE.Object3D | null): Item | null {
    return (o && this.items.find((i) => i.obj === o)) || null;
  }

  pickTarget() {
    this.pickItem(this.itemOf(this.interaction.target));
  }

  pickItem(it: Item | null) {
    if (!it || this.held) return false;
    this.held = it;
    it.body.setGravityScale(0, true);
    it.body.setAngularDamping(8);
    it.body.setLinearDamping(2);
    for (const c of it.colliders) c.setCollisionGroups(HELD_GROUPS);
    this.interaction.ignore = it.obj;
    return true;
  }

  private release(): Item | null {
    const it = this.held;
    if (!it) return null;
    this.held = null;
    this.interaction.ignore = null;
    it.body.setGravityScale(1, true);
    it.body.setAngularDamping(0.5);
    it.body.setLinearDamping(0.05);
    for (const c of it.colliders) c.setCollisionGroups(FREE_GROUPS);
    return it;
  }

  drop() {
    const it = this.release();
    if (!it) return false;
    const v = it.body.linvel();
    it.body.setLinvel({ x: v.x * 0.3, y: Math.min(v.y, 0), z: v.z * 0.3 }, true);
    return true;
  }

  toss() {
    const it = this.release();
    if (!it) return false;
    this.camera.getWorldDirection(this.fwd);
    const m = it.body.mass();
    const speed = TOSS_SPEED / Math.max(1, Math.sqrt(m));
    it.body.setLinvel({ x: 0, y: 0, z: 0 }, true);
    it.body.applyImpulse({ x: this.fwd.x * m * speed, y: (this.fwd.y + 0.15) * m * speed, z: this.fwd.z * m * speed }, true);
    return true;
  }

  /** Call before world.step(): drive the held body toward the hold point. */
  beforeStep() {
    const it = this.held;
    if (!it) return;
    this.camera.getWorldDirection(this.fwd);
    const o = this.camera.position;
    let d = HOLD_DIST;
    const hit = this.world.castRay(
      new RAPIER.Ray({ x: o.x, y: o.y, z: o.z }, this.fwd), HOLD_DIST + 0.3, true,
      undefined, undefined, this.playerCollider, it.body,
    );
    if (hit) d = Math.max(MIN_DIST, Math.min(HOLD_DIST, hit.timeOfImpact - 0.3));
    this.tgt.copy(o).addScaledVector(this.fwd, d);
    const p = it.body.translation();
    const dx = this.tgt.x - p.x, dy = this.tgt.y - p.y, dz = this.tgt.z - p.z;
    const dist = Math.hypot(dx, dy, dz);
    if (dist > BREAK_DIST) { this.drop(); return; }
    const k = Math.min(FOLLOW_GAIN, MAX_FOLLOW_SPEED / Math.max(dist, 1e-6));
    it.body.setLinvel({ x: dx * k, y: dy * k, z: dz * k }, true);
  }

  private respawn(it: Item) {
    if (this.held === it) this.release();
    this.respawns++;
    console.warn(`[grab] ${it.obj.name} left the world, respawning`);
    it.body.setTranslation(it.home.p, true);
    it.body.setRotation(it.home.q, true);
    it.body.setLinvel({ x: 0, y: 0, z: 0 }, true);
    it.body.setAngvel({ x: 0, y: 0, z: 0 }, true);
  }

  /** Call after world.step(): copy body transforms to meshes (sleeping bodies are skipped). */
  afterStep() {
    for (const it of this.items) {
      if (it.body.translation().y < -3) this.respawn(it);
      const sleeping = it.body.isSleeping();
      if (sleeping && !it.awake) continue;
      it.awake = !sleeping;
      const t = it.body.translation(), r = it.body.rotation();
      it.obj.position.set(t.x, t.y, t.z);
      it.obj.quaternion.set(r.x, r.y, r.z, r.w);
    }
  }
}
