import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Vite = the dev server + bundler. `npm run dev` serves the app at http://localhost:5173
export default defineConfig({
  plugins: [react()],
  server: { port: 5173 },
});
