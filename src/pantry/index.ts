import * as THREE from 'three/webgpu';
import RAPIER from '@dimforge/rapier3d-compat';
import type { Interaction } from '../interact';
import type { GrabSystem } from '../interact/grab';
import type { AudioSystem } from '../audio/audio';
import type { FirstPersonController } from '../controller';
import { registerUse, triggerUse } from '../interact/registry';
import { EasedLight, Glow, Steam, Stream, approach, smooth } from './fx';
import { Hinge } from './hinge';

export const SOUNDS = [
  'coffee_grind', 'coffee_pour', 'steam_hiss', 'microwave_hum', 'microwave_beep', 'microwave_door_open', 'microwave_door_close',
  'fridge_door_open', 'fridge_door_close', 'fridge_hum', 'kettle_boil', 'kettle_click', 'sink_tap', 'cabinet_open', 'cabinet_close',
];

const DOOR_SOUNDS: Record<string, [string, string]> = {
  fridge_door: ['fridge_door_open', 'fridge_door_close'],
  microwave: ['microwave_door_open', 'microwave_door_close'],
  cabinet_door: ['cabinet_open', 'cabinet_close'],
};
const GRIND = 2.2, POUR = 2.4, MW_TIME = 10, KETTLE_TIME = 4.5;

interface Ctx {
  scene: THREE.Scene; world: RAPIER.World; interaction: Interaction; grab: GrabSystem; audio: AudioSystem; player: FirstPersonController;
}

/** Pantry Use items (coffee machine, microwave, fridge, kettle, sink, cabinet doors). Call `update(dt)` every frame. */
export function initPantry({ scene, world, interaction, grab, audio, player }: Ctx) {
  const find = (n: string) => scene.getObjectByName(n) ?? null;
  const V = (x: number, y: number, z: number) => new THREE.Vector3(x, y, z);
  const origin = (o: THREE.Object3D) => o.getWorldPosition(new THREE.Vector3());
  scene.updateMatrixWorld(true);

  // ---- hinged doors ------------------------------------------------------------------------------------------------
  const hinges = new Map<THREE.Object3D, Hinge>();
  scene.traverse((o) => {
    if (o.userData.hinge_axis) hinges.set(o, new Hinge(o, world, player.collider));
  });
  const doorPos = new THREE.Vector3();
  const mugsBehind = new Map<Hinge, typeof grab.items>();
  const cabinet = find('wall_cabinet_body');
  const cabBox = cabinet ? new THREE.Box3().setFromObject(cabinet) : null;
  for (const [door, h] of hinges) {
    if (door.userData.use_kind !== 'cabinet_door' || door.parent !== cabinet || !cabBox) continue;
    const db = new THREE.Box3().setFromObject(door);
    const list = grab.items.filter((it) => {
      const p = it.obj.position;
      return it.obj.name.startsWith('mug') && p.y > cabBox.min.y + 0.2 && p.x > cabBox.min.x && p.z > db.min.z && p.z < db.max.z;
    });
    for (const it of list) it.body.sleep(); // asleep until their door opens
    mugsBehind.set(h, list);
  }
  let fridgeHum: AudioBufferSourceNode | null = null;
  const fridgeDoors = () => [...hinges.values()].filter((h) => h.obj.userData.use_kind === 'fridge_door');
  const toggleDoor = (obj: THREE.Object3D) => {
    const h = hinges.get(obj);
    if (!h) return;
    const opening = h.toggle();
    const s = DOOR_SOUNDS[String(obj.userData.use_kind)];
    if (s) audio.play(s[opening ? 0 : 1], obj.getWorldPosition(doorPos));
    if (obj.userData.use_kind === 'fridge_door') { // compressor hum while any fridge door is open
      if (opening && !fridgeHum) fridgeHum = audio.play('fridge_hum', obj.getWorldPosition(doorPos), 0, true) ?? null;
      if (!fridgeDoors().some((d) => d.target !== 0)) { try { fridgeHum?.stop(); } catch { /* stopped */ } fridgeHum = null; }
    }
    if (opening) for (const it of mugsBehind.get(h) ?? []) it.body.wakeUp();
  };

  // ---- fridge ------------------------------------------------------------------------------------------------------
  const fridgeDoorList = fridgeDoors();
  const glowFor = (h: Hinge, behind: boolean, color: number, max: number, inset: number) => {
    const b = new THREE.Box3().setFromObject(h.obj); // closed pose
    const c = b.getCenter(new THREE.Vector3());
    c.x = behind ? b.max.x + 0.003 : b.min.x - 0.004;
    return new Glow(scene, c, b.max.z - b.min.z - 2 * inset, b.max.y - b.min.y - 2 * inset, color, max);
  };
  const fridgeGlows = fridgeDoorList.map((h) => glowFor(h, true, 0xdce9ff, 0.9, 0.03));
  const fridgeCenter = fridgeDoorList.length
    ? fridgeDoorList.reduce((a, h) => a.add(origin(h.obj)), new THREE.Vector3()).divideScalar(fridgeDoorList.length)
    : V(0, 0, 0);
  const fridgeLight = new EasedLight(scene, V(fridgeCenter.x - 0.25, fridgeCenter.y + 0.2, fridgeCenter.z - 0.25), 0xdce9ff, 3, 2.5);

  // ---- microwave ---------------------------------------------------------------------------------------------------
  const mw = find('lg_microwave');
  const mwDoor = find('lg_microwave_door');
  const mwHinge = mwDoor ? hinges.get(mwDoor) ?? null : null;
  const mwOpenGlow = mwHinge ? glowFor(mwHinge, true, 0xfff0d0, 0.9, 0.025) : null;
  const mwRunGlow = mwHinge ? glowFor(mwHinge, false, 0xffd9a0, 0.55, 0.03) : null;
  const mwLight = new EasedLight(scene, mw ? origin(mw).add(V(-0.25, 0, 0)) : V(0, 0, 0), 0xffd9a0, 1.2, 1.5);
  const canvas = document.createElement('canvas');
  canvas.width = 128; canvas.height = 32;
  const g2 = canvas.getContext('2d')!;
  const dispTex = new THREE.CanvasTexture(canvas);
  dispTex.colorSpace = THREE.SRGBColorSpace;
  const drawDisplay = (txt: string) => {
    g2.clearRect(0, 0, 128, 32);
    g2.fillStyle = '#7dffb0'; g2.font = 'bold 28px monospace'; g2.textAlign = 'center'; g2.textBaseline = 'middle';
    g2.fillText(txt, 64, 17);
    dispTex.needsUpdate = true;
  };
  drawDisplay('');
  if (mw) {
    const d = new THREE.Mesh(new THREE.PlaneGeometry(0.066, 0.0165), new THREE.MeshBasicMaterial({ map: dispTex, transparent: true, depthWrite: false, toneMapped: false }));
    d.position.copy(origin(mw)).add(V(-0.166, 0.079, 0.1375));
    d.rotation.y = -Math.PI / 2;
    d.renderOrder = 4;
    scene.add(d);
  }
  const mwState = { running: false, delay: 0, t: 0, shown: -1, hum: null as AudioBufferSourceNode | null, flash: 0 };
  const mwUse = (obj: THREE.Object3D) => {
    if (obj === mwDoor) return toggleDoor(obj);
    if (mwState.running) return; // already cooking
    mwState.running = true; mwState.t = 0; mwState.shown = -1;
    mwState.delay = 0;
    if (mwHinge && mwHinge.target === 1) { toggleDoor(mwDoor!); mwState.delay = 0.9; }
    else if (mw) mwState.hum = audio.play('microwave_hum', origin(mw), 0, true);
  };

  // ---- coffee machine ----------------------------------------------------------------------------------------------
  const machine = find('tata_bistro_machine');
  const nozzle = machine ? origin(machine).add(V(-0.115, 0.215, -0.07)) : V(0, 0, 0);
  const mugSpot = machine ? origin(machine).add(V(-0.115, 0.07, -0.07)) : V(0, 0, 0);
  const coffeeStream = new Stream(scene, 0x3a1d0c, 0.95);
  const coffeeSteam = new Steam(scene, 10, 0.07, 0.3, 0.28, 8);
  const mugProto = find('mug_olive_counter')?.clone(true) ?? null; // pristine template for spawning (no coffee disc)
  const discGeo = new THREE.CircleGeometry(0.0355, 20).rotateX(-Math.PI / 2);
  const discMat = new THREE.MeshStandardMaterial({ color: 0x2b1609, roughness: 0.2 });
  const addDisc = (mug: THREE.Object3D) => {
    const d = new THREE.Mesh(discGeo, discMat);
    d.name = 'coffee_surface';
    d.position.y = 0.02;
    d.scale.setScalar(1e-4);
    d.userData = { collider: 'none' };
    mug.add(d);
    return d;
  };
  for (const it of grab.items) if (it.obj.name.startsWith('mug')) addDisc(it.obj);
  let spawned = 0;
  const cof = { phase: 0, t: 0, mug: null as THREE.Object3D | null, item: null as (typeof grab.items)[number] | null, steamT: 0 };
  const mugUnderSpout = () => {
    for (const it of grab.items) {
      if (!it.obj.name.startsWith('mug') || grab.held === it) continue;
      const p = it.obj.position;
      if (Math.hypot(p.x - mugSpot.x, p.z - mugSpot.z) < 0.1 && Math.abs(p.y - mugSpot.y) < 0.15) return it;
    }
    return null;
  };
  const coffeeUse = () => {
    if (!machine || (cof.phase !== 0 && cof.phase !== 3)) return;
    let it = mugUnderSpout();
    if (!it) {
      if (!mugProto) return;
      const m = mugProto.clone(true);
      m.name = `mug_spawn_${++spawned}`;
      scene.add(m);
      grab.register(scene, scene);
      it = grab.items.find((i) => i.obj === m) ?? null;
      if (!it) return;
      addDisc(m);
      interaction.refresh();
    }
    cof.item = it; cof.mug = it.obj; cof.phase = 1; cof.t = 0;
    const m = it.obj;
    m.position.copy(mugSpot);
    m.quaternion.identity();
    it.body.setTranslation(mugSpot, true);
    it.body.setRotation({ x: 0, y: 0, z: 0, w: 1 }, true);
    it.body.setLinvel({ x: 0, y: 0, z: 0 }, true);
    it.body.setAngvel({ x: 0, y: 0, z: 0 }, true);
    it.body.setBodyType(RAPIER.RigidBodyType.Fixed, true);
    m.userData.interact = 'look'; // can't be grabbed while brewing
    const disc = m.getObjectByName('coffee_surface');
    if (disc) disc.scale.setScalar(1e-4);
    audio.play('coffee_grind', nozzle, GRIND);
  };

  // ---- kettle ------------------------------------------------------------------------------------------------------
  const kettleObj = find('kettle_01');
  const kettleSteam = new Steam(scene, 8, 0.05, 0.22, 0.22, 6);
  if (kettleObj) kettleSteam.origin.copy(origin(kettleObj)).add(V(-0.12, 0.2, 0));
  const ket = { on: false, t: 0, node: null as AudioBufferSourceNode | null };
  const stopNode = (n: AudioBufferSourceNode | null) => { try { n?.stop(); } catch { /* already stopped */ } };
  const kettleUse = () => {
    if (!kettleObj) return;
    ket.on = !ket.on;
    ket.t = 0;
    kettleSteam.emitting = ket.on;
    if (ket.on) ket.node = audio.play('kettle_boil', origin(kettleObj), 0, true);
    else { stopNode(ket.node); ket.node = null; audio.play('kettle_click', origin(kettleObj)); }
  };

  // ---- sink --------------------------------------------------------------------------------------------------------
  const faucet = find('sink_faucet');
  const tip = faucet ? origin(faucet).add(V(-0.0975, 0.2546, 0)) : V(0, 0, 0);
  const bowlY = faucet ? origin(faucet).y - 0.17 : 0;
  const water = new Stream(scene, 0xbfe3ff, 0.55);
  const splash = new THREE.Mesh(new THREE.CircleGeometry(1, 16).rotateX(-Math.PI / 2), new THREE.MeshBasicMaterial({ color: 0xdff2ff, transparent: true, opacity: 0, depthWrite: false }));
  splash.scale.setScalar(1e-4);
  scene.add(splash);
  const sink = { on: false, flow: 0, node: null as AudioBufferSourceNode | null };
  const sinkUse = () => {
    if (!faucet) return;
    sink.on = !sink.on;
    if (sink.on) sink.node = audio.play('sink_tap', tip, 0, true);
    else { stopNode(sink.node); sink.node = null; }
  };

  // ---- use handlers ------------------------------------------------------------------------------------------------
  const doorOr = (fallback: (o: THREE.Object3D) => void) => (o: THREE.Object3D) => (hinges.has(o) ? toggleDoor(o) : fallback(o));
  registerUse('fridge_door', toggleDoor);
  registerUse('cabinet_door', toggleDoor);
  registerUse('microwave', mwUse);
  registerUse('coffee_machine', doorOr(coffeeUse));
  registerUse('kettle', kettleUse);
  registerUse('sink', sinkUse);

  const mugTop = V(0, 0, 0);
  let clock = 0;
  return {
    hinges,
    /** Harness hook: use an item as if E were pressed on it. */
    use(name: string) { const o = find(name); if (o) triggerUse(o); return !!o; },
    state() {
      return {
        doors: Object.fromEntries([...hinges].map(([o, h]) => [o.name, h.p])),
        bounced: [...hinges.values()].reduce((a, h) => a + h.bounced, 0),
        coffeePhase: cof.phase, mw: mwState.running, kettle: ket.on, sink: sink.on,
        filled: grab.items.filter((i) => i.obj.userData.filled).map((i) => i.obj.name),
        sleepingMugs: [...mugsBehind.values()].flat().filter((i) => i.body.isSleeping()).length,
      };
    },
    busy() {
      return cof.phase === 1 || cof.phase === 2 || mwState.running || [...hinges.values()].some((h) => h.moving);
    },
    update(dt: number) {
      clock += dt;
      for (const h of hinges.values()) h.update(dt);

      // fridge + microwave open glow / lights
      let anyOpen = 0;
      fridgeDoorList.forEach((h, i) => { const l = Math.min(1, h.p * 4); fridgeGlows[i].target = l; fridgeGlows[i].level = l; fridgeGlows[i].update(0); anyOpen = Math.max(anyOpen, l); });
      fridgeLight.target = anyOpen; fridgeLight.update(dt);
      if (mwHinge && mwOpenGlow && mwRunGlow) {
        const open = Math.min(1, mwHinge.p * 4);
        mwOpenGlow.target = mwOpenGlow.level = open; mwOpenGlow.update(0);
        mwRunGlow.target = mwState.running && mwState.delay <= 0 ? 0.8 + 0.2 * Math.sin(clock * 30) : 0;
        mwRunGlow.update(dt, 8);
        mwLight.target = Math.max(open * 0.6, mwRunGlow.target);
        mwLight.update(dt);
      }

      // microwave countdown
      if (mwState.running) {
        if (mwState.delay > 0) {
          mwState.delay -= dt;
          if (mwState.delay <= 0 && mw) { mwState.hum = audio.play('microwave_hum', origin(mw), 0, true); mwState.t = 0; }
        } else {
          mwState.t += dt;
          const left = Math.max(0, Math.ceil(MW_TIME - mwState.t));
          if (left !== mwState.shown) { mwState.shown = left; drawDisplay(`0:${String(left).padStart(2, '0')}`); }
          if (mwState.t >= MW_TIME) {
            mwState.running = false; mwState.flash = 1.2;
            stopNode(mwState.hum); mwState.hum = null;
            if (mw) audio.play('microwave_beep', origin(mw), 1.6);
          }
        }
      } else if (mwState.flash > 0 && (mwState.flash -= dt) <= 0) drawDisplay('');
      if (mwState.running && mwState.delay > 0 && mwState.shown < 0) { mwState.shown = -2; drawDisplay(`0:${MW_TIME < 10 ? '0' : ''}${MW_TIME}`); }

      // coffee
      if (cof.phase === 1 || cof.phase === 2) {
        cof.t += dt;
        if (cof.phase === 1 && cof.t >= GRIND) { cof.phase = 2; cof.t = 0; audio.play('coffee_pour', nozzle); audio.play('steam_hiss', nozzle, 1.2); }
        if (cof.phase === 2) {
          const e = Math.min(1, cof.t / POUR);
          const flow = smooth(Math.min(1, cof.t / 0.2)) * (1 - smooth(Math.max(0, (e - 0.9) / 0.1)));
          const surf = mugSpot.y + 0.02 + 0.058 * smooth(e);
          coffeeStream.set(nozzle.x, nozzle.y, nozzle.z, surf, 0.0045, flow, clock);
          const disc = cof.mug!.getObjectByName('coffee_surface');
          if (disc) { disc.position.y = 0.02 + 0.058 * smooth(e); disc.scale.setScalar(Math.max(1e-4, smooth(Math.min(1, e * 4)))); }
          if (cof.t >= POUR) {
            coffeeStream.set(nozzle.x, nozzle.y, nozzle.z, surf, 0.0045, 0, clock);
            cof.mug!.userData.interact = 'grab';
            cof.mug!.userData.filled = true;
            cof.item!.body.setBodyType(RAPIER.RigidBodyType.Dynamic, true);
            cof.item!.body.wakeUp();
            cof.phase = 3; cof.t = 0;
            coffeeSteam.emitting = true;
          }
        }
      } else if (cof.phase === 3) {
        cof.t += dt;
        cof.mug!.getWorldPosition(mugTop);
        coffeeSteam.origin.set(mugTop.x, mugTop.y + 0.09, mugTop.z);
        if (cof.t > 6) { coffeeSteam.emitting = false; cof.phase = 0; }
      }
      coffeeSteam.update(dt);

      // kettle
      if (ket.on) {
        ket.t += dt;
        if (ket.t >= KETTLE_TIME) kettleUse();
      }
      kettleSteam.update(dt);

      // sink
      sink.flow = approach(sink.flow, sink.on ? 1 : 0, dt * 4);
      water.set(tip.x, tip.y, tip.z, bowlY, 0.0055, sink.flow, clock);
      splash.position.set(tip.x, bowlY + 0.003, tip.z);
      splash.scale.setScalar(Math.max(1e-4, sink.flow * (0.03 + 0.006 * Math.sin(clock * 40))));
      (splash.material as THREE.MeshBasicMaterial).opacity = sink.flow * 0.5;
    },
  };
}
