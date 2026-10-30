import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// In dev, /api/* is forwarded to FastAPI (same path layout as nginx in Docker).
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
        rewrite: (p) => p.replace(/^\/api/, ""),
      },
    },
  },
});
