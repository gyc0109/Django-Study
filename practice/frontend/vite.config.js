/**
 * Vite 配置：开发服务器 + /api 代理。
 *
 * 为什么端口用 5174？
 *   上一个项目的 Vite 跑在 5173，两个项目同时开也不会打架。
 *
 * 为什么需要 proxy？
 *   浏览器有同源策略：5174 的页面不能直接请求 8001 的接口。
 *   让浏览器只访问 5174，由 Vite 在服务器端转发到 8001，
 *   浏览器看到的就是同源请求，不存在跨域问题。
 */

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue2'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5174,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8001',
        changeOrigin: true
        // 没有 rewrite：/api/books/ 原样转发到 8001/api/books/
      }
    }
  }
})
