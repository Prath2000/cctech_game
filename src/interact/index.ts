import * as THREE from 'three/webgpu';
import RAPIER from '@dimforge/rapier3d-compat';
import { PromptHud, type Level } from '../hud/prompt';
import { captionFor } from './captions';
import { Highlight } from './highlight';
import { triggerUse } from './registry';

export { registerUse } from './registry';
export const REACH = 2.5;

export function interactLevel(o: THREE.Object3D): Level | null {
  const v = o.userData.interact;
  return v === 'look' || v === 'use' || v === 'grab' ? v : null;
}

/** Crosshair raycast -> highlight + prompt; E triggers `use` handlers. */
export class Interaction {
  readonly ray = new THREE.Raycaster();
  readonly prompt = new PromptHud();
  private highlight: Highlight;
  /** Interactive object under the crosshair (null if none / out of reach). */
  target: THREE.Object3D | null = null;
  /** Object to ignore for aiming (the held item). */
  ignore: THREE.Object3D | null = null;
  private dir = new THREE.Vector2(0, 0);
  /** Extra prompt text override for the current target (e.g. held state). */
  promptExtra: ((t: THREE.Object3D) => string | undefined) | null = null;

  constructor(private scene: THREE.Scene, private camera: THREE.PerspectiveCamera, readonly world: RAPIER.World) {
    this.ray.far = REACH;
    this.highlight = new Highlight(scene);
    addEventListener('keydown', (e) => {
      if (e.code === 'KeyE' && this.target && interactLevel(this.target) === 'use') triggerUse(this.target);
    });
  }

  /** Raycast from screen centre; returns the nearest interactive ancestor of the first hit. */
  pick(): THREE.Object3D | null {
    this.ray.setFromCamera(this.dir, this.camera);
    for (const h of this.ray.intersectObjects(this.scene.children, true)) {
      if (!(h.object as THREE.Mesh).isMesh && !(h.object as THREE.Line).isLine) continue;
      let o: THREE.Object3D | null = h.object;
      let found: THREE.Object3D | null = null;
      let ignored = false;
      for (; o; o = o.parent) {
        if (o === this.ignore) { ignored = true; break; }
        if (!found && interactLevel(o)) found = o;
      }
      if (ignored) continue; // see through the held item
      return found; // first solid hit decides (walls occlude)
    }
    return null;
  }

  update() {
    const t = this.pick();
    this.target = t;
    const level = t && interactLevel(t);
    if (!t || !level) {
      this.highlight.set(null);
      this.prompt.show(null);
      return;
    }
    const c = captionFor(t.userData.caption_id, t.name);
    this.highlight.set(t, level);
    this.prompt.show(level, c.name, c.caption, this.promptExtra?.(t));
  }
}
