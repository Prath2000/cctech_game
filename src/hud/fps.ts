/** Minimal fps / frame-time overlay using the median of recent frames. */
export class FpsHud {
  private el = document.createElement('div');
  private samples: number[] = [];
  private last = performance.now();
  private lastUpdate = 0;

  constructor(private backend: string) {
    Object.assign(this.el.style, {
      position: 'fixed', top: '8px', left: '8px', padding: '4px 8px',
      font: '12px ui-monospace, monospace', color: '#0f0', background: 'rgba(0,0,0,.6)',
      pointerEvents: 'none', whiteSpace: 'pre', zIndex: '10',
    });
    this.el.id = 'hud-fps';
    document.body.appendChild(this.el);
  }

  tick(): void {
    const now = performance.now();
    this.samples.push(now - this.last);
    this.last = now;
    if (this.samples.length > 60) this.samples.shift();
    if (now - this.lastUpdate < 250) return;
    this.lastUpdate = now;
    const sorted = [...this.samples].sort((a, b) => a - b);
    const ms = sorted[Math.floor(sorted.length / 2)];
    this.el.textContent = `${(1000 / ms).toFixed(0)} fps  ${ms.toFixed(1)} ms\n${this.backend}`;
  }
}
