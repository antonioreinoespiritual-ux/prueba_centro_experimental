import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { resolve } from 'node:path';

export default defineConfig({
  base: '/static/hypotheses/',
  plugins: [react()],
  build: {
    outDir: resolve(__dirname, '../../static/hypotheses'),
    assetsDir: 'assets',
    emptyOutDir: true,
  },
});
