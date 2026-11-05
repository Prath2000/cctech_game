import * as THREE from 'three/webgpu';

export type BackendName = 'WebGPU' | 'WebGL2';

export interface RendererInfo {
  renderer: THREE.WebGPURenderer;
  backend: BackendName;
}

/** Creates the renderer. `?webgl=1` forces the WebGL2 backend. */
export async function createRenderer(): Promise<RendererInfo> {
  const forceWebGL = new URLSearchParams(location.search).get('webgl') === '1';
  const renderer = new THREE.WebGPURenderer({ antialias: true, forceWebGL });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.toneMapping = THREE.AgXToneMapping;
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  document.body.appendChild(renderer.domElement);
  await renderer.init();

  const isGPU = (renderer.backend as { isWebGPUBackend?: boolean }).isWebGPUBackend === true;
  const backend: BackendName = isGPU ? 'WebGPU' : 'WebGL2';
  console.log(`[renderer] active backend: ${backend}`);
  return { renderer, backend };
}
