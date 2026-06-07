import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

const backend = process.env.VITE_BACKEND_URL || 'http://127.0.0.1:8000'
const appVersion = process.env.npm_package_version

export default defineConfig({
  plugins: [vue()],
  define: {
    'process.env': {},
    __APP_VERSION__: JSON.stringify(appVersion),
  },
  server: {
    proxy: {
      '/api': { target: backend, changeOrigin: true, ws: true },
      '/list': { target: backend, changeOrigin: true },
      '/delete': { target: backend, changeOrigin: true },
      '/cover': { target: backend, changeOrigin: true },
      '/downloads': { target: backend, changeOrigin: true },
    },
  },
})