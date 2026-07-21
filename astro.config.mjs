import { defineConfig } from 'astro/config';

export default defineConfig({
  site: 'https://alexpark.example.com',
  experimental: {
    contentLayer: true,
  },
  markdown: {
    shikiConfig: {
      theme: 'github-dark-dimmed',
      wrap: true,
    },
  },
});
