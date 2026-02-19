import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { resolve } from 'node:path';

export default defineConfig({
  base: '/static/interviews/',
  plugins: [react()],
  build: {
    outDir: resolve(__dirname, '../../static/interviews'),
    assetsDir: 'assets',
    emptyOutDir: true,
  },
});
