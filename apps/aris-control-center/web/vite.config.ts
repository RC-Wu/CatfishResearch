import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";

export default defineConfig({
  plugins: [react()],
  root: path.resolve(__dirname),
  server: {
    host: "127.0.0.1",
    port: 41851,
    proxy: {
      "/api": "http://127.0.0.1:47951",
      "/ws": {
        target: "ws://127.0.0.1:47951",
        ws: true
      }
    }
  },
  build: {
    outDir: "dist",
    emptyOutDir: true
  }
});
