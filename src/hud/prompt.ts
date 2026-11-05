export type Level = 'look' | 'use' | 'grab';
const META: Record<Level, { icon: string; label: string; color: string }> = {
  look: { icon: '\u{1F441}', label: 'Look', color: '#8fd3ff' },
  use: { icon: '✋', label: 'Use [E]', color: '#ffd166' },
  grab: { icon: '\u{1F90F}', label: 'Grab [click]', color: '#7dffa0' },
};
export const LEVEL_COLOR: Record<Level, number> = { look: 0x8fd3ff, use: 0xffd166, grab: 0x7dffa0 };

/** Crosshair dot + interaction prompt (level, name, caption). */
export class PromptHud {
  private cross = document.createElement('div');
  private box = document.createElement('div');
  private last = '';

  constructor() {
    Object.assign(this.cross.style, {
      position: 'fixed', left: '50%', top: '50%', width: '6px', height: '6px', margin: '-3px 0 0 -3px',
      borderRadius: '50%', background: 'rgba(255,255,255,.8)', boxShadow: '0 0 2px #000', pointerEvents: 'none', zIndex: '10',
    });
    Object.assign(this.box.style, {
      position: 'fixed', left: '50%', top: '56%', transform: 'translateX(-50%)', padding: '6px 12px',
      font: '14px system-ui, sans-serif', color: '#fff', background: 'rgba(0,0,0,.55)', borderRadius: '6px',
      textAlign: 'center', pointerEvents: 'none', zIndex: '10', display: 'none', maxWidth: '60vw',
    });
    this.box.id = 'hud-prompt';
    document.body.append(this.cross, this.box);
  }

  show(level: Level | null, name = '', caption = '', extra = '') {
    const key = `${level}|${name}|${caption}|${extra}`;
    if (key === this.last) return;
    this.last = key;
    if (!level) { this.box.style.display = 'none'; return; }
    const m = META[level];
    this.box.style.display = 'block';
    this.box.replaceChildren();
    const head = document.createElement('div');
    head.style.cssText = `color:${m.color};font-size:12px;letter-spacing:.05em`;
    head.textContent = `${m.icon} ${extra || m.label}`;
    const n = document.createElement('div');
    n.style.fontWeight = '600';
    n.textContent = name;
    this.box.append(head, n);
    if (caption) {
      const c = document.createElement('div');
      c.style.cssText = 'opacity:.8;font-size:13px';
      c.textContent = caption;
      this.box.append(c);
    }
  }
}
