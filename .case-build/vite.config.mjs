import { resolve } from 'node:path';
import { defineConfig } from 'vite';

const here = import.meta.dirname;
export default defineConfig({
  root: here,
  base: './',
  logLevel: 'warn',
  build: {
    outDir: resolve(here, 'dist'),
    emptyOutDir: true,
    rollupOptions: {
      input: resolve(here, 'src/case-embed.js'),
      output: { entryFileNames: 'case-embed.js', chunkFileNames: '[name]-[hash].js' },
    },
  },
});
