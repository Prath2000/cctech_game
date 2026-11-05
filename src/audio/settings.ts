import type { AudioSystem } from './audio';

/** Light pause/settings overlay: Esc toggles it (also appears when pointer lock is released). Master volume + mute. */
export function initSettings(audio: AudioSystem, canvas: HTMLElement) {
  const el = document.createElement('div');
  el.style.cssText = 'position:fixed;inset:0;display:none;align-items:center;justify-content:center;background:rgba(0,0,0,.55);z-index:50;font:14px system-ui,sans-serif;color:#eee';
  el.innerHTML = `<div style="background:#1c2024;padding:20px 28px;border-radius:8px;min-width:240px">
    <div style="font-size:16px;margin-bottom:12px">Paused</div>
    <label>Volume <input id="aud-vol" type="range" min="0" max="1" step="0.05" style="vertical-align:middle"></label><br>
    <label style="display:block;margin:10px 0"><input id="aud-mute" type="checkbox"> Mute (M)</label>
    <button id="aud-close">Resume</button> <span style="opacity:.6;font-size:12px">click the view to look around</span></div>`;
  document.body.appendChild(el);
  const vol = el.querySelector<HTMLInputElement>('#aud-vol')!;
  const mute = el.querySelector<HTMLInputElement>('#aud-mute')!;
  const sync = () => { vol.value = String(audio.volume); mute.checked = audio.muted; };
  audio.listeners.add(sync);
  sync();
  vol.oninput = () => audio.setVolume(Number(vol.value));
  mute.onchange = () => audio.setMuted(mute.checked);
  const show = (v: boolean) => { el.style.display = v ? 'flex' : 'none'; };
  el.querySelector<HTMLButtonElement>('#aud-close')!.onclick = () => show(false);
  addEventListener('keydown', (e) => { if (e.code === 'Escape' && !e.repeat) show(el.style.display === 'none'); });
  document.addEventListener('pointerlockchange', () => show(document.pointerLockElement !== canvas));
  return { show, get open() { return el.style.display !== 'none'; } };
}
