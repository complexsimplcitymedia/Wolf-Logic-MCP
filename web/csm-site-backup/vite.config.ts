import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { resolve } from 'path';

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 3000,
    allowedHosts: [
      'complexsimplicityai.com',
      'caddy-manager.complexsimplicityai.com',
      '.complexsimplicityai.com'
    ]
  },
  build: {
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'index.html'),
        portfolio: resolve(__dirname, 'src/pages/portfolio.html'),
        services: resolve(__dirname, 'src/pages/services.html'),
        contact: resolve(__dirname, 'src/pages/contact.html'),
        privacy: resolve(__dirname, 'src/pages/privacy.html'),
        terms: resolve(__dirname, 'src/pages/terms.html'),
        ai: resolve(__dirname, 'src/pages/ai.html'),
        biography: resolve(__dirname, 'src/pages/biography.html'),
      },
    },
  },
  optimizeDeps: {
    include: ['react', 'react-dom']
  }
});