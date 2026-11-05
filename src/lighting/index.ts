import * as THREE from 'three/webgpu';
import type RAPIER from '@dimforge/rapier3d-compat';
import { ReflectionProbes, type Quality } from './reflections';
import { ContactShadows } from './contact';

export interface LightingOpts {
  quality?: Quality;
  world?: RAPIER.World;
}

export interface Lighting {
  /** Call after baked lighting is applied: captures reflection cubemaps and switches glossy materials to them. */
  captureReflections(): void;
  /** Re-capture reflection cubemaps in place, one probe per frame (after a light-state change). */
  recaptureReflections(): Promise<void>;
}

export function initLighting(scene: THREE.Scene, renderer: THREE.WebGPURenderer, opts: LightingOpts = {}): Lighting {
  const quality = opts.quality ?? ((new URLSearchParams(location.search).get('quality') as Quality) || 'high');
  const probes = new ReflectionProbes(scene, renderer, quality);
  if (opts.world) new ContactShadows(scene, opts.world);
  return { captureReflections: () => probes.capture(), recaptureReflections: () => probes.recapture() };
}
