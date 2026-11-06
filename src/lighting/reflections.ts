import * as THREE from 'three/webgpu';
import { pmremTexture, reflectVector, vec3, float } from 'three/tsl';
import { getParallaxCorrectNormal } from 'three/tsl';

export type Quality = 'low' | 'high';

interface ProbeDef {
  name: string;
  /** capture position == box centre (parallax box is centred on the probe). */
  pos: [number, number, number];
  /** box size in metres */
  size: [number, number, number];
}

// Room 8.7 x 2.65 hall (z 0-7.35) + kitchenette bay x 6.7-8.7, z 7.35-10 (blender/layout.py, from the scan).
const PROBES: ProbeDef[] = [
  { name: 'pantry', pos: [7.7, 1.3, 8.7], size: [2.0, 2.65, 2.7] },
  { name: 'window', pos: [4.35, 1.3, 1.4], size: [8.7, 2.65, 2.8] },
  { name: 'hall', pos: [4.35, 1.3, 3.675], size: [8.7, 2.65, 7.35] },
];

/** Glossy material name -> env intensity (diffuse irradiance is also scaled, so keep subtle on diffuse-ish ones). */
const GLOSSY: [RegExp, number][] = [
  [/^granite/, 0.6],
  [/steel|chrome/, 1],
  [/gloss|laminate|pet$/, 0.55],
  [/glass/, 1],
  [/^aluminium/, 0.6],
  [/^floor_tile/, 0.25],
];

/**
 * Box-projected reflection probes. Cubemaps are captured once (CubeCamera) via `capture()`, after the baked
 * lighting is applied; materials are switched to per-probe node-material variants with a PMREM envNode
 * (roughness-aware blur) and TSL parallax correction.
 */
export class ReflectionProbes {
  private applied = false;

  constructor(private scene: THREE.Scene, private renderer: THREE.WebGPURenderer, private quality: Quality) {}

  private pmRTs: any[] = [];
  private busy = false;

  private captureOne(i: number, pm: THREE.PMREMGenerator): THREE.Texture {
    const size = this.quality === 'high' ? 256 : 64;
    const rt = new THREE.CubeRenderTarget(size, { type: THREE.HalfFloatType, generateMipmaps: false });
    const cam = new THREE.CubeCamera(0.05, 40, rt);
    cam.position.set(...PROBES[i].pos);
    this.scene.add(cam);
    cam.update(this.renderer, this.scene);
    this.scene.remove(cam);
    // reuse the PMREM target on re-capture: same texture object, so no material/bind-group rebuild (no hitch)
    const out = pm.fromCubemap(rt.texture, this.pmRTs[i] ?? null);
    this.pmRTs[i] = out;
    rt.dispose();
    return out.texture;
  }

  capture(): void {
    const pm = new THREE.PMREMGenerator(this.renderer);
    const textures = PROBES.map((_, i) => this.captureOne(i, pm));
    pm.dispose();
    this.apply(textures);
    // Warm-up: the first capture saw only the plain materials. Re-render once now that the glossy env-node
    // variants exist, so their render-target pipelines compile during loading, not at the first light toggle.
    const pm2 = new THREE.PMREMGenerator(this.renderer);
    PROBES.forEach((_, i) => this.captureOne(i, pm2));
    pm2.dispose();
  }

  /** Re-capture the cubemaps in place, one probe per frame (e.g. after the lights finished fading). */
  async recapture(): Promise<void> {
    if (!this.applied || this.busy) return;
    this.busy = true;
    try {
      for (let i = 0; i < PROBES.length; i++) {
        await new Promise((r) => requestAnimationFrame(r));
        const pm = new THREE.PMREMGenerator(this.renderer);
        this.captureOne(i, pm);
        pm.dispose();
      }
    } finally { this.busy = false; }
  }

  private apply(textures: THREE.Texture[]): void {
    if (this.applied) return;
    this.applied = true;
    const lib = (this.renderer as any).library;
    const cache = new Map<string, THREE.Material>();
    const box = new THREE.Box3();
    const c = new THREE.Vector3();
    const s = new THREE.Vector3();
    this.scene.traverse((o) => {
      const mesh = o as THREE.Mesh;
      if (!mesh.isMesh || mesh.userData.reflect === false) return;
      box.setFromObject(mesh).getCenter(c);
      box.getSize(s);
      const probe = this.pickProbe(c, s);
      const mats = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
      const out = mats.map((m) => {
        const hit = GLOSSY.find(([re]) => re.test(m.name));
        if (!hit) return m;
        const key = `${m.uuid}|${probe}`;
        let nm = cache.get(key);
        if (!nm) {
          nm = lib.fromMaterial(m) as THREE.MeshStandardNodeMaterial;
          (nm as { uuid: string }).uuid = THREE.MathUtils.generateUUID();
          const p = PROBES[probe];
          const dir = getParallaxCorrectNormal(reflectVector, vec3(...p.size), vec3(...p.pos));
          (nm as THREE.MeshStandardNodeMaterial).envNode = pmremTexture(textures[probe], dir).mul(float(hit[1]));
          cache.set(key, nm);
        }
        return nm;
      });
      mesh.material = Array.isArray(mesh.material) ? out : out[0];
    });
    console.log(`[reflections] ${cache.size} glossy material variants, ${textures.length} probes`);
  }

  /** Large meshes (floor, window wall) use the room-wide probe; small ones the nearest zone probe. */
  private pickProbe(c: THREE.Vector3, s: THREE.Vector3): number {
    if (Math.max(s.x, s.z) > 4) return 2;
    if (c.z < 2.75 && c.y > 0.5) return 1;
    // kitchenette bay (sink, counter, fridge): its own probe; the hall probe's box does not contain it, so its parallax reflections were wrong
    return c.x > 6.7 && c.z > 6.8 ? 0 : 2;
  }
}
