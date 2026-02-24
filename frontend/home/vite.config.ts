import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { resolve } from 'node:path';

export default defineConfig({
  base: '/static/home/',
  plugins: [react()],
  build: {
    outDir: resolve(__dirname, '../../static/home'),
    assetsDir: 'assets',
    emptyOutDir: true,
  },
});
