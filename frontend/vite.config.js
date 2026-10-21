import react from '@vitejs/plugin-react'
import { defineConfig, loadEnv } from 'vite'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  // Charge les variables du fichier .env du frontend (jamais versionné).
  const env = loadEnv(mode, process.cwd(), '')

  // URL du backend Django called from the development server.
  const apiTarget = env.VITE_DEV_API_TARGET || 'http://127.0.0.1:8000'

  return {
    plugins: [react()],

    server: {
      port: 5173,
      // Proxy: the frontend calls "/api/..." and Vite forwards the calls
      // to Django. This avoids CORS problems during development.
      proxy: {
        '/api': {
          target: apiTarget,
          changeOrigin: true,
        },
        '/media': {
          target: apiTarget,
          changeOrigin: true,
        },
      },
    },

    build: {
      outDir: 'dist',
      sourcemap: mode !== 'production',
    },
  }
})
