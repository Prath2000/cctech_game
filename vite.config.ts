import { defineConfig } from 'vite';
import { resolve } from 'node:path';

// Multi-page: index.html (game) + spike.html (TASK-1.4 lighting spike).
// `three` is aliased to the WebGPU build so examples/jsm loaders (GLTFLoader, EXRLoader) share one class set.
// pathtrace.html needs the WebGL build of three (WebGLRenderer), which three/webgpu lacks.
const webglThree = {
  name: 'pathtrace-webgl-three',
  enforce: 'pre' as const,
  resolveId(source: string, importer?: string) {
    if (source === 'three' && importer && /three-gpu-pathtracer|three-mesh-bvh|src\/pathtrace\//.test(importer)) {
      return resolve(__dirname, 'node_modules/three/build/three.module.js');
    }
    return null;
  },
};

export default defineConfig({
  plugins: [webglThree],
  resolve: { alias: [{ find: /^three$/, replacement: 'three/webgpu' }] },
  build: {
    rollupOptions: { input: { main: resolve(__dirname, 'index.html'), spike: resolve(__dirname, 'spike.html'), pathtrace: resolve(__dirname, 'pathtrace.html') } },
  },
});
