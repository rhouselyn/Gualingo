import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: parseInt(process.env.VITE_PORT || '5173', 10),
    proxy: {
      '/api': {
        target: process.env.VITE_API_TARGET || 'http://localhost:8000',
        changeOrigin: true,
        timeout: 600000,
      }
    }
  },
  build: {
    rollupOptions: {
      output: {
        // 将第三方依赖拆分为独立 chunk：文件名带 hash、内容稳定，
        // 配合后端一年 immutable 缓存，可显著加快重访速度并减少主入口体积。
        manualChunks: {
          'react-vendor': ['react', 'react-dom', 'react-is', 'scheduler'],
          'framer-motion': ['framer-motion'],
          'lucide-react': ['lucide-react'],
          'axios': ['axios'],
        },
      },
    },
  },
})
