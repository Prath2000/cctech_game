import captions from '../data/captions.json';

export interface Caption { name: string; caption: string }
const table = captions as unknown as Record<string, Caption>;

/** "Coffee_Machine.001" -> "Coffee Machine" */
export function prettify(raw: string): string {
  const s = raw.replace(/\.\d+$/, '').replace(/[_-]+/g, ' ').trim();
  return s.replace(/\b\w/g, (c) => c.toUpperCase());
}

/** Looks up by caption_id, then object name (also without `.001`/`_001` suffix); falls back to a prettified name. */
export function captionFor(id: string | undefined, objectName: string): Caption {
  const base = objectName.replace(/[._]\d+$/, '');
  for (const k of [id, objectName, base]) {
    const c = k && table[k];
    if (c && typeof c === 'object') return { name: c.name || prettify(objectName), caption: c.caption ?? '' };
  }
  return { name: prettify(objectName), caption: '' };
}
