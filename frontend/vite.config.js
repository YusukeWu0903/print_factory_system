import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    // 允許所有 ngrok 的網域，或是直接允許所有主機 (true)
    allowedHosts: ['.ngrok-free.dev', 'all'],
    host: '0.0.0.0', // 允許外部 IP 連線
    // API 代理設定：將 /api 請求轉發至後端
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '/api'),
      },
    },
  },
})