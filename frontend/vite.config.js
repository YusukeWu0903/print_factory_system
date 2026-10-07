import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath } from 'node:url'

const apiProxyTarget = process.env.API_PROXY_TARGET || 'http://127.0.0.1:8000'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    // 允許所有 ngrok 的網域，或是直接允許所有主機 (true)
    allowedHosts: ['.ngrok-free.dev', '.ngrok-free.app'],
    host: '0.0.0.0', // 允許外部 IP 連線
    // API 代理設定：將 /api 請求轉發至後端
    proxy: {
      '/api': {
        target: apiProxyTarget,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '/api'),
      },
    },
  },
})
