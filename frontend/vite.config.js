import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vuetify, { transformAssetUrls } from 'vite-plugin-vuetify'

export default defineConfig({
  plugins: [
    vue({
      template: { transformAssetUrls }
    }),
    vuetify({ autoImport: true })
  ],
  server: {
    port: 5173,
    host: true, // bind to 0.0.0.0 inside container
    proxy: {
      '/api': 'http://localhost:8000',
      '/reports': 'http://localhost:8000'
    }
  }
})
