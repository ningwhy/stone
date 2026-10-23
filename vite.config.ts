import { defineConfig } from 'vite';

export default defineConfig({
  base: './',
  server: { port: 5173, strictPort: true },
  build: {
    rollupOptions: {
      output: { manualChunks(id) { if (id.includes('/phaser/')) return 'phaser'; if (/\/react(?:-dom|-reconciler)?\//.test(id)) return 'react'; } },
    },
  },
});
