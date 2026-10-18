import { defineConfig } from "vite";

// The backend runs on 127.0.0.1:8000 (make dev); `ZEST_API` points elsewhere (the E2E test uses a random port).
const api = process.env.ZEST_API ?? "http://127.0.0.1:8000";

export default defineConfig({
  oxc: { jsx: { runtime: "automatic", importSource: "react" } },
  server: { host: "localhost", proxy: { "/api": { target: api, changeOrigin: true } } },
  preview: { host: "localhost", proxy: { "/api": { target: api, changeOrigin: true } } },
});
