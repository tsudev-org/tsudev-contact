import { defineConfig } from 'astro/config';

// Trang tĩnh, không JavaScript phía trình duyệt; CSS tách tệp để CSP style-src 'self' cho qua.
export default defineConfig({
  site: 'https://contact.tsudev.com',
  trailingSlash: 'always',
  compressHTML: true,
  build: { format: 'directory', inlineStylesheets: 'never' },
  vite: {
    server: { fs: { allow: ['..'] } },
    build: { assetsInlineLimit: 0 },
  },
});
