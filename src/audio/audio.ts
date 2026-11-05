import * as THREE from 'three/webgpu';

interface Def { files: string[]; loop: boolean; volume: number }
interface Settings { volume: number; muted: boolean }
const KEY = 'cctech.audio';
const FOOT = ['footstep_tile_1', 'footstep_tile_2', 'footstep_tile_3', 'footstep_tile_4'];
const SETDOWN: Record<string, string[]> = { glass: ['glass_set_down'], mug: ['mug_set_down_1', 'mug_set_down_2', 'mug_clink'] };
export const AMBIENCE = ['office_room_tone', 'ac_hum', 'city_distant'];
/** Sounds the engine itself plays (footsteps, set-downs, ambience, light switch); always preloaded. */
export const CORE_SOUNDS = [...FOOT, ...AMBIENCE, 'glass_set_down', 'mug_set_down_1', 'mug_set_down_2', 'mug_clink', 'light_switch_on', 'light_switch_off'];

let current: AudioSystem | null = null;
/** Fire-and-forget global helper (e.g. the light switch: `playSound('switch_on')`); aliases switch_on/off map to light_switch_*. */
export function playSound(name: string, pos?: THREE.Vector3) {
  return current?.play(name.startsWith('switch_') ? `light_${name}` : name, pos) ?? null;
}

/**
 * Tiny WebAudio helper driven by public/audio/manifest.json (ogg for Chrome/Firefox, m4a for Safari).
 * Buffers decode once up front; `play` only creates source/gain/panner nodes (no per-frame cost).
 * `count` records plays per sound (also used by harness checks, works while the context is suspended).
 */
export class AudioSystem {
  readonly count: Record<string, number> = {};
  private ctx: AudioContext | null = null;
  private defs: Record<string, Def> = {};
  private buffers = new Map<string, AudioBuffer>();
  private base = `${import.meta.env.BASE_URL}audio/`;
  private ready: Promise<void> | null = null;
  private master: GainNode | null = null;
  private settings: Settings = { volume: 0.8, muted: false };
  readonly listeners = new Set<() => void>();
  /** World point of the window wall that the faint city ambience comes from (set by main/harness). */
  windowPos: THREE.Vector3 | null = null;
  private cityGain: GainNode | null = null;
  private ambienceOn = false;
  private stride = 0;
  private stepIdx = 0;
  private lastFeet = new THREE.Vector3();
  private haveFeet = false;
  private lastSpeed = new Map<object, number>();
  private lastSet = new Map<object, number>();
  private clock = 0;

  constructor(private camera: THREE.Camera, preload: string[] = []) {
    try { this.ctx = new AudioContext(); } catch { this.ctx = null; }
    try {
      const o = JSON.parse(localStorage.getItem(KEY) ?? 'null');
      if (o && typeof o.volume === 'number') this.settings = { volume: THREE.MathUtils.clamp(o.volume, 0, 1), muted: !!o.muted };
    } catch { /* storage unavailable */ }
    if (this.ctx) {
      this.master = this.ctx.createGain();
      this.master.connect(this.ctx.destination);
      this.applyMaster();
    }
    // Unlock on the first user gesture (the pointer-lock click counts).
    const resume = () => { void this.ctx?.resume(); };
    for (const ev of ['pointerdown', 'click', 'keydown']) addEventListener(ev, resume);
    addEventListener('keydown', (e) => { if (e.code === 'KeyM' && !e.repeat) this.setMuted(!this.settings.muted); });
    current = this;
    this.ready = this.load([...new Set([...CORE_SOUNDS, ...preload])]);
  }

  get muted() { return this.settings.muted; }
  get volume() { return this.settings.volume; }
  get masterLevel() { return this.master?.gain.value ?? 0; }
  setMuted(m: boolean) { this.settings.muted = m; this.applyMaster(); this.save(); }
  setVolume(v: number) { this.settings.volume = THREE.MathUtils.clamp(v, 0, 1); this.applyMaster(); this.save(); }
  private applyMaster() {
    if (this.master) this.master.gain.value = this.settings.muted ? 0 : this.settings.volume;
    this.listeners.forEach((f) => f());
  }
  private save() { try { localStorage.setItem(KEY, JSON.stringify(this.settings)); } catch { /* ignore */ } }

  private async load(names: string[]) {
    if (!this.ctx) return;
    try {
      this.defs = (await (await fetch(`${this.base}manifest.json`)).json()).sounds;
    } catch { return; }
    for (const n of names) await this.decode(n); // sequential: decode runs off-thread, one at a time keeps frames smooth
    this.startAmbience();
  }

  /** Room tone + AC hum (flat) and city ambience (volume follows distance to the window wall). Idempotent. */
  startAmbience() {
    if (this.ambienceOn || !this.ctx || !this.buffers.has('ac_hum')) return;
    this.ambienceOn = true;
    this.play('office_room_tone', undefined, 0, true);
    this.play('ac_hum', undefined, 0, true);
    this.play('city_distant', undefined, 0, true, (g) => { this.cityGain = g; g.gain.value = 0; });
  }

  /** Per-frame: footsteps (stride based), set-down clinks (sudden speed loss of grab items), city volume. */
  update(dt: number, feet: THREE.Vector3, active: boolean, items: { obj: THREE.Object3D; body: { linvel(): { x: number; y: number; z: number }; isSleeping(): boolean } }[] = []) {
    this.clock += dt;
    if (this.haveFeet && active) {
      const d = Math.hypot(feet.x - this.lastFeet.x, feet.z - this.lastFeet.z);
      if (d < 0.5 && Math.abs(feet.y - this.lastFeet.y) < 0.2 && dt > 0) {
        const sprint = d / dt > 3.2;
        this.stride += d;
        if (this.stride >= (sprint ? 1.25 : 0.8)) {
          this.stride = 0;
          this.stepIdx = (this.stepIdx + 1 + Math.floor(Math.random() * 3)) % FOOT.length; // never repeat back-to-back
          this.play(FOOT[this.stepIdx], undefined, 0, false, undefined, (sprint ? 1.15 : 0.9) * (0.85 + Math.random() * 0.3), 0.92 + Math.random() * 0.16);
        }
      }
    }
    this.lastFeet.copy(feet);
    this.haveFeet = true;
    for (const it of items) {
      const v = it.body.linvel();
      const sp = Math.hypot(v.x, v.y, v.z);
      const prev = this.lastSpeed.get(it) ?? 0;
      this.lastSpeed.set(it, sp);
      if (prev - sp > 1.2 && prev > 1.5 && this.clock - (this.lastSet.get(it) ?? -9) > 0.25) {
        this.lastSet.set(it, this.clock);
        const n = it.obj.name.toLowerCase();
        const set = n.includes('glass') || n.includes('tumbler') ? SETDOWN.glass : SETDOWN.mug;
        this.play(set[Math.floor(Math.random() * set.length)], it.obj.position, 0, false, undefined, Math.min(1, 0.4 + prev * 0.12));
      }
    }
    if (this.cityGain && this.windowPos && this.ctx) {
      const d = this.camera.position.distanceTo(this.windowPos);
      const k = THREE.MathUtils.clamp(1 - (d - 1) / 7, 0, 1); // full within 1 m of the wall, gone beyond ~8 m
      this.cityGain.gain.setTargetAtTime((this.defs.city_distant?.volume ?? 0.2) * k, this.ctx.currentTime, 0.3);
    }
  }

  private async decode(name: string) {
    const d = this.defs[name];
    if (!d || !this.ctx || this.buffers.has(name)) return;
    const probe = document.createElement('audio');
    const pick = (ext: string) => d.files.find((f) => f.endsWith(ext));
    const file = (probe.canPlayType('audio/ogg; codecs="opus"') ? pick('.ogg') : pick('.m4a')) ?? d.files[0];
    try {
      const raw = await (await fetch(this.base + file)).arrayBuffer();
      this.buffers.set(name, await this.ctx.decodeAudioData(raw));
    } catch (e) { console.warn(`[audio] ${name} failed to decode`, e); }
  }

  /** Play a manifest sound; optional world position (panned relative to the camera) and max length in seconds. */
  play(name: string, pos?: THREE.Vector3, maxSeconds = 0, loop = false, tap?: (g: GainNode) => void, gain = 1, rate = 1): AudioBufferSourceNode | null {
    this.count[name] = (this.count[name] ?? 0) + 1;
    const buf = this.buffers.get(name);
    const ctx = this.ctx;
    if (!ctx || !buf) return null;
    const src = ctx.createBufferSource();
    src.buffer = buf;
    src.loop = loop;
    src.playbackRate.value = rate;
    const g = ctx.createGain();
    g.gain.value = (this.defs[name]?.volume ?? 1) * gain;
    tap?.(g);
    src.connect(g);
    if (pos) {
      const p = ctx.createPanner();
      p.panningModel = 'HRTF';
      p.distanceModel = 'inverse';
      p.refDistance = 1.5;
      p.rolloffFactor = 1.3;
      p.maxDistance = 40;
      p.positionX.value = pos.x; p.positionY.value = pos.y; p.positionZ.value = pos.z;
      g.connect(p).connect(this.master!);
      src.onended = () => { p.disconnect(); g.disconnect(); };
      this.syncListener();
    } else { g.connect(this.master!); src.onended = () => g.disconnect(); }
    src.start();
    if (maxSeconds > 0) {
      g.gain.setValueAtTime(g.gain.value, ctx.currentTime + maxSeconds - 0.15);
      g.gain.linearRampToValueAtTime(0, ctx.currentTime + maxSeconds);
      src.stop(ctx.currentTime + maxSeconds);
    }
    return src;
  }

  private fwd = new THREE.Vector3();
  private syncListener() {
    const l = this.ctx!.listener;
    const c = this.camera;
    c.getWorldDirection(this.fwd);
    l.positionX.value = c.position.x; l.positionY.value = c.position.y; l.positionZ.value = c.position.z;
    l.forwardX.value = this.fwd.x; l.forwardY.value = this.fwd.y; l.forwardZ.value = this.fwd.z;
    l.upX.value = 0; l.upY.value = 1; l.upZ.value = 0;
  }

  whenReady() { return this.ready; }
}
