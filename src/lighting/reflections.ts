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

// Room 12 x 7.5 x 3.2 (blender/layout.py): window wall z=0, counter east x 11.4-12.
const PROBES: ProbeDef[] = [
  { name: 'pantry', pos: [10, 1.6, 3.75], size: [4, 3.2, 7.5] },
  { name: 'window', pos: [6, 1.6, 1.4], size: [12, 3.2, 2.8] },
  { name: 'hall', pos: [6, 1.6, 3.75], size: [12, 3.2, 7.5] },
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
    return c.x > 8 ? 0 : 2;
  }
}
