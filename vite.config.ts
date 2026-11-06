import { defineConfig } from 'vite';
import { rmSync } from 'node:fs';
import { resolve } from 'node:path';

// Production build holds the game only. spike.html and pathtrace.html are served by the dev server, which render:pt and the checks use.
// `three` is aliased to the WebGPU build so examples/jsm loaders (GLTFLoader, EXRLoader) share one class set.
// pathtrace.html needs the WebGL build of three (WebGLRenderer), which three/webgpu lacks.
const webglThree = {
  name: 'pathtrace-webgl-three',
  enforce: 'pre' as const,
  resolveId(source: string, importer?: string) {
    if (source === 'three' && importer && /three-gpu-pathtracer|three-mesh-bvh|src\/pathtrace\//.test(importer)) {
      return resolve(__dirname, 'node_modules/three/build/three.module.js');
    }
    if (source === 'three') return resolve(__dirname, 'node_modules/three/build/three.webgpu.js');
    return null;
  },
};

// Everything in public/ is copied to dist, so the spike assets are removed after the copy.
const dropSpikeAssets = {
  name: 'drop-spike-assets',
  apply: 'build' as const,
  closeBundle() {
    rmSync(resolve(__dirname, 'dist/spike'), { recursive: true, force: true });
  },
};

export default defineConfig({
  plugins: [webglThree, dropSpikeAssets],
  build: {
    rollupOptions: { input: { main: resolve(__dirname, 'index.html') } },
  },
});
