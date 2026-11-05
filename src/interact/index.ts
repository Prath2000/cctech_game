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
  private meshes: THREE.Object3D[] = [];
  private hits: THREE.Intersection[] = [];
  /** Set by the grab system: while an item is held, the prompt shows it with a drop/toss hint. */
  heldInfo: (() => { obj: THREE.Object3D; hint: string } | null) | null = null;

  constructor(private scene: THREE.Scene, private camera: THREE.PerspectiveCamera, readonly world: RAPIER.World) {
    this.ray.far = REACH;
    this.highlight = new Highlight(scene);
    addEventListener('keydown', (e) => {
      if (e.code === 'KeyE' && this.target && interactLevel(this.target) === 'use') triggerUse(this.target);
    });
  }

  /** Rebuild the cached list of pickable meshes (call after adding/removing scene content). */
  refresh() {
    this.meshes.length = 0;
    this.scene.traverse((o) => { if ((o as THREE.Mesh).isMesh) this.meshes.push(o); });
  }

  /** Raycast from screen centre; returns the nearest interactive ancestor of the first hit. */
  pick(): THREE.Object3D | null {
    this.ray.setFromCamera(this.dir, this.camera);
    this.hits.length = 0;
    this.ray.intersectObjects(this.meshes, false, this.hits);
    for (const h of this.hits) {
      let o: THREE.Object3D | null = h.object;
      let found: THREE.Object3D | null = null;
      let ignored = false;
      let hidden = false;
      for (; o; o = o.parent) {
        if (!o.visible) { hidden = true; break; }
        if (o === this.ignore) { ignored = true; break; }
        if (!found && interactLevel(o)) found = o;
      }
      if (hidden || ignored) continue; // see through the held item
      return found; // first solid hit decides (walls occlude)
    }
    return null;
  }

  update() {
    const held = this.heldInfo?.();
    if (held) {
      this.target = null;
      const c = captionFor(held.obj.userData.caption_id, held.obj.name);
      this.highlight.set(null);
      this.prompt.show('grab', c.name, c.caption, held.hint);
      return;
    }
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
    this.prompt.show(level, c.name, c.caption);
  }
}
