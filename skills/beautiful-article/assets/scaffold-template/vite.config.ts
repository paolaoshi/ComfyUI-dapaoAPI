import { resolve } from "node:path";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { viteSingleFile } from "vite-plugin-singlefile";

// reacticle is consumed from the published npm package (see package.json).
// Builds a self-contained single-page HTML (CSS + JS inlined, opens offline)
// to dist/index.html. `npm run html` then copies it to article/article.html.
export default defineConfig({
  plugins: [react(), viteSingleFile()],
  build: {
    outDir: "dist",
    emptyOutDir: true,
    rollupOptions: {
      input: resolve(__dirname, "index.html"),
    },
  },
});
