import * as THREE from 'three/webgpu';
import type { AudioSystem } from './audio';
import type { FirstPersonController } from '../controller';
import type { GrabSystem } from '../interact/grab';
import { initSettings } from './settings';

/** Wires footsteps, set-down clinks, window-wall city ambience and the settings overlay. Returns a per-frame update. */
export function initAudioExtras(audio: AudioSystem, scene: THREE.Scene, player: FirstPersonController, grab: GrabSystem, canvas: HTMLElement) {
  scene.updateMatrixWorld(true);
  let win: THREE.Object3D | null = null;
  scene.traverse((o) => { if (!win && /window/i.test(o.name)) win = o; });
  const box = new THREE.Box3().setFromObject(scene);
  const c = box.getCenter(new THREE.Vector3());
  // No window mesh found: the window wall is z = 0 (blender/layout.py), centred along x.
  audio.windowPos = win ? (win as THREE.Object3D).getWorldPosition(new THREE.Vector3()) : new THREE.Vector3(c.x, 1.5, box.min.z);
  const settings = initSettings(audio, canvas);
  return {
    settings,
    update: (dt: number, active: boolean) => audio.update(dt, player.feet, active && !settings.open, grab.items),
  };
}
