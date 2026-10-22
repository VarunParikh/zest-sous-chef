import { defineConfig } from "vite";

// Zest 2.0 runs its backend on 127.0.0.1:8100 and this dev server on 5273, next to Zest 1.0 on 8000 and 5173 (ADR-012).
// `ZEST_API` and `WEB_PORT` point elsewhere (the E2E test uses random ports).
const api = process.env.ZEST_API ?? "http://127.0.0.1:8100";
const port = Number(process.env.WEB_PORT ?? 5273);

export default defineConfig({
  oxc: { jsx: { runtime: "automatic", importSource: "react" } },
  server: { host: "localhost", port, proxy: { "/api": { target: api, changeOrigin: true } } },
  preview: { host: "localhost", proxy: { "/api": { target: api, changeOrigin: true } } },
});
