import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    watch: {
      // Docker Desktop on macOS doesn't reliably forward native filesystem
      // events through a bind mount, so Vite's watcher never fires without
      // polling. Only enabled inside the container (see docker-compose.yml) —
      // local, non-Docker dev is untouched.
      usePolling: process.env.CHOKIDAR_USEPOLLING === 'true',
    },
  },
})
