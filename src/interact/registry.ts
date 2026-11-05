import type * as THREE from 'three/webgpu';

export type UseHandler = (obj: THREE.Object3D, useKind: string) => void;
const handlers = new Map<string, UseHandler>();

/** Later tasks (pantry/seating/light switch) register handlers by `use_kind`. */
export function registerUse(kind: string, h: UseHandler) {
  handlers.set(kind, h);
}

export function triggerUse(obj: THREE.Object3D) {
  const kind = String(obj.userData.use_kind ?? '');
  const h = handlers.get(kind);
  if (h) h(obj, kind);
  else console.log(`[use] ${obj.name} (use_kind=${kind || 'none'}) - no handler yet`);
}
