// TASK-1.13: the wall light switch. E toggles the lights-only bake blend (uLights) with a ~0.5 s eased fade.
import { registerUse } from '../interact/registry';
import { playSound } from '../audio/audio';
import type { BakedLighting } from './baked';
import type { Lighting } from './index';

export const FADE_S = 0.5;

export class LightSwitch {
  target: 0 | 1;
  private fading = false;
  private t: number;

  constructor(private baked: BakedLighting, private lighting: Lighting) {
    this.t = baked.uLights.value;
    this.target = this.t >= 0.5 ? 1 : 0;
    registerUse('light_switch', () => this.toggle());
  }

  get isOn() { return this.target === 1; }

  toggle(on = !this.isOn) {
    if (!this.baked.hasOn) return;
    this.target = on ? 1 : 0;
    this.fading = true;
    playSound(on ? 'switch_on' : 'switch_off');
  }

  /** Per frame: ease uLights toward the target (linear in time, smoothstepped for display). */
  update(dt: number) {
    if (!this.fading) return;
    const step = dt / FADE_S;
    this.t = this.target > this.t ? Math.min(this.target, this.t + step) : Math.max(this.target, this.t - step);
    this.baked.uLights.value = this.t * this.t * (3 - 2 * this.t);
    if (this.t === this.target) { this.fading = false; void this.lighting.recaptureReflections(); }
  }
}
