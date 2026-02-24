import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  base: '/static/home/',
  build: {
    outDir: '../../static/home',
    emptyOutDir: true
  }
})
