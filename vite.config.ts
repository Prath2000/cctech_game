import { defineConfig } from 'vite';
import { resolve } from 'node:path';

// Multi-page: index.html (game) + spike.html (TASK-1.4 lighting spike).
// `three` is aliased to the WebGPU build so examples/jsm loaders (GLTFLoader, EXRLoader) share one class set.
export default defineConfig({
  resolve: { alias: [{ find: /^three$/, replacement: 'three/webgpu' }] },
  build: {
    rollupOptions: { input: { main: resolve(__dirname, 'index.html'), spike: resolve(__dirname, 'spike.html') } },
  },
});
