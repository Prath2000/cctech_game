import type * as THREE from 'three/webgpu';

const WINDOW_MS = 2000; // judge speed over this long
const SLOW_MEDIAN_MS = 20; // slower than 50 fps counts as struggling
const STEP = 0.8; // each drop renders 20% fewer pixels per axis
const MIN_RATIO = 0.75;
const SKIP_MS = 3000; // ignore the hitchy frames right after load

/**
 * Lowers render resolution when the frame rate stays low. It only goes down, so the
 * picture never pumps up and down mid-walk. `?autores=0` turns it off.
 */
export class AutoResolution {
  private samples: number[] = [];
  private windowStart = 0;
  private started = performance.now();

  constructor(private renderer: THREE.WebGPURenderer, private isEnabled: () => boolean) {}

  /** Call once per frame with that frame's duration in ms. */
  tick(frameMs: number, now: number): void {
    if (!this.isEnabled() || document.hidden || now - this.started < SKIP_MS) {
      this.samples.length = 0;
      this.windowStart = now;
      return;
    }
    this.samples.push(frameMs);
    if (now - this.windowStart < WINDOW_MS) return;

    const sorted = this.samples.sort((a, b) => a - b);
    const median = sorted[sorted.length >> 1];
    this.samples = [];
    this.windowStart = now;

    const ratio = this.renderer.getPixelRatio();
    if (median <= SLOW_MEDIAN_MS || ratio <= MIN_RATIO) return;
    const next = Math.max(MIN_RATIO, ratio * STEP);
    this.renderer.setPixelRatio(next);
    console.log(`[autores] median ${median.toFixed(1)} ms, pixel ratio ${ratio.toFixed(2)} -> ${next.toFixed(2)}`);
  }
}
