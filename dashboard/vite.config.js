import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // Le frontend appelle toujours "/api/...", jamais l'URL complete de
      // l'API. Vite redirige ces requetes vers FastAPI (port 8000) et enleve
      // le prefixe "/api" (l'API expose /health, pas /api/health).
      // Avantage : pas de probleme CORS en dev, et en prod on changerait
      // juste cette config sans toucher au code React.
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})
