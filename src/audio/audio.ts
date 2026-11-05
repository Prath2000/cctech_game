import * as THREE from 'three/webgpu';

interface Def { files: string[]; loop: boolean; volume: number }

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

  constructor(private camera: THREE.Camera, preload: string[] = []) {
    try { this.ctx = new AudioContext(); } catch { this.ctx = null; }
    const resume = () => { void this.ctx?.resume(); };
    addEventListener('pointerdown', resume);
    addEventListener('keydown', resume);
    this.ready = this.load(preload);
  }

  private async load(names: string[]) {
    if (!this.ctx) return;
    try {
      this.defs = (await (await fetch(`${this.base}manifest.json`)).json()).sounds;
    } catch { return; }
    await Promise.all(names.map((n) => this.decode(n)));
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
  play(name: string, pos?: THREE.Vector3, maxSeconds = 0, loop = false): AudioBufferSourceNode | null {
    this.count[name] = (this.count[name] ?? 0) + 1;
    const buf = this.buffers.get(name);
    const ctx = this.ctx;
    if (!ctx || !buf) return null;
    const src = ctx.createBufferSource();
    src.buffer = buf;
    src.loop = loop;
    const g = ctx.createGain();
    g.gain.value = this.defs[name]?.volume ?? 1;
    src.connect(g);
    if (pos) {
      const p = ctx.createPanner();
      p.panningModel = 'equalpower';
      p.distanceModel = 'inverse';
      p.refDistance = 1.5;
      p.positionX.value = pos.x; p.positionY.value = pos.y; p.positionZ.value = pos.z;
      g.connect(p).connect(ctx.destination);
      this.syncListener();
    } else g.connect(ctx.destination);
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
