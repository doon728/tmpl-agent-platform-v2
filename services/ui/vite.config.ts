import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 3000,
    proxy: {
      // UI calls /api/... and Vite forwards to agent-runtime container
      "/api": {
        target: process.env.VITE_AGENT_RUNTIME_URL || "http://agent-runtime:8080",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, "")
      }
    }
  }
});
