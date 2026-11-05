import * as THREE from 'three/webgpu';
import RAPIER from '@dimforge/rapier3d-compat';
import type { Interaction } from './interact';
import { registerUse } from './interact/registry';
import type { GrabSystem } from './interact/grab';
import type { FirstPersonController } from './controller';
import type { AudioSystem } from './audio/audio';

// Chair body groups: member bit 3, collide with everything except the player (the player walks "through" and pushes by proximity).
const CHAIR_GROUPS = 0x0008_fffe;
// Stand-up clearance query: player membership; ignore held items (bit 2) and chairs (bit 3).
const CLEAR_GROUPS = 0x0001_fff3;
const SEAT_EYE = 1.15;
const SIT_TIME = 0.4;
const YAW_LIMIT = THREE.MathUtils.degToRad(100);
const PITCH_MIN = -1.0;
const PITCH_MAX = 0.8;
const PUSH_RADIUS = 0.62;
const FILL_TIME = 2.4;
const VEND_MOTOR = 1.0;
const VEND_SLIDE = 0.15;
const VEND_OUT = 0.2;
const TRAY_Y = 0.2;
const MAX_VENDED = 8;
const MAX_GLASSES = 6;
const TAU = Math.PI * 2;

export const SOUNDS = ['chair_creak', 'chair_roll', 'vending_hum', 'vending_drop', 'water_cooler_glug'];

interface Chair {
  obj: THREE.Object3D;
  body: RAPIER.RigidBody;
  awake: boolean;
  rollCooldown: number;
}
interface Fill { active: boolean; obj: THREE.Object3D; water: THREE.Mesh | null; t: number; spawned: boolean }

const ease = (u: number) => u * u * (3 - 2 * u);
const wrapPi = (a: number) => a - TAU * Math.round(a / TAU);
const isGlass = (o: THREE.Object3D | null) => !!o && (o.userData.caption_id === 'glass' || o.userData.caption_id === 'steel_tumbler');

/** Seating-area interactions: rolling/swivelling/sittable chairs, snack vending, water coolers. */
export class Seating {
  readonly chairs: Chair[] = [];
  sitting: Chair | null = null;
  /** Debug/harness: last water level 0..1 per glass lives in obj.userData.water_level. */
  private coolers: THREE.Object3D[] = [];
  private snacks: THREE.Object3D[] = [];
  private spirals: THREE.Object3D[] = [];
  private glassTemplate: THREE.Object3D | null = null;
  private waters = new WeakMap<THREE.Object3D, THREE.Mesh>();
  private vended = 0;
  private glasses = 0;
  private waterMat = new THREE.MeshStandardMaterial({ color: 0x9fd6f2, transparent: true, opacity: 0.6, roughness: 0.05, depthWrite: false });

  // sit state
  private sitT = 0;
  private sitAt = 0;
  private baseYaw = 0;
  private yawOff = 0;
  private yawOff0 = 0;
  private yawTarget = 0;
  private pitch = 0;
  private swivel = 0;
  private startPos = new THREE.Vector3();
  private seatPos = new THREE.Vector3();
  private q0 = new THREE.Quaternion();
  private qY = new THREE.Quaternion();
  private qTmp = { x: 0, y: 0, z: 0, w: 1 };
  private readonly UP = new THREE.Vector3(0, 1, 0);

  // scratch
  private f = new THREE.Vector3();
  private p = new THREE.Vector3();
  private qw = new THREE.Quaternion();
  private lv = { x: 0, y: 0, z: 0 };
  private prevFeet = new THREE.Vector3();
  private vel = new THREE.Vector2();
  private capsule = new RAPIER.Capsule(0.55, 0.3);
  private fills: Fill[] = Array.from({ length: 4 }, () => ({ active: false, obj: null as unknown as THREE.Object3D, water: null, t: 0, spawned: false }));

  // vending animation (one at a time, preallocated)
  private vend = { active: false, phase: 0, t: 0, obj: null as unknown as THREE.Object3D, src: null as unknown as THREE.Object3D, spiral: null as THREE.Object3D | null,
    p0: new THREE.Vector3(), pIn: new THREE.Vector3(), pOut: new THREE.Vector3(), fall: 0, tilt: new THREE.Vector3(), q0: new THREE.Quaternion(), fwd: new THREE.Vector3(), y0: 0, root: null as unknown as THREE.Object3D };

  constructor(
    private world: RAPIER.World,
    private scene: THREE.Scene,
    private camera: THREE.PerspectiveCamera,
    private interaction: Interaction,
    private grab: GrabSystem,
    private player: FirstPersonController,
    private audio: AudioSystem,
    dom: HTMLElement,
  ) {
    this.prevFeet.copy(player.feet);
    this.collect(scene);
    registerUse('chair', (o) => this.sit(o));
    registerUse('vending', (o) => this.useVending(o));
    registerUse('cooler', (o) => this.useCooler(o));
    addEventListener('keydown', (e) => {
      if (e.code !== 'KeyE' || e.repeat) return;
      if (this.sitting) { if (performance.now() - this.sitAt > 300) this.stand(); }
      else if (this.grab.held) this.fillHeld();
    });
    addEventListener('mousemove', (e) => {
      if (this.sitting && document.pointerLockElement === dom) this.look(-e.movementX * 0.0022, -e.movementY * 0.0022);
    });
  }

  // ---- setup -------------------------------------------------------------------------------------------------------

  private collect(scene: THREE.Object3D) {
    const chairs: THREE.Object3D[] = [];
    scene.traverse((o) => {
      if (o.userData.use_kind === 'chair') chairs.push(o);
      else if (o.userData.use_kind === 'cooler') this.coolers.push(o);
      else if (/^vend_snack_/.test(o.name)) this.snacks.push(o);
      else if (/^vend_spiral_/.test(o.name)) this.spirals.push(o);
      else if (!this.glassTemplate && /^glass_\d+$/.test(o.name)) this.glassTemplate = o;
    });
    for (const o of chairs) this.chairs.push(this.makeChair(o));
  }

  private makeChair(o: THREE.Object3D): Chair {
    this.scene.attach(o);
    o.updateMatrixWorld(true);
    let geo: THREE.BufferGeometry | null = null;
    o.traverse((m) => { if (!geo && (m as THREE.Mesh).isMesh) geo = (m as THREE.Mesh).geometry; });
    geo = geo as THREE.BufferGeometry | null;
    if (geo && !geo.boundingBox) geo.computeBoundingBox();
    const bb = geo?.boundingBox ?? new THREE.Box3(new THREE.Vector3(-0.25, 0, -0.22), new THREE.Vector3(0.25, 0.86, 0.22));
    // Front (local +x) trimmed so chairs pulled up to a table don't start inside the table's box collider.
    const x1 = Math.min(bb.max.x, 0.04), y0 = Math.max(bb.min.y, 0.03);
    const body = this.world.createRigidBody(
      RAPIER.RigidBodyDesc.dynamic()
        .setTranslation(o.position.x, o.position.y, o.position.z)
        .setRotation({ x: o.quaternion.x, y: o.quaternion.y, z: o.quaternion.z, w: o.quaternion.w })
        .enabledTranslations(true, false, true)
        .enabledRotations(false, true, false)
        .setLinearDamping(2.5)
        .setAngularDamping(3)
        .setCanSleep(true),
    );
    this.world.createCollider(
      RAPIER.ColliderDesc.cuboid((x1 - bb.min.x) / 2, (bb.max.y - y0) / 2, (bb.max.z - bb.min.z) / 2)
        .setTranslation((x1 + bb.min.x) / 2, (bb.max.y + y0) / 2 - o.position.y, (bb.max.z + bb.min.z) / 2)
        .setMass(Number(o.userData.mass) > 0 ? Number(o.userData.mass) : 3.5)
        .setFriction(0.05)
        .setRestitution(0.1)
        .setCollisionGroups(CHAIR_GROUPS),
      body,
    );
    return { obj: o, body, awake: true, rollCooldown: 0 };
  }

  // ---- chairs ------------------------------------------------------------------------------------------------------

  forwardOf(o: THREE.Object3D, out: THREE.Vector3) {
    o.getWorldQuaternion(this.qw);
    return out.set(1, 0, 0).applyQuaternion(this.qw);
  }

  /** E on a chair: camera glides to the seat; mouse look is limited around the chair's facing. */
  sit(o: THREE.Object3D) {
    if (this.sitting) return false;
    const ch = this.chairs.find((c) => c.obj === o);
    if (!ch) return false;
    this.sitting = ch;
    this.sitAt = performance.now();
    this.sitT = 0;
    this.forwardOf(o, this.f);
    this.baseYaw = Math.atan2(-this.f.x, -this.f.z);
    this.yawOff0 = wrapPi(this.player.yaw - this.baseYaw);
    this.yawTarget = THREE.MathUtils.clamp(this.yawOff0, -YAW_LIMIT, YAW_LIMIT);
    this.yawOff = this.yawOff0;
    this.pitch = THREE.MathUtils.clamp(this.player.pitch, PITCH_MIN, PITCH_MAX);
    this.swivel = 0;
    this.startPos.copy(this.camera.position);
    this.seatPos.set(o.position.x - this.f.x * 0.02, SEAT_EYE, o.position.z - this.f.z * 0.02);
    this.q0.copy(o.quaternion);
    ch.body.setLinvel({ x: 0, y: 0, z: 0 }, true);
    ch.body.setBodyType(RAPIER.RigidBodyType.Fixed, true);
    this.player.collider.setTranslation({ x: this.seatPos.x, y: 0.9, z: this.seatPos.z });
    this.audio.play('chair_creak', o.position);
    return true;
  }

  /** E again: stand at the first spot around the chair where the capsule fits and the path is clear. */
  stand() {
    const ch = this.sitting;
    if (!ch) return false;
    const o = ch.obj;
    this.forwardOf(o, this.f);
    const back = Math.atan2(-this.f.z, -this.f.x); // direction pointing behind the chair
    const spot = this.findStandSpot(o.position.x, o.position.z, back);
    if (!spot) { console.warn('[seating] no safe spot to stand'); return false; }
    this.sitting = null;
    this.player.teleport(spot.x, 0, spot.z, THREE.MathUtils.radToDeg(this.baseYaw + this.yawOff));
    this.player.yaw = this.baseYaw + this.yawOff;
    this.player.pitch = this.pitch;
    this.prevFeet.copy(this.player.feet);
    ch.body.setBodyType(RAPIER.RigidBodyType.Dynamic, true);
    ch.body.setTranslation({ x: o.position.x, y: o.position.y, z: o.position.z }, true);
    ch.awake = true;
    this.audio.play('chair_creak', o.position);
    return true;
  }

  private spot = { x: 0, z: 0 };
  private findStandSpot(cx: number, cz: number, back: number) {
    const ang = [0, 0.8, -0.8, 1.57, -1.57, 2.4, -2.4, Math.PI];
    for (const r of [0.75, 1.0, 1.3]) {
      for (const a of ang) {
        const x = cx + Math.cos(back + a) * r, z = cz + Math.sin(back + a) * r;
        if (this.isClear(x, z, cx, cz)) { this.spot.x = x; this.spot.z = z; return this.spot; }
      }
    }
    return null;
  }

  /** True if a standing capsule fits at (x, z) and nothing solid lies between (fromX, fromZ) and it. */
  isClear(x: number, z: number, fromX = x, fromZ = z) {
    const hit = this.world.intersectionWithShape({ x, y: 0.9, z }, { x: 0, y: 0, z: 0, w: 1 }, this.capsule, undefined, CLEAR_GROUPS, this.player.collider);
    if (hit) return false;
    const dx = x - fromX, dz = z - fromZ, d = Math.hypot(dx, dz);
    if (d < 1e-4) return true;
    const ray = new RAPIER.Ray({ x: fromX, y: 0.9, z: fromZ }, { x: dx / d, y: 0, z: dz / d });
    return !this.world.castRay(ray, d, true, undefined, CLEAR_GROUPS, this.player.collider);
  }

  look(dyaw: number, dpitch: number) {
    if (!this.sitting) return;
    this.yawOff = THREE.MathUtils.clamp(this.yawOff + dyaw, -YAW_LIMIT, YAW_LIMIT);
    this.yawTarget = this.yawOff;
    this.pitch = THREE.MathUtils.clamp(this.pitch + dpitch, PITCH_MIN, PITCH_MAX);
  }

  get yaw() { return this.baseYaw + this.yawOff; }

  // ---- vending -----------------------------------------------------------------------------------------------------

  useVending(root: THREE.Object3D) {
    const v = this.vend;
    if (v.active || this.sitting) return false;
    const src = this.snacks.find((s) => s.visible);
    if (!src || this.vended >= MAX_VENDED) { console.log('[vending] sold out'); return false; }
    this.vended++;
    src.visible = false;
    const o = src.clone();
    o.visible = true;
    o.userData = { interact: 'grab', mass: 0.06, collider: 'box', caption_id: 'snack_packet', static: 0 };
    o.name = `vend_snack_dispensed_${this.vended}`;
    src.getWorldPosition(v.p0);
    src.getWorldQuaternion(v.q0);
    this.scene.add(o);
    o.position.copy(v.p0);
    o.quaternion.copy(v.q0);
    v.obj = o; v.src = src; v.root = root;
    this.forwardOf(root, v.fwd);
    root.getWorldPosition(this.p);
    v.pIn.set(this.p.x + v.fwd.x * 0.3, TRAY_Y, this.p.z + v.fwd.z * 0.3);
    v.pOut.set(this.p.x + v.fwd.x * 0.52, TRAY_Y + 0.02, this.p.z + v.fwd.z * 0.52);
    v.tilt.set(-v.fwd.z, 0, v.fwd.x);
    v.y0 = v.p0.y;
    v.fall = Math.sqrt((2 * Math.max(0.1, v.y0 - TRAY_Y)) / 9.81);
    // nearest spiral (same row/column) turns while the motor runs
    let best = Infinity;
    v.spiral = null;
    for (const s of this.spirals) {
      s.getWorldPosition(this.p);
      const d = this.p.distanceToSquared(v.p0);
      if (d < best) { best = d; v.spiral = s; }
    }
    v.phase = 0; v.t = 0; v.active = true;
    this.audio.play('vending_hum', root.getWorldPosition(this.p), VEND_MOTOR + 0.2);
    return true;
  }

  private updateVending(dt: number) {
    const v = this.vend;
    if (!v.active) return;
    v.t += dt;
    const o = v.obj;
    if (v.phase === 0) {
      v.spiral?.rotateX((TAU * dt) / VEND_MOTOR);
      o.position.x = v.p0.x + Math.sin(v.t * 60) * 0.0008 * v.fwd.z; // motor shudder
      if (v.t >= VEND_MOTOR) { v.phase = 1; v.t = 0; o.position.copy(v.p0); }
    } else if (v.phase === 1) {
      // nudge off the spiral, then fall to the tray under gravity while drifting toward the flap
      const slide = Math.min(1, v.t / VEND_SLIDE);
      const tf = Math.max(0, v.t - VEND_SLIDE), u = Math.min(1, tf / v.fall);
      const nx = v.p0.x + v.fwd.x * 0.05 * slide, nz = v.p0.z + v.fwd.z * 0.05 * slide;
      o.position.x = nx + (v.pIn.x - nx) * u;
      o.position.z = nz + (v.pIn.z - nz) * u;
      o.position.y = Math.max(TRAY_Y, v.y0 - 0.5 * 9.81 * tf * tf);
      this.qY.setFromAxisAngle(v.tilt, 0.6 * Math.sin(Math.PI * u));
      o.quaternion.copy(this.qY).multiply(v.q0);
      if (u >= 1) {
        v.phase = 2; v.t = 0;
        this.audio.play('vending_drop', v.pIn);
      }
    } else {
      const u = ease(Math.min(1, v.t / VEND_OUT));
      o.position.lerpVectors(v.pIn, v.pOut, u);
      if (v.t >= VEND_OUT) this.finishVend();
    }
  }

  private finishVend() {
    const v = this.vend;
    v.active = false;
    this.grab.register(v.obj, this.scene);
    const it = this.grab.items.find((i) => i.obj === v.obj);
    if (it) it.body.setLinvel({ x: v.fwd.x * 0.8, y: 0, z: v.fwd.z * 0.8 }, true);
    this.interaction.refresh();
  }

  // ---- water coolers -----------------------------------------------------------------------------------------------

  /** E at a cooler with empty hands: a glass appears under the tap, fills, and ends up in your hand. */
  useCooler(cooler: THREE.Object3D) {
    if (this.sitting) return false;
    if (this.grab.held) return this.fillHeld();
    if (!this.glassTemplate || this.glasses >= MAX_GLASSES) return false;
    const slot = this.freeFill();
    if (!slot) return false;
    this.glasses++;
    const g = this.glassTemplate.clone();
    for (let i = g.children.length - 1; i >= 0; i--) if (g.children[i].name === 'water') g.remove(g.children[i]);
    g.userData = { interact: 'grab', mass: 0.25, collider: 'box', caption_id: 'glass', static: 0 };
    g.name = `glass_cooler_${this.glasses}`;
    this.forwardOf(cooler, this.f);
    cooler.getWorldPosition(this.p);
    g.position.set(this.p.x + this.f.x * 0.3, 0.43, this.p.z + this.f.z * 0.3);
    g.quaternion.identity();
    this.scene.add(g);
    this.grab.register(g, this.scene);
    const it = this.grab.items.find((i) => i.obj === g)!;
    it.body.setBodyType(RAPIER.RigidBodyType.Fixed, true); // sits under the tap while filling
    this.interaction.refresh();
    this.startFill(slot, g, true, cooler.getWorldPosition(this.p));
    return true;
  }

  /** E while carrying a glass near a cooler: fill it. */
  fillHeld() {
    const h = this.grab.held;
    if (!h || !isGlass(h.obj) || h.obj.userData.water_level >= 1) return false;
    const cam = this.camera.position;
    this.camera.getWorldDirection(this.f);
    for (const c of this.coolers) {
      c.getWorldPosition(this.p);
      const dx = this.p.x - cam.x, dz = this.p.z - cam.z, d = Math.hypot(dx, dz);
      if (d > 1.6 || (dx * this.f.x + dz * this.f.z) / Math.max(d, 1e-6) < 0.5) continue;
      const slot = this.freeFill();
      if (!slot) return false;
      this.startFill(slot, h.obj, false, this.p);
      return true;
    }
    return false;
  }

  private freeFill() { return this.fills.find((f) => !f.active) ?? null; }

  private startFill(slot: Fill, obj: THREE.Object3D, spawned: boolean, at: THREE.Vector3) {
    let w = this.waters.get(obj);
    if (!w) this.waters.set(obj, (w = this.makeWater(obj)));
    obj.userData.water_level = 0;
    slot.active = true; slot.obj = obj; slot.water = w; slot.t = 0; slot.spawned = spawned;
    slot.water!.scale.y = 0.001;
    slot.water!.visible = true;
    this.audio.play('water_cooler_glug', at, FILL_TIME + 0.2);
  }

  private makeWater(obj: THREE.Object3D) {
    let geo: THREE.BufferGeometry | null = null;
    obj.traverse((m) => { if (!geo && (m as THREE.Mesh).isMesh) geo = (m as THREE.Mesh).geometry; });
    const g0 = geo as unknown as THREE.BufferGeometry;
    if (!g0.boundingBox) g0.computeBoundingBox();
    const bb = g0.boundingBox!;
    const hw = Math.min(bb.max.x - bb.min.x, bb.max.z - bb.min.z) / 2;
    const h = (bb.max.y - bb.min.y) * 0.72;
    const cg = new THREE.CylinderGeometry(hw * 0.86, hw * 0.68, 1, 16);
    cg.translate(0, 0.5, 0); // base at y = 0 so scale.y grows upward
    const m = new THREE.Mesh(cg, this.waterMat);
    m.name = 'water';
    m.position.set((bb.max.x + bb.min.x) / 2, bb.min.y + 0.015, (bb.max.z + bb.min.z) / 2);
    m.userData.fullHeight = h;
    m.scale.set(1, 0.001, 1);
    m.raycast = () => {}; // never block aiming
    obj.add(m);
    return m;
  }

  private updateFills(dt: number) {
    for (const f of this.fills) {
      if (!f.active) continue;
      f.t += dt;
      const u = Math.min(1, f.t / FILL_TIME);
      f.obj.userData.water_level = u;
      f.water!.scale.y = Math.max(0.001, f.water!.userData.fullHeight * u);
      if (u < 1) continue;
      f.active = false;
      if (f.spawned) {
        const it = this.grab.items.find((i) => i.obj === f.obj);
        if (it) {
          it.body.setBodyType(RAPIER.RigidBodyType.Dynamic, true);
          if (!this.grab.held) this.grab.pickItem(it);
        }
      }
    }
  }

  // ---- per frame ---------------------------------------------------------------------------------------------------

  update(dt: number) {
    if (dt <= 0) return;
    this.updateFills(dt);
    this.updateVending(dt);
    if (this.sitting) this.updateSeated(dt);
    else this.updateChairs(dt);
    this.prevFeet.copy(this.player.feet);
  }

  private updateSeated(dt: number) {
    const ch = this.sitting!;
    if (this.sitT < 1) {
      this.sitT = Math.min(1, this.sitT + dt / SIT_TIME);
      const e = ease(this.sitT);
      this.camera.position.lerpVectors(this.startPos, this.seatPos, e);
      this.yawOff = this.yawOff0 + (this.yawTarget - this.yawOff0) * e;
    } else this.camera.position.copy(this.seatPos);
    this.camera.rotation.set(this.pitch, this.baseYaw + this.yawOff, 0, 'YXZ');
    // swivel: the seat turns after the head (slightly lagging)
    this.swivel += (this.yawOff * 0.7 - this.swivel) * Math.min(1, dt * 4);
    this.qY.setFromAxisAngle(this.UP, this.swivel).multiply(this.q0);
    ch.obj.quaternion.copy(this.qY);
    this.qTmp.x = this.qY.x; this.qTmp.y = this.qY.y; this.qTmp.z = this.qY.z; this.qTmp.w = this.qY.w;
    ch.body.setRotation(this.qTmp, true);
  }

  private updateChairs(dt: number) {
    const feet = this.player.feet;
    this.vel.set((feet.x - this.prevFeet.x) / dt, (feet.z - this.prevFeet.z) / dt);
    const speed = this.vel.length();
    for (const c of this.chairs) {
      const o = c.obj;
      if (c.rollCooldown > 0) c.rollCooldown -= dt;
      // Walking into a chair shoves it along (the player capsule itself passes through chairs).
      if (speed > 0.3 && Math.abs(o.position.x - feet.x) < PUSH_RADIUS && Math.abs(o.position.z - feet.z) < PUSH_RADIUS) {
        const dx = o.position.x - feet.x, dz = o.position.z - feet.z, d = Math.hypot(dx, dz);
        if (d < PUSH_RADIUS && d > 1e-4 && (this.vel.x * dx + this.vel.y * dz) / (d * speed) > 0.3) {
          this.lv.x = (dx / d) * speed * 1.1; this.lv.z = (dz / d) * speed * 1.1;
          c.body.setLinvel(this.lv, true);
          if (c.rollCooldown <= 0) { this.audio.play('chair_roll', o.position, 1.2); c.rollCooldown = 2.5; }
        }
      }
      const sleeping = c.body.isSleeping();
      if (sleeping && !c.awake) continue;
      c.awake = !sleeping;
      const t = c.body.translation(), r = c.body.rotation();
      o.position.set(t.x, t.y, t.z);
      o.quaternion.set(r.x, r.y, r.z, r.w);
    }
  }
}
