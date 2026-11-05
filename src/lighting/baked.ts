// TASK-1.10 baked lighting: ambient-cube lightmaps on static meshes, interpolated cube probes on dynamic ones.
// One TSL code path (`ambientCube`) for both; identical on WebGPU and WebGL2. No scene lights are needed.
import * as THREE from 'three/webgpu';
import { float, materialColor, materialEmissive, materialMetalness, mix, normalWorld, step, texture, uniform, uv, vec3 } from 'three/tsl';
import { EXRLoader } from 'three/addons/loaders/EXRLoader.js';

const AX = ['px', 'nx', 'py', 'ny', 'pz', 'nz'] as const; // GAME axes: +x east, +y up, +z south
type Cube = Record<(typeof AX)[number], any>;

/** Valve ambient cube: E(n) = n.x^2 E(+-X) + n.y^2 E(+-Y) + n.z^2 E(+-Z). */
export function ambientCube(n: any, c: Cube) {
  const n2 = n.mul(n);
  const cx = mix(c.nx, c.px, step(0, n.x));
  const cy = mix(c.ny, c.py, step(0, n.y));
  const cz = mix(c.nz, c.pz, step(0, n.z));
  return cx.mul(n2.x).add(cy.mul(n2.y)).add(cz.mul(n2.z));
}

interface ProbeGrid { x: number[]; y: number[]; z: number[]; valid: number[]; cube: number[][][] }
interface Dyn { mesh: THREE.Mesh; u: Record<string, any>; last: THREE.Vector3; local: THREE.Vector3 }

export interface BakedLighting {
  /** Per-frame: refresh probe samples of dynamic meshes that moved. */
  update(): void;
  /** Re-sample probes for a mesh (e.g. after teleporting it). */
  sampleAt(p: THREE.Vector3, out: number[]): void;
  meta: any;
}

export interface BakedOpts { state?: 'off' | 'on'; exposure?: number; skyIntensity?: number }

export async function loadBakedLighting(scene: THREE.Scene, renderer: THREE.WebGPURenderer, opts: BakedOpts = {}): Promise<BakedLighting> {
  const q = new URLSearchParams(location.search);
  const state = opts.state ?? 'off';
  const base = `${import.meta.env.BASE_URL}lightmaps/`;
  const dir = `${base}${state}/`;
  const meta = await (await fetch(`${dir}lighting.json`)).json();
  renderer.toneMappingExposure = Number(q.get('exposure') ?? opts.exposure ?? 1);

  // ---- atlases: 6 sRGB8 maps each, value = irradiance-radiance / range ----
  const loader = new THREE.TextureLoader();
  const atlasCube: Record<string, Cube> = {};
  await Promise.all(Object.entries(meta.atlases as Record<string, { range: number }>).map(async ([name, a]) => {
    const c: any = {};
    await Promise.all(AX.map(async (ax) => {
      const t = await loader.loadAsync(`${dir}${name}_${ax}.png`);
      t.colorSpace = THREE.SRGBColorSpace; t.flipY = false; t.generateMipmaps = false;
      t.minFilter = THREE.LinearFilter; t.magFilter = THREE.LinearFilter;
      c[ax] = texture(t, uv(1)).rgb.mul(a.range);
    }));
    atlasCube[name] = c;
  }));

  // ---- probes ----
  const g: ProbeGrid = meta.probes;
  const cubeData = new Float32Array(g.cube.length * 18);
  g.cube.forEach((p, i) => p.forEach((f, k) => f.forEach((v, c) => (cubeData[i * 18 + k * 3 + c] = v))));
  const nY = g.y.length, nZ = g.z.length;
  const axis = (arr: number[], v: number): [number, number] => {
    const c = Math.min(Math.max(v, arr[0]), arr[arr.length - 1]);
    let i = 0; while (i < arr.length - 2 && c > arr[i + 1]) i++;
    return [i, (c - arr[i]) / (arr[i + 1] - arr[i])];
  };
  const sampleAt = (p: THREE.Vector3, out: number[]) => {
    const [ix, fx] = axis(g.x, p.x), [iy, fy] = axis(g.y, p.y), [iz, fz] = axis(g.z, p.z);
    out.fill(0);
    let wsum = 0;
    for (let pass = 0; pass < 2; pass++) { // pass 1 ignores probe validity if every corner was invalid
      for (let dx = 0; dx < 2; dx++) for (let dy = 0; dy < 2; dy++) for (let dz = 0; dz < 2; dz++) {
        const i = ((ix + dx) * nY + (iy + dy)) * nZ + (iz + dz);
        const w = (dx ? fx : 1 - fx) * (dy ? fy : 1 - fy) * (dz ? fz : 1 - fz) * (pass === 0 ? g.valid[i] : 1);
        if (w <= 0) continue;
        wsum += w;
        for (let k = 0; k < 18; k++) out[k] += w * cubeData[i * 18 + k];
      }
      if (wsum > 1e-6) break;
    }
    for (let k = 0; k < 18; k++) out[k] /= wsum;
  };

  const dyn: Dyn[] = [];
  const tmp = new Array(18).fill(0);
  const tv = new THREE.Vector3();
  const place = (d: Dyn) => {
    tv.copy(d.local).applyMatrix4(d.mesh.matrixWorld);
    if (tv.distanceToSquared(d.last) < 1e-4) return;
    d.last.copy(tv);
    sampleAt(tv, tmp);
    AX.forEach((ax, k) => d.u[ax].value.set(tmp[k * 3], tmp[k * 3 + 1], tmp[k * 3 + 2]));
  };

  // ---- materials ----
  const diffuseOf = (E: any) => materialColor.rgb.mul(float(1).sub(materialMetalness)).mul(E);
  const lit = (m: THREE.Material, E: any) => {
    const std = m as THREE.MeshStandardMaterial;
    if (!std.isMeshStandardMaterial) return m;
    const nm = THREE.MeshStandardNodeMaterial.fromMaterial(std) as THREE.MeshStandardNodeMaterial;
    nm.name = m.name; nm.emissiveNode = diffuseOf(E).add(materialEmissive);
    return nm;
  };
  scene.updateMatrixWorld(true);
  let nStatic = 0, nDyn = 0;
  scene.traverse((o) => {
    const mesh = o as THREE.Mesh;
    if (!mesh.isMesh || mesh.userData.lit === false) return;
    const atlas = mesh.userData.lm_atlas as string | undefined;
    const isStatic = mesh.userData.static === 1 && mesh.userData.bake !== 0 && atlas && atlasCube[atlas] && mesh.geometry.getAttribute('uv1');
    let E: any, d: Dyn | undefined;
    if (isStatic) { E = ambientCube(normalWorld, atlasCube[atlas!]); nStatic++; }
    else {
      const u: Record<string, any> = {};
      for (const ax of AX) u[ax] = uniform(new THREE.Vector3());
      E = ambientCube(normalWorld, Object.fromEntries(AX.map((ax) => [ax, u[ax]])) as Cube);
      mesh.geometry.computeBoundingSphere();
      d = { mesh, u, last: new THREE.Vector3(1e9, 0, 0), local: mesh.geometry.boundingSphere!.center.clone() };
      dyn.push(d); nDyn++;
    }
    mesh.material = Array.isArray(mesh.material) ? mesh.material.map((m) => lit(m, E)) : lit(mesh.material, E);
    if (d) place(d);
  });
  console.log(`[lighting] baked: ${nStatic} static meshes on ${Object.keys(atlasCube).join('+')}, ${nDyn} probe-lit meshes`);

  // ---- window backdrop (sky from Blender, orientation matches the baked sun) ----
  try {
    const sky = await new EXRLoader().loadAsync(`${base}sky.exr`);
    sky.mapping = THREE.EquirectangularReflectionMapping;
    scene.background = sky;
    scene.backgroundIntensity = Number(q.get('sky') ?? opts.skyIntensity ?? 1);
  } catch (e) { console.warn('[lighting] no sky backdrop', e); }

  return { update() { for (const d of dyn) place(d); }, sampleAt, meta };
}
