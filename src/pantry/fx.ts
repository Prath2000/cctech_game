import * as THREE from 'three/webgpu';

/** Quintic ease in/out (0..1). */
export const smooth = (p: number) => { const c = p < 0 ? 0 : p > 1 ? 1 : p; return c * c * c * (c * (c * 6 - 15) + 10); };
export const approach = (cur: number, tgt: number, d: number) => (cur < tgt ? Math.min(tgt, cur + d) : Math.max(tgt, cur - d));

let blob: THREE.CanvasTexture | null = null;
function blobTexture() {
  if (blob) return blob;
  const c = document.createElement('canvas');
  c.width = c.height = 64;
  const g = c.getContext('2d')!;
  const gr = g.createRadialGradient(32, 32, 0, 32, 32, 32);
  gr.addColorStop(0, 'rgba(255,255,255,0.9)');
  gr.addColorStop(0.5, 'rgba(255,255,255,0.35)');
  gr.addColorStop(1, 'rgba(255,255,255,0)');
  g.fillStyle = gr;
  g.fillRect(0, 0, 64, 64);
  blob = new THREE.CanvasTexture(c);
  blob.colorSpace = THREE.SRGBColorSpace;
  return blob;
}

/** Fixed pool of soft sprites rising from `origin`; nothing is allocated after construction. */
export class Steam {
  emitting = false;
  readonly origin = new THREE.Vector3();
  private sprites: THREE.Sprite[] = [];
  private mats: THREE.SpriteMaterial[] = [];
  private age: Float32Array;
  private life: Float32Array;
  private px: Float32Array; private py: Float32Array; private pz: Float32Array;
  private dx: Float32Array; private dz: Float32Array;

  constructor(scene: THREE.Scene, private n: number, private size: number, private rise: number, private peak: number, private rate: number) {
    this.age = new Float32Array(n); this.life = new Float32Array(n);
    this.px = new Float32Array(n); this.py = new Float32Array(n); this.pz = new Float32Array(n);
    this.dx = new Float32Array(n); this.dz = new Float32Array(n);
    for (let i = 0; i < n; i++) {
      const m = new THREE.SpriteMaterial({ map: blobTexture(), transparent: true, depthWrite: false, opacity: 0, color: 0xf2f4f6 });
      const s = new THREE.Sprite(m);
      s.scale.setScalar(size);
      s.renderOrder = 5;
      scene.add(s);
      this.sprites.push(s); this.mats.push(m);
      this.age[i] = this.life[i] = 1; // dead
    }
  }

  update(dt: number) {
    for (let i = 0; i < this.n; i++) {
      if (this.age[i] >= this.life[i]) {
        if (!this.emitting || Math.random() > dt * this.rate) continue;
        this.age[i] = 0;
        this.life[i] = 1.1 + Math.random() * 0.9;
        this.px[i] = this.origin.x + (Math.random() - 0.5) * 0.02;
        this.py[i] = this.origin.y;
        this.pz[i] = this.origin.z + (Math.random() - 0.5) * 0.02;
        this.dx[i] = (Math.random() - 0.5) * 0.06;
        this.dz[i] = (Math.random() - 0.5) * 0.06;
      }
      const a = (this.age[i] += dt);
      const u = a / this.life[i];
      if (u >= 1) { this.mats[i].opacity = 0; continue; }
      this.sprites[i].position.set(this.px[i] + this.dx[i] * a, this.py[i] + this.rise * u, this.pz[i] + this.dz[i] * a);
      this.sprites[i].scale.setScalar(this.size * (0.5 + 1.5 * u));
      this.mats[i].opacity = this.peak * Math.sin(Math.PI * u);
    }
  }
}

/** Thin open cylinder (liquid stream) with a wobbling radius; scaled to ~0 when not flowing. */
export class Stream {
  readonly mesh: THREE.Mesh;
  constructor(scene: THREE.Scene, color: number, opacity: number) {
    this.mesh = new THREE.Mesh(
      new THREE.CylinderGeometry(1, 1, 1, 10, 1, true),
      new THREE.MeshBasicMaterial({ color, transparent: true, opacity, depthWrite: false, side: THREE.DoubleSide }),
    );
    this.mesh.scale.setScalar(1e-5);
    scene.add(this.mesh);
  }
  set(x: number, yTop: number, z: number, yBot: number, radius: number, flow: number, t: number) {
    const r = Math.max(1e-5, radius * flow * (1 + 0.18 * Math.sin(t * 55)));
    this.mesh.position.set(x, (yTop + yBot) / 2, z);
    this.mesh.scale.set(r, Math.max(1e-5, (yTop - yBot) * (flow > 0.001 ? 1 : 0)), r);
  }
}

/** Additive emissive plane facing -x (lit window / fridge interior); opacity eased toward a target. */
export class Glow {
  level = 0;
  target = 0;
  private mat: THREE.MeshBasicMaterial;
  constructor(scene: THREE.Scene, pos: THREE.Vector3, w: number, h: number, color: number, private max: number) {
    this.mat = new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0, depthWrite: false, blending: THREE.AdditiveBlending, toneMapped: false });
    const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h), this.mat);
    m.position.copy(pos);
    m.rotation.y = -Math.PI / 2; // normal -x
    m.renderOrder = 4;
    scene.add(m);
  }
  update(dt: number, rate = 5) {
    this.level = approach(this.level, this.target, dt * rate);
    this.mat.opacity = this.level * this.max;
  }
}

/** Small point light whose intensity eases; created once up front so the light count (shader) never changes. */
export class EasedLight {
  level = 0;
  target = 0;
  readonly light: THREE.PointLight;
  constructor(scene: THREE.Scene, pos: THREE.Vector3, color: number, private max: number, dist: number) {
    this.light = new THREE.PointLight(color, 0, dist, 2);
    this.light.position.copy(pos);
    scene.add(this.light);
  }
  update(dt: number, rate = 6) {
    this.level = approach(this.level, this.target, dt * rate);
    this.light.intensity = this.level * this.max;
  }
}
