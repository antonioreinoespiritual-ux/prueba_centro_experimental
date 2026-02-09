import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { resolve } from 'node:path';

export default defineConfig({
  base: '/static/cloud/',
  plugins: [react()],
  build: {
    outDir: resolve(__dirname, '../../static/cloud'),
    assetsDir: 'assets',
    emptyOutDir: true,
  },
});
